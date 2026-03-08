# ble/payloads/registry.py
from .processed_motion import ProcessedMotionDecoder, RawMotionDecoder, RawBiometricDecoder


PAYLOAD_DECODERS = {
    "processed_motion": ProcessedMotionDecoder(),
    "raw_motion": RawMotionDecoder(),
    "raw_biometric": RawBiometricDecoder(),
}
