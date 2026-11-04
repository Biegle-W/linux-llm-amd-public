"""Owner-selected software temperature ceiling, shared by campaign and SSD guards."""

TEMPERATURE_LIMIT_C = 100


def temperature_failure(thermal, *, check_cpu=True):
    """Evaluate existing sampled temperatures; hardware trip points remain telemetry."""
    for card in thermal['cards']:
        for value in card.get('temperature_c', {}).values():
            if value is not None and value >= TEMPERATURE_LIMIT_C:
                return f'GPU temperature at or above {TEMPERATURE_LIMIT_C:g} C'
    if check_cpu:
        for value in thermal.get('cpu_package_c', {}).values():
            if value is not None and value >= TEMPERATURE_LIMIT_C:
                return f'CPU temperature at or above {TEMPERATURE_LIMIT_C:g} C'
    return None
