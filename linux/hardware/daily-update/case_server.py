from pathlib import Path
import importlib.util,json,signal,sys,urllib.request
W=Path(sys.argv[1]).resolve()
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(W),str(R/'dsh')]

from prevention_guard import durable
cfg=json.loads((W/'profile.private.json').read_text());kind=cfg['backend'];model=cfg['model_name']
spec=importlib.util.spec_from_file_location('isolated_'+kind,R/'dsh'/(kind+'-router.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
server=None
def stop(*unused):raise KeyboardInterrupt
signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
try:
 if kind=='llama':
  m.CATALOG=[dict(c,enabled=True) for c in json.loads((R/'dsh/models.json').read_text()) if c['id']==model]
  m.native_port=18034
  m.activate_native('hip-amd',model=model);m.active_model=model;m.ensure_loaded(model)
 else:
  m.PUBLIC_PORT=18032;m.WORKER_PORT=18034
  # Qualification-only view; on-disk enable flags and production catalog are unchanged.
  m.PROFILES={model:dict(m.PROFILES[model],enabled=True)}
  m.ensure_worker(model)
 server=m.ThreadingHTTPServer(('127.0.0.1',18032),m.Handler)
 durable(W/'backend-ready.private.json',{'backend':kind,'model':model,'loaded':True,'profile_source':'normal managed profile; isolated ports/catalog view'})
 server.serve_forever()
except KeyboardInterrupt:pass
finally:
 if server:server.server_close()
 if kind=='llama':
  if m.memory_watch:m.memory_watch.set()
  m.stop_process(m.native)
 else:
  if hasattr(m,'closing'):m.closing.set()
  m.stop_worker()
