# ble/payloads/processed_motion.py
import struct
from .base import BLEPayloadDecoder

class ProcessedMotionDecoder(BLEPayloadDecoder):
    payload_type = "processed_motion"

    def decode(self, payload: bytes) -> dict:
        if len(payload) != 6:
            #print(len(payload), payload)
            return None
            raise ValueError("Invalid ProcessedMotion payload length")

        epoch = struct.unpack("<I", payload[0:4])[0]
        motion_state = payload[4]
        temperature = payload[5]
        print("motion_state", motion_state)
        print("temperature", temperature)
        return {
            "type": self.payload_type,
            "epoch": epoch,
            "motion_state": motion_state,
            "temperature_c": temperature,
        }


class RawMotionDecoder(BLEPayloadDecoder):
    payload_type = "raw_motion"

    def decode(self, payload: bytes):

        if len(payload) != 25:
            return None

        values = struct.unpack("<10h", payload[5:25])
        ax, ay, az = values[0:3]

        epoch = struct.unpack("<I", payload[0:4])[0]
        counter = payload[4]
        num_samples = payload[5]

        return {
            "type": self.payload_type,
            "epoch": epoch,
            "counter": counter,
            "ax": ax,
            "ay": ay,
            "az": az,
        }



class RawBiometricDecoder(BLEPayloadDecoder):
    payload_type = "raw_biometric"

    def decode(self, payload: bytes):
        #print(payload)
        if len(payload) != 36:
            return None

        epoch = struct.unpack("<I", payload[0:4])[0]
        counter = payload[4]
        num_samples = payload[5]

        samples = []

        offset = 6

        for _ in range(num_samples):

            red = int.from_bytes(payload[offset:offset+3], "little")
            infra = int.from_bytes(payload[offset+3:offset+6], "little")

            samples.append({
                "red": red,
                "infra": infra
            })

            offset += 6

        return {
            "type": self.payload_type,
            "epoch": epoch,
            "counter": counter,
            "samples": samples
        }