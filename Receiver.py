import can
from CanTpReceive import CanTpReceive

DEFINE_ARBITRATION_ID = 0x123

if __name__ == "__main__":
    bus = can.Bus(interface = 'neovi', channel = 1, bitrate = 1000000, receive_own_messages = False)
    cantp_sender = CanTpReceive(bus = bus, arbitration_id = DEFINE_ARBITRATION_ID, is_extended_id = False, is_fd = True)
    while True:
        cantp_sender.receive_message()

    bus.shutdown()