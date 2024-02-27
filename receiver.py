#!/usr/bin/python3
""" EBI receiver example """

import sys
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
    print("ENERGY SAVE -> ALWAYS ON:", e.energy_save(0x00))
    print(
        "OPERATING CHANNEL -> CH 2 (868.300 MHz), SF 7, BW 125 kHz, CR 4/5:",
        e.operating_channel(2,7,0,1)
    )
    print("NETWORK ADDRESS -> 00:02:", e.network_address([0,2]))
    print("NETWORK START:", e.network_start())
    while True:
        pkt = e.receive()
        if pkt:
            MSG = 'options: {options}, rssi: {rssi}, src: {src}, dst: {dst}, data:'
            print(MSG.format(**pkt))
            print(pkt['data'])
