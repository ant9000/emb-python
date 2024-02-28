#!/usr/bin/python3
""" EBI sender sample """

import sys
import time
from ebi import EBI

if __name__ == "__main__":
    DEVICE = "/dev/ttyUSB0"
    if len(sys.argv) > 1:
        DEVICE = sys.argv[1]
    e = EBI(DEVICE, debug=True)
    print("RESET:", e.reset())
    print("STATE:", e.state)
    if e.state['state'] == 'Online':
        print("NETWORK STOP:", e.network_stop())
    print("ENERGY SAVE -> TX ONLY:", e.energy_save(0x02))
    print("OUTPUT POWER -> +13dBm:", e.output_power(13))
    print(
        "OPERATING CHANNEL -> CH 2 (868.300 MHz), SF 7, BW 125 kHz, CR 4/5:",
        e.operating_channel(2,7,0,1)
    )
    print("NETWORK START:", e.network_start())
    payload = [0x12, 0x12, 0x12] + list(range(1,21))
    while True:
        p, r = e.hex(payload), e.send_data(payload=payload)
        print(f"SEND DATA:\n\tpayload: {p}\n\tresult: {r}")
        time.sleep(1)
    print("NETWORK STOP:", e.network_stop())
