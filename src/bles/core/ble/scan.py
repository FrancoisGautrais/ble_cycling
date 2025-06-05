import asyncio
from functools import partial

from bleak import BleakScanner


def detection_callback(data, device, advertisement_data):
    name = advertisement_data.local_name or "Nom inconnu"
    data[device.address] = {
        "name": name,
        "address": device.address,
        "rssi": device.rssi,
        "manufacturer_data": advertisement_data.manufacturer_data
    }

async def scan_ble_devices(scan_time=10):
    print("Scan des dispositifs BLE en cours (5 secondes)...\n")
    data = {}
    scanner = BleakScanner(detection_callback=partial(detection_callback, data))


    await scanner.start()
    await asyncio.sleep(10)
    await scanner.stop()


    print(data)
    return data


if __name__ == "__main__":
    asyncio.run(scan_ble_devices())