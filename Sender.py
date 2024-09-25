import can
import time
from CanTpTransmit import CanTpTransmit

DEFINE_ARBITRATION_ID = 0x123

if __name__ == "__main__":
    bus = can.Bus(interface = 'neovi', channel = 1, bitrate = 1000000, receive_own_messages = False)
    cantp_sender = CanTpTransmit(bus = bus, arbitration_id = DEFINE_ARBITRATION_ID, is_extended_id = False, is_fd = True)
    while True:
        user_input = input("Input: ")
        cantp_sender.send_message(list(user_input.encode('utf-8')))
    
    bus.shutdown()