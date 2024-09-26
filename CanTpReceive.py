import can
import time
from enum import Enum

OFFSET_FLOWCONTROL_ARBITRATION_ID = 0x300

class FrameType(Enum):
    SINGLE_FRAME        = 0         # Single Frame (SF)
    FIRST_FRAME         = 1         # First Frame (FF)
    CONSECUTIVE_FRAME   = 2         # Consecutive Frame (CF)
    FLOW_CONTROL        = 3         # Flow Control Frame (FC)

class FlowState(Enum):
    FS_CTS              = 0         # Continue To Send (CTS)
    FS_WAIT             = 1         # Wait (WAIT)
    FS_OVFLW            = 2         # Overflow (OVFLW)

class TimeType(Enum):
    N_AS                = 1         # Transmission time for CAN frame on sender side
    N_BS                = 3         # Time until next FlowControl N_PDU
    N_CS                = 1         # Time until next ConsecutiveFrame N_PDU: N/A

    N_AR                = 1         # Transmission time for CAN frame on receiver side
    N_BR                = 0.1       # Time until next FlowControl N_PDU: N/A
    N_CR                = 3         # Time until next Consecutive Frame N_PDU

class CanTpReceive:
    def __init__(self, bus, arbitration_id, is_extended_id, is_fd,):
        self.bus = bus
        self.arbitration_id = arbitration_id
        self.is_extended_id = is_extended_id
        self.is_fd = is_fd

        self.finish_flag = False
        self.data_buffer = []
        self.max_buffer_length = 10000
        self.current_buffer_length = 0
        self.num_consecutive_frame = 0
        self.expected_data_length = 0   

        self.block_size = 0x03
        self.st_min = 0x0A              #0x7F - 127ms

    def receive_message(self):
        self.finish_flag = False
        self.data_buffer = []
        self.max_buffer_length = 10000
        self.current_buffer_length = 0
        self.num_consecutive_frame = 0
        self.expected_data_length = 0

        key = False
        print("Receiver - Start...")
        while not self.finish_flag:
            time_start = time.time()
            arbitration_id_flag = False
            while (time.time() - time_start) <= TimeType.N_CR.value:
                message : can.Message = self.bus.recv(timeout=1)
                if message and message.arbitration_id == self.arbitration_id:
                    arbitration_id_flag = True
                    break

            if arbitration_id_flag == True:       
                key = True
                pci = message.data[0] >> 4
                if pci == FrameType.SINGLE_FRAME.value:
                    self._receive_single_frame_(message)
                elif pci == FrameType.FIRST_FRAME.value:
                    self._receive_first_frame_(message)
                elif pci == FrameType.CONSECUTIVE_FRAME.value:
                    self._receive_consecutive_frame_(message)
                else:
                    self._error_frame()
            else:
                if key == True:
                    print("Receiver - Timeout.")
                    break
        print("Receiver - Finished.")

    def _receive_single_frame_(self, message):
        length = message.data[0] & 0x0F or message.data[1]
        self.expected_data_length = length
        start_index = 1 if message.data[0] != 0 else 2
        self._append_data(message.data[start_index:start_index + length])
        print(f"Receiver - Single frame: {self.data_buffer} Current data length: {self.current_buffer_length} Expected: {self.expected_data_length}")
        self._print_data()

    def _receive_first_frame_(self, message):
        length = ((message.data[0] & 0x0F) << 8) | message.data[1]
        if length == 0:  
            length = (message.data[2] << 24) | (message.data[3] << 16) | (message.data[4] << 8) | message.data[5]
            start_index = 6
        else:
            start_index = 2

        self.expected_data_length = length
        if length <= self.max_buffer_length:
            self._append_data(message.data[start_index:])
            print(f"Receiver - First frame: {message.data[start_index:]} Current data length: {self.current_buffer_length} Expected: {self.expected_data_length}")
            self._send_flowcontrol_frame_(FlowState.FS_CTS)
        else:
            self._send_flowcontrol_frame_(FlowState.FS_OVFLW)
            self.finish_flag = True

    def _receive_consecutive_frame_(self, message):
        self.num_consecutive_frame += 1
        sequence = message.data[0] & 0x0F
        if self.current_buffer_length + len(message.data[1:]) < self.expected_data_length:
            self._append_data(message.data[1:])
            print(f"Receiver - Sequence: {sequence} - Data: {message.data[1:]} Current data length: {self.current_buffer_length} Expected: {self.expected_data_length}")
            if self.num_consecutive_frame == self.block_size:
                self._send_flowcontrol_frame_(FlowState.FS_WAIT)
                self._send_flowcontrol_frame_(FlowState.FS_CTS)
                self.num_consecutive_frame = 0
        else:
            self._append_data(message.data[1:self.expected_data_length - self.current_buffer_length + 1])
            print(f"Receiver - Sequence: {sequence} - Data: {message.data[1:]} Current data length: {self.current_buffer_length} Expected: {self.expected_data_length}")
            self.finish_flag = True
            self._print_data()

    def _send_flowcontrol_frame_(self, flow_status):
        print("arbritration_id", self.arbitration_id + OFFSET_FLOWCONTROL_ARBITRATION_ID)
        # time.sleep(TimeType.N_BR.value)
        payload = [(FrameType.FLOW_CONTROL.value << 4) | flow_status.value, self.block_size, self.st_min] + [0x00] * 5
        message = can.Message(arbitration_id= self.arbitration_id + OFFSET_FLOWCONTROL_ARBITRATION_ID, data=payload, is_extended_id=self.is_extended_id, is_fd=self.is_fd)
        self.bus.send(message)
        print("Receiver - Send flowcontrol frame", payload)

    def _append_data(self, data):
        self.data_buffer += data
        self.current_buffer_length += len(data)

    def _print_data(self):
        print(f"Receiver - Total data: {bytes(self.data_buffer).decode('utf-8', errors='ignore')}")
        self.finish_flag = True

    def _error_frame(self):
        print("Receiver - Error received PCI")
        self.finish_flag = True