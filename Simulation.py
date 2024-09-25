import can
import time
import threading

from CanTpTransmit import CanTpTransmit
from CanTpReceive import CanTpReceive

DEFINE_ARBITRATION_ID = 0x123

bus1 = can.interface.Bus('test', interface='virtual')
bus2 = can.interface.Bus('test', interface='virtual')

cantp_sender = CanTpTransmit(bus = bus1, arbitration_id = DEFINE_ARBITRATION_ID, is_extended_id = False, is_fd = False)
cantp_receiver = CanTpReceive(bus = bus2, arbitration_id = DEFINE_ARBITRATION_ID, is_extended_id = False, is_fd = True)

def fun_send_message():
    while True:
        string_to_send = input("User Input: ")
        cantp_sender.send_message(list(string_to_send.encode('utf-8')))
        time.sleep(5)

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
    
    bus1.shutdown()
    bus2.shutdown()

    print("End of simulation")