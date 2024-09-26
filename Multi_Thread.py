import can
import threading

from CanTpTransmit import CanTpTransmit
from CanTpReceive import CanTpReceive

SEND_ARBITRATION_ID = 0x123
RECEIVE_ARBITRATION_ID = 0x123

bus = can.Bus(interface = 'neovi', channel = 1, bitrate = 1000000, receive_own_messages = False)

cantp_sender = CanTpTransmit(bus = bus, arbitration_id = SEND_ARBITRATION_ID, is_extended_id = False, is_fd = False)
cantp_receiver = CanTpReceive(bus = bus, arbitration_id = RECEIVE_ARBITRATION_ID, is_extended_id = False, is_fd = False)

def fun_send_message():
    while True:
        user_input = input("Input: ")
        cantp_sender.send_message(list(user_input.encode('utf-8')))
    

def fun_receive_message():
    while True:
        cantp_receiver.receive_message()

if __name__ == "__main__":
    receive_thread = threading.Thread(target = fun_receive_message)
    send_thread = threading.Thread(target = fun_send_message) 

    receive_thread.start()
    send_thread.start()

    receive_thread.join()
    send_thread.join()
    
    bus.shutdown()