"""Avoid starting another GPU backend over an existing model worker."""
import socket


def require_worker_ports_free(ports):
    for port, name in ports:
        with socket.socket() as probe:
            probe.settimeout(1)
            occupied = probe.connect_ex(('127.0.0.1', port)) == 0
        if occupied:
            raise RuntimeError(f'{name} still has a model worker running. Close its backend terminal before switching backends.')
