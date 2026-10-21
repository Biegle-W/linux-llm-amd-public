"""Open the existing native worker UI once ready, without starting another server."""
import json
import os
import subprocess
import threading
import urllib.error
import urllib.parse
import urllib.request

PORTS={'strata':30021,'maya':30031}
ROUTERS={'strata':30020,'maya':30030}


def open_browser(url):
    try:
        subprocess.Popen(['xdg-open',url],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                         start_new_session=True)
        print('Opened native Chat/Monitor in the default browser.',flush=True)
    except OSError as error:
        print(f'Could not open a browser ({type(error).__name__}); use {url}',flush=True)


def start_llama_chat(backend,model,enabled,stopped):
    """Load one profile through the guarded llama.cpp router, then open its built-in Chat."""
    base='http://127.0.0.1:8080/'
    url=base+'#/?model='+urllib.parse.quote(model)
    print(f'llama.cpp Chat for {model}: {url}',flush=True)
    display=enabled and (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def load_and_open():
        requested=False
        for _ in range(1800):
            if stopped.is_set() or backend.poll() is not None:return
            try:
                if not requested:
                    with opener.open(base+'health',timeout=2) as response:
                        if json.load(response).get('status')!='ok':
                            stopped.wait(1);continue
                    # The router applies memory admission and runtime selection to POSTs.
                    request=urllib.request.Request(base+'models/load',json.dumps({'model':model}).encode(),
                                                   {'Content-Type':'application/json'})
                    try:
                        with opener.open(request,timeout=600) as response:response.read()
                    except urllib.error.HTTPError as error:
                        message=error.read().decode(errors='replace')
                        if 'already running' not in message:
                            print(f'{model} was not loaded: {message}',flush=True);return
                    requested=True
                with opener.open(base+'v1/models',timeout=5) as response:data=json.load(response)['data']
            except (OSError,ValueError):
                stopped.wait(1);continue
            status=next((item.get('status',{}) for item in data if item['id']==model),{})
            if status.get('failed'):
                print(f'{model} failed to load; inspect the llama.cpp log.',flush=True);return
            if status.get('value')!='loaded':
                stopped.wait(1);continue
            if display:open_browser(url)
            else:print('Open this address in a browser when needed; the backend uses the current terminal.',flush=True)
            return
        print('Model did not become ready within 30 minutes; inspect the backend log.',flush=True)
    threading.Thread(target=load_and_open,daemon=True).start()
    return stopped


def start_frontend(kind,backend,enabled=True,model=None):
    stopped=threading.Event()
    if kind=='llama' and model:return start_llama_chat(backend,model,enabled,stopped)
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
            open_browser(url)
            return
        print('Frontend did not become ready within 30 minutes; inspect the backend log.',flush=True)
    threading.Thread(target=open_ready,daemon=True).start()
    return stopped
