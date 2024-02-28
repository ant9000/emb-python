#!/usr/bin/python3
"""EBI example shell"""

import cmd
import sys
import shlex
from ebi import EBI

class EmbitShell(cmd.Cmd):
    """EBI Command shell"""
    prompt = "EMB> "

    def __init__(self, device, debug=True):
        self.debug = debug
        if self.debug:
            print("---Start Init")
        self._e = EBI(device)
        if self.debug:
            print("---Start Reset")
        self._e.reset()
        state = self._e.state
        self.intro = "EMBIT module {embit_module} - FW {firmware_version}\n".format(**state)
        if state['state'] == 'Online':
            self._e.network_stop()
        if self.debug:
            print("---Energy save")
        # Always on
        self._e.energy_save(0x00)
        # 868.100 MHz, 128 Chips/symbol, 125 kHz, 4/5
        self._params = { 'channel': 1, 'sf': 7, 'bw': 0, 'cr': 1 }
        if self.debug:
            print("---Operating channel")
        self._e.operating_channel(*self._params.values())
        if self.debug:
            print("---Start Network")
        self._e.network_start()
        super().__init__()

    def default(self, line):
        if line == "EOF":
            print("Bye!")
            return True
        return super().default(line)

    def do_debug(self, arg):
        """toggle debug mode
Usage: debug"""
        # pylint: disable=unused-argument
        self._e.debug = not self._e.debug
        print(f"{'debug': {self._e.debug}}")

    def do_state(self, arg):
        """get device state
Usage: state"""
        # pylint: disable=unused-argument
        ret = self._e.device_state()
        print(ret)

    def do_reset(self, arg):
        """reset device
Usage: reset"""
        # pylint: disable=unused-argument
        ret = self._e.device_state()
        print(ret)

    def do_power(self, arg):
        """get or set device power
Usage: power [value]

value: [0-256]"""
        value = None
        if arg:
            try:
                value = int(arg) % 256
            except ValueError:
                print(f"Invalid power value {arg}")
                return
        state = self._e.device_state()
        should_stop = value and state['state'] == 'Online'
        if should_stop:
            self._e.network_stop()
        ret = self._e.output_power(value)
        if should_stop:
            self._e.network_start()
        print(ret)

    def do_channel(self, arg):
        """get or set device channel parameters
Usage: channel [ch sf bw cr]

ch: 0x01 -> 868.100 MHz
    0x02 -> 868.300 MHz
    0x03 -> 868.500 MHz
    0x04 -> 869.525 MHz
sf: 0x07 -> 128 Chips/symbol
    0x08 -> 256 Chips/symbol
    0x09 -> 512 Chips/symbol
    0x0A -> 1024 Chips/symbol
    0x0B -> 2048 Chips/symbol
    0x0C -> 4096 Chips/symbol
bw: 0x00 -> 125 kHz
    0x01 -> 250 kHz
cr: 0x01 -> 4/5
    0x02 -> 4/6
    0x03 -> 4/7
    0x04 -> 4/8"""
        channel, spreading_factor, bandwidth, coding_rate = [None]*4
        args = (arg.split() + [""]*4)[:4]
        if args[0]:
            try:
                channel = EBI.LORA_CHANNEL[int(args[0])]
            except (ValueError, KeyError):
                print(f"Invalid channel value {args[0]}")
                return
            try:
                spreading_factor = EBI.LORA_SPREADING_FACTOR[int(args[1])]
            except (ValueError, KeyError):
                print(f"Invalid spreading factor value {args[1]}")
                return
            try:
                bandwidth = EBI.LORA_BANDWIDTH[int(args[2])]
            except (ValueError, KeyError):
                print(f"Invalid bandwith value {args[2]}")
                return
            try:
                coding_rate = EBI.LORA_CODING_RATE[int(args[3])]
            except (ValueError, KeyError):
                print(f"Invalid coding rate value {args[3]}")
                return
        state = self._e.device_state()
        should_stop = channel and state['state'] == 'Online'
        if should_stop:
            self._e.network_stop()
        ret = self._e.operating_channel(channel, spreading_factor, bandwidth, coding_rate)
        if channel and ret.get('status','') == 'Success':
            self._params = {
                'channel': channel, 'sf': spreading_factor,
                'bw': bandwidth, 'cr': coding_rate,
            }
        if 'channel' in ret:
            assert ret['channel'] == self._params['channel']
        ret.update(self._params)
        if should_stop:
            self._e.network_start()
        print(ret)

    def do_address(self, arg):
        """get or set device address
Usage: address [value]

value: [0-65535]"""
        value = None
        if arg:
            try:
                value = int(arg)
                value = [ (value & 0xFF00) >> 8, value & 0x00FF ]
            except ValueError:
                print(f"Invalid address value {arg}")
                return
        state = self._e.device_state()
        should_stop = value and state['state'] == 'Online'
        if should_stop:
            self._e.network_stop()
        ret = self._e.network_address(value)
        if should_stop:
            self._e.network_start()
        print(ret)

    def do_network(self, arg):
        """get or set device network identifier
Usage: network [value]

value: [0-65535]"""
        value = None
        if arg:
            try:
                value = int(arg)
                value = [ (value & 0xFF00) >> 8, value & 0x00FF ]
            except ValueError:
                print(f"Invalid network value {arg}")
                return
        state = self._e.device_state()
        should_stop = value and state['state'] == 'Online'
        if should_stop:
            self._e.network_stop()
        ret = self._e.network_identifier(value)
        if should_stop:
            self._e.network_start()
        print(ret)

    def do_send(self, arg):
        """send a network packet
Usage: send payload [dest]

dest: [0-65535]; specify no dest for broadcast"""
        if not arg:
            print("Please specify a payload to send")
            return
        payload, dst = (shlex.split(arg)+[None])[:2]
        payload = list(bytes(payload, 'utf8'))
        if dst is not None:
            try:
                dst = int(dst)
                dst = [ (dst & 0xFF00) >> 8, dst & 0x00FF ]
            except ValueError:
                print(f"Invalid destination value {dst}")
                return
        ret = self._e.send_data(payload=payload, dst=dst)
        print(ret)

    def do_receive(self, arg):
        """receive a network packet and print it
Usage: receive [timeout]

timeout in seconds; specify no timeout to wait forever"""
        timeout = None
        if arg:
            try:
                timeout = int(arg)
            except ValueError:
                print(f"Invalid timeout {arg}")
                return
        ret = self._e.receive(timeout)
        print(ret)

    def do_quit(self, arg):
        """quit EMB shell
Usage: quit"""
        # pylint: disable=unused-argument
        print("Bye!")
        return True

if __name__ == '__main__':
    DEVICE = "/dev/ttyUSB0"
    if len(sys.argv) > 1:
        DEVICE = sys.argv[1]
    shell = EmbitShell(DEVICE)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print("Bye!")
