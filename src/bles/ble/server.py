import time

from bles.ble.fitness import FitnessClient
from bles.ble.heart import HeartClient


def get_ftms():
    device_address = 'FB:6B:21:56:45:A7'
    client = FitnessClient(device_address)
    client.run_thread()
    return client


def get_hrs():
    device_address = 'D2:60:F3:44:A7:07'
    client = HeartClient(device_address)
    client.run_thread()
    return client

def main():


    ftms = get_ftms()
    print(f"FTMS connetected")
    time.sleep(20)
    hrs = get_hrs()
    print(f"HRS connetected")
    ftms.join()
    hrs.join()


if __name__ == '__main__':
    main()
