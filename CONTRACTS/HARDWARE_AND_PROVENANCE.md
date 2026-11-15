# Historical hardware constraints and provenance boundaries

From the engineering research paper, the approximate research vehicle is 18.5 cm × 12.8 cm, built around a Raspberry Pi 5 (8 GB), two wide-angle cameras, IMU, wheel encoders, three distance channels, geared motor and Ackermann steering servo. Hardware evolved across the project: MPU6050 → BNO08x variants; VL53L0X → VL6180X variants. Do not casually interchange driver APIs or assume a pin configuration from one revision is current.

A late-stage *documented, but not automatically confirmed* pin map is: motor PWM GPIO13; direction GPIO5/GPIO6; steering servo GPIO22; wheel encoder GPIO17/GPIO27; manual start GPIO18. Steering neutral command 75, bounded to [35,105] command units. These are *not actual wheel degrees*. Motor power and servo power use separate regulated rails. No valid public data establish current live wiring, exact polarity, active sensor addresses, physical clearance, kill-switch integration, or actuator calibration. Require hardware profile confirmation before any live output.

`WP3` used overhead ArUco IDs 10/11 and surveyed poses. `WP2` used protractor angles and AS5600 readings. Hardware experiments may be safely reconstructed as **logging and replay tools**, and later used to acquire fresh data after a supervised commissioning procedure.

Experimental time window described in published processed release: 1–9 Nov 2026 IST. Never backfill newly generated records with historical timestamps. The reconstructed source is a *new implementation* and must not be presented as the original 2026 source code.

## Safety checklist for any actuation module

- Safe defaults: motor disabled on boot, import, crash and unhandled error; pins configured to safe state.
- Manual latching emergency-stop hardware independent of software; a software 'stop' does not replace hardware power cut.
- Explicit operator arming with timed deadman, physical clearance, bench support, power limit, logging and visible state.
- Never auto-run loops merely to obtain the historical sample count or historical output value.
- Use dry-run fixtures and GPIO mocks in CI; prohibit motor energizing from tests.
- Preserve one failed cutoff from the historical WP1 release; do not edit evidence to imply 24/24 passed.
