# Hardware status and safety

Live acquisition is unavailable. `acquire EXPERIMENT --dry-run` exercises the
shared mock lifecycle for every physical module. Without `--dry-run`, the CLI
requires `--enable-hardware --arm --config FILE`; an armed request still stops
at the unimplemented live adapter. No code here initializes GPIO or enables
motor power. `Clock` and `Compass` calculate bounded steering plans only; they
are new illustrative controller interfaces, not recovered controller firmware.

Before replacing the stub, an operator must verify the physical apparatus
revision, wiring/polarity, IMU axes, calibrated servo command limits, separate
motor/servo rails, current limits, bench support, clearance, and a tested
independent latching power-cut e-stop. Store the calibration and operator
approval in the run manifest. Historical pins are unverified clues; the example
config deliberately has no active pin map. The historical [35,105] command
limits and neutral 75 are command units, not wheel degrees.

`SafetyGuard` requires all checklist items, matching confirmed/configured
revisions, two arming flags, a timeout and a duty cap. It checks e-stop and
deadline before each command, disarms on command error and stops on exit.
This is a software guard tested with mocks. It cannot stop a stalled process
by itself: a commissioned adapter needs an independent hardware watchdog that
cuts power without further Python execution. An independent physical e-stop
is required regardless of the watchdog. Tests never touch real hardware.

WP1 needs independent cutoff feedback, not a software stop flag. WP2 needs
verified servo calibration and physical-response timing. WP3 needs calibrated
camera/survey metadata and quality rejection. WP4/WP5/D1 need matched starts,
approved/balanced order, recorded battery, timeout and external success rules.
WP7 additionally needs a signed physical intervention record. WP8 needs an
operator-supervised sorter check and validated colour calibration. Each shares
the same default-off power/arming/cleanup boundary; none has a live adapter.

Missing videos warn without inventing a path. Fresh event clocks are actual
aware UTC and monotonic readings. Equal monotonic readings can occur at clock
resolution; `event_index` orders those ties without inventing nanoseconds.
