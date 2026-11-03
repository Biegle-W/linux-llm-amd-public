# Mixed RGB RAM lighting restored — November 3, 2026

All three RGB RAM sticks now respond to the PC Lights controller. The owner
visually confirmed all three are white. Four DIMMs are installed in total; one
has no RGB.

The ASUS motherboard migration had disabled the RAM detectors, configured zero
expected RGB modules, removed the narrow RAM access rule, and left White/Off
profiles containing only the motherboard. Re-enabling Corsair detection covered
two sticks. The third, described by the owner as Chinese-market Corsair, uses an
ENE controller and needs the separate ENE SMBus DRAM detector.

The ENE identity sequence was positively matched before enabling that detector.
The final detection is two Corsair ten-LED controllers plus one ENE eight-LED
controller and the ASUS TX GAMING B760M WIFI motherboard. The controller reports
3/3 RGB RAM devices and requires exactly one ENE device; an extra Corsair device
cannot substitute for a missing ENE device.

White and Off now explicitly apply Direct mode to both RAM controller families
and Static mode to the motherboard, then validate inventory, mode, LED layout
and every requested color. Complete White/Off profiles have been regenerated.
Persistent access is restricted to the motherboard I801 bus; boot module loading
and the existing enabled restore service are retained. The device-access setup
preserves RAM access on future runs.

Validation: Off, White and final restore pass software application validation;
13 CPU validator checks pass, including missing ENE, wrong ENE color and
extra-Corsair substitution cases. The owner visually confirmed the final White
result. Current preference is White. A new reboot was not performed for this
repair. No inference runtime, GPU workload, fan curve, BIOS, SPD setting, guard,
model hold or recurring schedule was changed.

Evidence: [structured results](results/rgb-ram-controller-fix-2026-11-03.json).
Protocol reference: [OpenRGB 1.1 ENE detector](https://raw.githubusercontent.com/CalcProgrammer1/OpenRGB/release_1.1/Controllers/ENESMBusController/ENESMBusControllerDetect.cpp).
Access reference: [OpenRGB udev documentation](https://openrgb.org/udev.html).
