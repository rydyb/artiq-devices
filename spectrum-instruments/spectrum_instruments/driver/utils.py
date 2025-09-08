import os
import spcm


def list_devices():
    devices = []

    for devfile in os.listdir("/dev"):
        if not devfile.startswith("spcm"):
            continue

        device_identifier = f"/dev/{devfile}"
        with spcm.Card(device_identifier) as card:
            devices.append(
                {
                    "device_identifier": device_identifier,
                    "serial_number": card.sn(),
                    "family": card.family(),
                    "num_channels": card.num_channels(),
                    "product_name": card.product_name(),
                }
            )

    return devices
