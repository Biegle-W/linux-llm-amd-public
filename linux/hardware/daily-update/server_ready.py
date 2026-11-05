def server_ready(health, model, backend_ready=None):
    if health.get('unloaded') is True:
        return False
    if any(health.get(key) is not None and health[key]!=model for key in ['model','active_model']):
        return False
    if health.get('loaded') is True:
        return True
    if health.get('status')=='ok' and health.get('active_model')==model:
        return True
    if (health.get('status')=='ok' and backend_ready
            and backend_ready.get('loaded') is True and backend_ready.get('model')==model
            and backend_ready.get('backend')=='llama'):
        return True
    return (health.get('status')=='ok' and health.get('model')==model
            and health.get('unloaded') is False)
