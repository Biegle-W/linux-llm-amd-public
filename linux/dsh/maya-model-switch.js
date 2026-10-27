/* Same-origin controls for the maintained Maya router; no engine parameters. */
(() => {
  const panel = document.createElement('section');
  panel.style.cssText = 'padding:12px;display:grid;gap:8px;border-bottom:1px solid var(--st-border,#444)';
  const label = document.createElement('label');
  label.textContent = 'Maya model';
  label.htmlFor = 'managed-maya-model';
  const select = document.createElement('select');
  select.id = label.htmlFor;
  select.className = 'st-input';
  select.style.cssText = 'width:100%;max-width:100%;color:inherit;background:var(--st-bg,#151522)';
  const button = document.createElement('button');
  button.className = 'st-btn';
  button.textContent = 'Switch model';
  const status = document.createElement('div');
  status.setAttribute('role', 'status');
  status.setAttribute('aria-live', 'polite');
  status.style.cssText = 'font-size:12px;overflow-wrap:anywhere';
  panel.append(label, select, button, status);
  const side = document.querySelector('.side');
  if (!side) return;
  side.insertBefore(panel, side.querySelector('nav'));
  let state = null, dirty = false, fetching = false, sending = false, actionError = '';
  const requestHeaders = () => typeof headers === 'function' ? headers(true) : {'Content-Type': 'application/json'};
  select.addEventListener('change', () => { dirty = true; actionError = ''; render(); });
  function render() {
    if (!state) { button.disabled = true; return; }
    const loading = state.operation?.state === 'loading';
    if (loading) select.value = state.operation.model;
    select.disabled = loading || sending;
    button.disabled = loading || sending || state.busy || (!state.memory_fault && select.value === state.active_model);
    button.textContent = state.memory_fault ? 'Reload model' : 'Switch model';
    const context = state.models.find(model => model.id === state.active_model)?.context;
    if (loading || !state.active_model) {
      const modelLine = document.getElementById('side-model');
      if (modelLine) modelLine.textContent = loading || state.busy ? 'Model loading…' : 'No model loaded';
      if ((loading || state.busy) && typeof setPill === 'function') setPill('reading', 'Loading model');
    }
    status.textContent = actionError || state.memory_fault || (loading ? `Loading ${state.operation.model}… Keep this page open.` :
      state.operation?.state === 'error' ? `Switch failed: ${state.operation.error}` :
      state.active_model ? `Loaded: ${state.active_model} · ${context?.toLocaleString()} tokens` :
      state.busy ? 'Loading Maya… Keep this page open.' : 'No model loaded. Choose a model and load it.');
  }
  async function refresh() {
    if (fetching) return;
    fetching = true;
    try {
      const response = await fetch('/managed/models', {headers: requestHeaders(), cache: 'no-store'});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Cannot read Maya model status');
      const previous = state?.active_model;
      state = data;
      if (state.active_model && previous !== state.active_model && typeof loadHealth === 'function') {
        loadHealth(); // Refresh native model-specific sampling/context without discarding chats.
      }
      if (!select.options.length) {
        for (const model of state.models) {
          const option = document.createElement('option');
          option.value = model.id;
          option.textContent = ({'glm-5.3-flash-maya': 'GLM 5.3 Flash',
            'deepseek-v4.1-flash-1017-maya': 'DeepSeek V4.1 Flash · XS + DSpark'})[model.id] || model.name;
          option.title = model.name;
          select.append(option);
        }
      }
      if ((!dirty || previous !== state.active_model) && state.active_model) {
        select.value = state.active_model;
        dirty = false;
      }
      render();
    } catch (error) {
      status.textContent = error.message;
      button.disabled = true;
    } finally { fetching = false; }
  }
  button.addEventListener('click', async () => {
    actionError = '';
    sending = true;
    render();
    try {
      const response = await fetch('/managed/models/load', {
        method: 'POST', headers: requestHeaders(), body: JSON.stringify({model: select.value})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Model switch failed');
      state = data;
      dirty = false;
      render();
    } catch (error) { actionError = error.message; }
    finally { sending = false; await refresh(); }
  });
  refresh();
  const timer = setInterval(refresh, 2000);
  window.addEventListener('pagehide', () => clearInterval(timer), {once: true});
})();
