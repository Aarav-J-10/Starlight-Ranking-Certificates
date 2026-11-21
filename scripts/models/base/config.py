"""Units SI unless stated. ASSUMED values are not empirical calibration.

This model abstracts image-space wall control to geometric pursuit. It preserves
HSV-first candidate formation, released confidence/area gates, physical steering
saturation, three-lap event logic and camera-to-heading parking role division.
It does not execute or validate the Raspberry Pi competition program.
"""
import numpy as np

DEFAULT_MODEL = dict(steering_gain=1.2, color_error_scale=1.0,
    motor_tau=0.18, speed_scale=1.0, mount_attenuation=0.40,
    parking_camera_scale=1.0, dt=0.04, vehicle_length=0.250,
    force_perception_loss=0.0, rear_trigger_attenuation=.45,
    lab_quality_advantage=1., parking_arc_degrees=90., parking_center_shift=.05)
MODEL_KEYS = tuple(DEFAULT_MODEL)

def model_array(model=None):
    d = DEFAULT_MODEL.copy()
    if model:
        unknown = set(model)-set(d)
        if unknown: raise ValueError('Unknown model parameters: '+str(unknown))
        d.update(model)
    return np.asarray([d[k] for k in MODEL_KEYS],dtype=np.float64)

WHEELBASE=.1075
WIDTH=.128
NOMINAL_SPEED=.55
MAX_TIME=180.
CONFIDENCE_WEIGHTS=(.65,.20,.15)
CONFIDENCE_THRESHOLD=.55
SERVO_CENTER=75.
SERVO_LEFT=35.
SERVO_RIGHT=105.
