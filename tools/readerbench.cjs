// GPU frame trace and blocking-task regression for ordinary scrolling and the existing zoom gestures.
// Requires Playwright and installed Edge. Use a test server with a copy of the paper; never a generation job.
// Baseline directory: baseline-reader.js and baseline-reader.css saved before editing.
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
const [url, dir, baseline] = process.argv.slice(2).filter(arg=>arg!=='--zoom-only');
if (!url || !dir) throw new Error('Usage: node tools/readerbench.cjs URL OUTPUT_DIRECTORY [BASELINE_ASSETS_DIRECTORY]');
fs.mkdirSync(dir, {recursive:true});
const mode = baseline ? 'baseline' : 'candidate';
function frames(buf, gestureOnly = false) {
  const events = JSON.parse(buf).traceEvents;
  const start = gestureOnly ? events.find(e=>e.name==='readerbench.begin').ts/1000 : -Infinity;
  const end = gestureOnly ? events.find(e=>e.name==='readerbench.end').ts/1000 : Infinity;
  const seen = new Map();
  for (const e of events) {
    if(e.name !== 'PipelineReporter' || e.ph !== 'b') continue;
    const f=e.args.frame_reporter;
    if(f.frame_type === 'FORKED') continue;
    seen.set(f.frame_source+':'+f.frame_sequence,[e.ts/1000,f.state]);
  }
  const all=[...seen.values()].filter(f=>f[0]>=start && f[0]<=end).sort((a,b)=>a[0]-b[0]);
  const active=all.filter(f=>f[1]!=='STATE_NO_UPDATE_DESIRED');
  const shown=all.filter(f=>f[1].startsWith('STATE_PRESENTED') && f[0]>=active[0]?.[0] && f[0]<=active.at(-1)?.[0]);
  const dropped=active.filter(f=>f[1]==='STATE_DROPPED').length;
  return {presented:shown.length,dropped,dropPercent:+(100*dropped/Math.max(1,dropped+shown.length)).toFixed(1),worstGapsMs:shown.slice(1).map((f,i)=>+(f[0]-shown[i][0]).toFixed(1)).sort((a,b)=>b-a).slice(0,5)};
}
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:false,args:['--enable-gpu-rasterization']});
 const page=await browser.newPage({viewport:{width:1512,height:982},deviceScaleFactor:2});
 if(baseline) for(const ext of ['js','css']) await page.route('**/static/reader.'+ext,r=>r.fulfill({path:path.join(baseline,'baseline-reader.'+ext),contentType:ext==='js'?'text/javascript':'text/css'}));
 await page.addInitScript(()=>{
   window.__drPerf=[];window.__scrollTasks=[];
   new PerformanceObserver(list=>window.__scrollTasks.push(...list.getEntries().map(e=>({start:e.startTime,ms:e.duration})))).observe({type:'longtask',buffered:true});
 });
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(url);await page.locator('#zoombar button').first().waitFor();await page.waitForTimeout(1800);
 const gpu=await (await browser.newBrowserCDPSession()).send('SystemInfo.getInfo');
 const result={mode,gpu:gpu.gpu.featureStatus,scroll:[],zoom:[],errors};
 for(const level of (process.argv.includes('--zoom-only') ? [] : [4,3,2])) {
   await page.evaluate(l=>window.__reader.setLevel(l),level);await page.waitForTimeout(1800);
   await page.evaluate(()=>scrollTo(0,document.documentElement.scrollHeight*.25));await page.waitForTimeout(1800);
   await page.mouse.move(700,460);
   await page.evaluate(()=>{window.__drPerf.length=0;window.__scrollTasks.length=0;});
   await browser.startTracing(page,{categories:['benchmark','cc','devtools.timeline','disabled-by-default-devtools.timeline.frame']});
   const start=await page.evaluate(()=>performance.now());
   for(const direction of [1,-1,1]) {
     for(let i=0;i<10;i++){await page.mouse.wheel(0,direction*220);await page.waitForTimeout(50);}
     await page.waitForTimeout(380);
   }
   await page.waitForTimeout(900);
   const buf=await browser.stopTracing();
   const data=await page.evaluate(()=>({perf:window.__drPerf,tasks:window.__scrollTasks,y:scrollY,height:document.documentElement.scrollHeight,level:window.__reader.level,nodes:document.querySelectorAll('*').length}));
   data.tasks=data.tasks.filter(t=>t.start>=start);
   result.scroll.push({level,...frames(buf),...data});
   fs.writeFileSync(path.join(dir,mode+'-L'+level+'-trace.json'),buf);
 }
 await page.evaluate(()=>window.__reader.setLevel(4));await page.waitForTimeout(1800);
 await page.evaluate(()=>scrollTo(0,document.documentElement.scrollHeight*.3));await page.waitForTimeout(2200);
 // Bound the trace to the gesture and its settling animation. Later preparation can draw a frame
 // after a long idle interval; that interval is not an animation stall.
 const zoom=async(name,action)=>{
   await browser.startTracing(page,{categories:['benchmark','cc','blink.user_timing','disabled-by-default-devtools.timeline.frame']});
   await page.evaluate(()=>performance.mark('readerbench.begin'));
   await action();
   await page.waitForFunction(()=>!document.documentElement.classList.contains('morphing'));
   await page.evaluate(()=>performance.mark('readerbench.end'));
   const b=await browser.stopTracing();
   result.zoom.push({name,...frames(b,true),level:await page.evaluate(()=>window.__reader.level)});
   fs.writeFileSync(path.join(dir,mode+'-'+name+'-trace.json'),b);
   await page.waitForTimeout(1800);
 };
 for(const [name,d] of [['pinchOut',6.5],['pinchIn',-6.5]]) await zoom(name,async()=>{await page.keyboard.down('Control');for(let i=0;i<110;i++){await page.mouse.wheel(0,d);await page.waitForTimeout(16);}await page.keyboard.up('Control');});
 const buttons=await page.locator('#zoombar button').evaluateAll(bs=>bs.map(b=>{const r=b.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2];}));
 await zoom('drag',async()=>{await page.mouse.move(...buttons[0]);await page.mouse.down();for(let i=1;i<=60;i++){await page.mouse.move(buttons[0][0]+(buttons[4][0]-buttons[0][0])*i/60,buttons[0][1]);await page.waitForTimeout(16);}await page.mouse.up();});
 await zoom('clickFull',async()=>{await page.mouse.click(...buttons[0]);});
 // Real wheel detents and reversals over the level bar, immediately after moving the reading passage.
 // Gentle pinch tests with prewarmed caches do not catch the live-layout fallback at cold anchors.
 const rapid=[];
 for(const pause of [0,2500]) {
   await page.evaluate(()=>window.__reader.setLevel(4));
   await page.waitForFunction(()=>!document.documentElement.classList.contains('morphing'));
   await page.waitForTimeout(1500);
   await page.evaluate(()=>scrollTo(0,document.documentElement.scrollHeight*.32));
   if(pause) await page.waitForTimeout(pause);
   const bar=await page.locator('#zoombar').boundingBox();
   await page.mouse.move(bar.x+bar.width/2,bar.y+bar.height/2);
   await page.evaluate(()=>{window.__drPerf.length=0;window.__scrollTasks.length=0;});
   for(const direction of [120,-120,120]) for(let i=0;i<8;i++) {
     await page.mouse.wheel(0,direction);await page.waitForTimeout(30);
   }
   await page.waitForTimeout(200);
   await page.waitForFunction(()=>!document.documentElement.classList.contains('morphing'));
   rapid.push({pause,...await page.evaluate(()=>({level:window.__reader.level,perf:window.__drPerf,tasks:window.__scrollTasks}))});
 }
 result.rapid=rapid;
 await page.screenshot({path:path.join(dir,mode+'.png')});
 fs.writeFileSync(path.join(dir,mode+'.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));await browser.close();
 if(result.scroll.some(s=>s.perf.some(t=>/^cap/.test(t[0]) && t[1]>=50))) {console.log('FAIL: zoom preparation blocks page scrolling for >= 50 ms');process.exitCode=2;}
 if(result.zoom.length && result.zoom.some((z,i)=>z.level!==[1,4,0,4][i])) {console.log('FAIL: zoom gestures did not reach their expected levels');process.exitCode=2;}
 if(errors.length) {console.log('FAIL: reader JavaScript errors');process.exitCode=2;}
 if(rapid.some(r=>r.level!==0 || r.perf.some(x=>(x[0]==='prepare'||x[0]==='zoom.prepareStep')&&x[1]>=50))) {
   console.log('FAIL: rapid level-wheel gesture stalls or ends at the wrong level');process.exitCode=2;
 }
})().catch(e=>{console.error(e);process.exit(1);});
