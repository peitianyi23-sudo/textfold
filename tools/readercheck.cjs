// Browser regression: all five reading levels, exact equation heights, reading-position stability,
// animation, and interrupting background preparation at two reading widths. Requires Playwright and Edge.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('fs');
const path=require('path');
const url=process.argv[2], out=process.argv[3];
if(!url || !out) throw new Error('Usage: node tools/readercheck.cjs URL OUTPUT_DIRECTORY');
fs.mkdirSync(out,{recursive:true});
(async()=>{
const b=await chromium.launch({channel:'msedge',headless:false,args:['--enable-gpu-rasterization']});
const p=await b.newPage({viewport:{width:1512,height:982},deviceScaleFactor:2});
const errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.addInitScript(()=>{window.__drPerf=[];});
await p.goto(url);
await p.waitForTimeout(2000);
const results=[];
for(const width of [1512,1000]){
await p.setViewportSize({width,height:982});await p.waitForTimeout(1000);
for(const level of [4,3,2,1,0,4]){
await p.evaluate(l=>__reader.setLevel(l),level);await p.waitForTimeout(1800);
assert.equal(await p.evaluate(()=>__reader.level),level);
const geometry=await p.evaluate(()=>{
 const es=[...document.querySelectorAll('#doc .eq-body')].filter(el=>el.getBoundingClientRect().height>0);
 const before=es.map(el=>({sized:el.classList.contains('eq-sized'),r:el.getBoundingClientRect()}));
 es.forEach(el=>el.classList.remove('eq-sized'));
 const deltas=es.map((el,i)=>{const r=el.getBoundingClientRect(),old=before[i].r;return Math.max(Math.abs(r.top-old.top),Math.abs(r.height-old.height));});
 es.forEach((el,i)=>{if(before[i].sized)el.classList.add('eq-sized');});
 return {equations:es.length,maxDelta:Math.max(0,...deltas)};
});
assert(geometry.maxDelta<1,JSON.stringify({width,level,...geometry}));
results.push({width,level,...geometry});
}
await p.evaluate(()=>scrollTo(0,document.documentElement.scrollHeight*.3));await p.waitForTimeout(1600);
const pin=await p.evaluate(()=>{
const es=[...document.querySelectorAll('#doc .u')];const el=es.find(el=>{const r=el.getBoundingClientRect();return r.top>100&&r.top<700;});
return el?{id:el.dataset.u,top:el.getBoundingClientRect().top,height:document.documentElement.scrollHeight}:null;
});
assert(pin,'a reading anchor is visible');await p.waitForTimeout(1400);
const drift=await p.evaluate(pin=>({top:document.querySelector(`[data-u="${pin.id}"]`).getBoundingClientRect().top-pin.top,height:document.documentElement.scrollHeight-pin.height}),pin);
assert(Math.abs(drift.top)<1 && Math.abs(drift.height)<1,JSON.stringify(drift));
results.push({width,drift});
await p.evaluate(()=>__reader.scrubTo(3.5));await p.waitForTimeout(400);
const animation=await p.evaluate(()=>({staged:__reader.staged,animations:document.getAnimations().length,pos:__reader.pos}));
assert(animation.staged || animation.animations>0,'level changes must still animate');
results.push({width,animation});
if(width===1512)await p.screenshot({path:path.join(out,'animation.png')});
await p.evaluate(()=>__reader.letGo());await p.waitForTimeout(1500);
// Resume page scrolling while a fresh keyframe can be in progress, then request another level.
await p.mouse.move(650,450);await p.mouse.wheel(0,1100);await p.waitForTimeout(790);await p.mouse.wheel(0,-500);
await p.evaluate(()=>__reader.setLevel(2));await p.waitForTimeout(1800);
assert.equal(await p.evaluate(()=>__reader.level),2);
await p.evaluate(()=>__reader.setLevel(4));await p.waitForTimeout(1800);
}
assert.deepEqual(errors,[]);
fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify({results,errors},null,2));console.log(JSON.stringify({results,errors}));
await b.close();
})().catch(e=>{console.error(e);process.exit(1);});
