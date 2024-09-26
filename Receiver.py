import can
from CanTpReceive import CanTpReceive

RECEIVE_ARBITRATION_ID = 0x123

if __name__ == "__main__":
    bus = can.Bus(interface = 'neovi', channel = 1, bitrate = 1000000, receive_own_messages = False)
    cantp_receiver = CanTpReceive(bus = bus, arbitration_id = RECEIVE_ARBITRATION_ID, is_extended_id = False, is_fd = True)
    while True:
        cantp_receiver.receive_message()

    bus.shutdown()