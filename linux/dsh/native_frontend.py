"""Open the existing native worker UI once ready, without starting another server."""
import json
import os
import subprocess
import threading
import urllib.request

PORTS={'strata':30021,'maya':30031}
ROUTERS={'strata':30020,'maya':30030}


def start_frontend(kind,backend,enabled=True):
    stopped=threading.Event()
    if kind not in PORTS:return stopped
    url=f'http://127.0.0.1:{PORTS[kind]}/'
    print(f'{kind.title()} native Chat/Monitor: {url}',flush=True)
    if not enabled or not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        print('Open this address in a browser when needed; the backend uses the current terminal.',flush=True)
        return stopped
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def open_ready():
        for _ in range(1800):
            if stopped.is_set() or backend.poll() is not None:return
            try:
                with opener.open(f'http://127.0.0.1:{ROUTERS[kind]}/health',timeout=2) as response:managed=json.load(response)
                if managed.get('status')!='ok' or not managed.get('active_model') or managed.get('memory_fault'):
                    stopped.wait(1);continue
                with opener.open(url+'health',timeout=2) as response:state=json.load(response)
                if state.get('unloaded',False) or state.get('loaded',True) is False:
                    stopped.wait(1);continue
                if state.get('model')!=managed['active_model']:
                    stopped.wait(1);continue
            except (OSError,ValueError):
                stopped.wait(1);continue
            try:
                subprocess.Popen(['xdg-open',url],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                print('Opened native Chat/Monitor in the default browser.',flush=True)
            except OSError as error:
                print(f'Could not open a browser ({type(error).__name__}); use {url}',flush=True)
            return
        print('Frontend did not become ready within 30 minutes; inspect the backend log.',flush=True)
    threading.Thread(target=open_ready,daemon=True).start()
    return stopped
