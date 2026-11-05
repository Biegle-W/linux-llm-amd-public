import time

def await_completed(rows, count, check, timeout=1.0):
    """Let the HTTP proxy commit its already-finished response before the client verdict."""
    end=time.monotonic()+timeout
    while len(rows)==count and any(r['status']=='starting' for r in rows):
        check()
        if time.monotonic()>=end:
            raise TimeoutError('Proxy response completion was not committed')
        time.sleep(.01)
    if len(rows)!=count or any(r['status']!='completed' for r in rows):
        raise RuntimeError('Expected completed proxy requests')
