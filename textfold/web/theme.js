// Apply before the styles load, so a saved preference also colours the first frame.
window.TFTheme = (() => {
  const key = 'pf-theme', system = matchMedia('(prefers-color-scheme: dark)');
  let mode = 'system';
  try { mode = localStorage.getItem(key) || 'system'; } catch {}
  if (!['system', 'light', 'dark'].includes(mode)) mode = 'system';
  function apply() {
    document.documentElement.dataset.theme = mode === 'system' ? (system.matches ? 'dark' : 'light') : mode;
  }
  system.addEventListener('change', apply);
  apply();
  return {
    get: () => mode,
    set(value) {
      mode = value;
      try { localStorage.setItem(key, mode); } catch {}
      apply();
    },
  };
})();
