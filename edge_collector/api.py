from fastapi import FastAPI
from pydantic import BaseModel
from edge_collector.ble.state_machine_instance import state_machine
import asyncio

app = FastAPI()
connected_devices = {}

CHAR_INDEX = {
    "motion": 0,
    "biometric": 1,
    "air": 2,
    "gnss": 3
}

class DeviceRequest(BaseModel):
    address: str

class CharacteristicRequest(BaseModel):
    address: str
    characteristic: str
    enabled: bool

#Metodo che fa partire la state_machine, importantissimo!!!!
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(state_machine.start())

async def update_device_state(new_state):

    address = state_machine.device_address

    print("callback state:", new_state)
    print("device:", address)
    print("connected_devices:", connected_devices)

    if address in connected_devices:
        connected_devices[address]["state"] = new_state.name
        print("NEW STATE", new_state.name)

@app.post("/connect")
async def connect(req: DeviceRequest):
    address = req.address

    connected_devices[address] = {
        "address": address,
        "state": "CONNECTING",
        "characteristics": {
            "motion": False,
            "biometric": False,
            "air": False,
            "gnss": False
        }
    }
    # assegna callback stato
    print("connected devices: ", connected_devices)
    state_machine.state_callback = update_device_state

    await state_machine.set_device(req.address)
    return {"status": "device selected"}

@app.post("/disconnect")
async def disconnect(req: DeviceRequest):

    address = req.address

    print("Disconnect request:", address)

    if address not in connected_devices:
        return {"error": "device not found"}

    connected_devices[address]["characteristics"] = {
        "motion": False,
        "biometric": False,
        "air": False,
        "gnss": False
    }

    state_machine.device_configs[address] = {
        "motion": False,
        "biometric": False,
        "air": False,
        "gnss": False
    }

    # 🔥 chiama la state machine
    await state_machine.disconnect()

    # aggiorna stato UI (opzionale ma utile)
    connected_devices[address]["state"] = "DISCONNECTING"

    return {"status": "disconnecting"}


@app.get("/devices")
async def get_devices():

    return {
        "devices": list(connected_devices.values())
    }


# @app.post("/characteristic2")
# async def write_characteristic_old(req: CharacteristicRequest):
#
#     address = req.address
#     char = req.characteristic
#     enabled = req.enabled
#
#     print("Characteristic request:", address, char, enabled)
#
#     await state_machine.write_characteristic(char, enabled)
#
#     if address in connected_devices:
#         connected_devices[address]["characteristics"][char] = enabled
#
#     return {"status": "ok"}

@app.post("/characteristic")
async def write_characteristic(req: CharacteristicRequest):

    address = req.address
    char = req.characteristic
    enabled = req.enabled

    print("Characteristic request:", address, char, enabled)

    if address not in connected_devices:
        return {"error": "device not found"}

    if char not in CHAR_INDEX:
        return {"error": "invalid characteristic"}

    # aggiorna stato interno
    connected_devices[address]["characteristics"][char] = enabled
    state_machine.device_configs[address] = connected_devices[address]["characteristics"]
    chars = connected_devices[address]["characteristics"]

    value = bytearray([
        1 if chars["motion"] else 0,
        1 if chars["biometric"] else 0,
        1 if chars["air"] else 0,
        1 if chars["gnss"] else 0
    ])

    print("Writing bytearray:", list(value))

    await state_machine.write_raw_enable_realtime(value)

    return {"status": "ok"}
