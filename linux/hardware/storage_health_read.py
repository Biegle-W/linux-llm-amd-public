"""Read cached UDisks SSD SMART data; no refresh, self-test or disk mutation."""
import json
from pathlib import Path
import gi
from gi.repository import Gio, GLib


def read():
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    def call(path, interface, method, args=None):
        return bus.call_sync('org.freedesktop.UDisks2', path, interface, method,
            args, None, Gio.DBusCallFlags.NONE, 4000, None).unpack()
    objects = call('/org/freedesktop/UDisks2', 'org.freedesktop.DBus.ObjectManager', 'GetManagedObjects')[0]
    devices, seen = [], set()
    for block in Path('/sys/class/block').iterdir():
        if (block / 'partition').exists() or not (block / 'device').exists():
            continue
        info = objects.get('/org/freedesktop/UDisks2/block_devices/' + block.name, {})
        drive = info.get('org.freedesktop.UDisks2.Block', {}).get('Drive')
        if not drive or drive == '/' or drive in seen:
            continue
        seen.add(drive)
        interfaces = objects.get(drive, {})
        nvme = 'org.freedesktop.UDisks2.NVMe.Controller' in interfaces
        ata = 'org.freedesktop.UDisks2.Drive.Ata' in interfaces
        if not nvme and not ata:
            continue
        interface = 'org.freedesktop.UDisks2.NVMe.Controller' if nvme else 'org.freedesktop.UDisks2.Drive.Ata'
        props = call(drive, 'org.freedesktop.DBus.Properties', 'GetAll', GLib.Variant('(s)', (interface,)))[0]
        attrs = call(drive, interface, 'SmartGetAttributes', GLib.Variant('(a{sv})', ({},)))[0]
        devices.append({'device': block.name, 'nvme': nvme,
            'updated': props.get('SmartUpdated'), 'temperature_K': props.get('SmartTemperature'),
            'critical_warning': props.get('SmartCriticalWarning') if nvme else [],
            'failing': props.get('SmartFailing', False),
            'failing_attributes': props.get('SmartNumAttributesFailing', 0),
            'media_errors': attrs.get('media_errors') if nvme else None,
            'spare': attrs.get('avail_spare') if nvme else None,
            'spare_threshold': attrs.get('spare_thresh') if nvme else None,
            'wear_used_percent': attrs.get('percent_used') if nvme else None,
            'host_bytes_written': attrs.get('total_data_written') if nvme else None})
    return devices


if __name__ == '__main__':
    print(json.dumps(read()))
