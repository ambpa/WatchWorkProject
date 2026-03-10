from fastapi import FastAPI
from pydantic import BaseModel
from edge_collector.ble.state_machine_instance import state_machine
import asyncio

app = FastAPI()
connected_devices = {}



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

@app.get("/devices")
async def get_devices():

    return {
        "devices": list(connected_devices.values())
    }


@app.post("/characteristic")
async def write_characteristic(req: CharacteristicRequest):

    address = req.address
    char = req.characteristic
    enabled = req.enabled

    print("Characteristic request:", address, char, enabled)

    await state_machine.write_characteristic(char, enabled)

    if address in connected_devices:
        connected_devices[address]["characteristics"][char] = enabled

    return {"status": "ok"}