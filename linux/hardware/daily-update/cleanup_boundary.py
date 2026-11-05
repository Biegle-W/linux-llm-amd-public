"""Contain an explicitly completed owned scope; never fabricate memory readings."""
def drain_completed_scope(scope, progress, terminal):
    if progress.get('phase') != 'cleanup':
        raise RuntimeError('Missing memory telemetry outside owned cleanup')
    status = terminal.get('status', '')
    if not (status.startswith('passed') or status in ('failed','completed-local-comparison')):
        raise RuntimeError('Owned runner has not committed a terminal result')
    # Same pinned cgroup containment used by the ordinary failure path. A live
    # scope is terminated and must become empty before sampling can continue.
    scope.terminate()
    if scope.populated():
        raise RuntimeError('Owned cleanup still populated after termination')
