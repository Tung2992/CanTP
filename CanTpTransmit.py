import can
import time
from enum import Enum


FLOWCONTROL_ARBITRATION_ID = 0x300

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
    N_BR                = 0.5       # Time until next FlowControl N_PDU: N/A
    N_CR                = 3         # Time until next Consecutive Frame N_PDU

class CanTpTransmit:
    def __init__(self, bus, arbitration_id, is_extended_id, is_fd):
        self.bus = bus
        self.arbitration_id = arbitration_id
        self.is_extended_id = is_extended_id
        self.is_fd = is_fd
        self.desired_lengths_classic = [8]                      # CAN 2.0 payload sizes
        self.desired_lengths_fd = [8, 12, 16, 20, 24, 32, 48, 64]  # CAN FD payload sizes
        self.length = None
        self.idx = 0
        self.sequence_number = 0
        self.finish_flag = False

    def send_message(self, data):
        self.finish_flag = False
        self.idx = 0
        self.sequence_number = 0
        self.length = len(data)

        print("Sender - Start...")
        if self.is_fd:
            self.desired_lengths = self.desired_lengths_fd
        else:
            self.desired_lengths = self.desired_lengths_classic

        if self.length <= self._max_single_frame_payload_size():
            self._send_single_frame(data)
        else:
            self._send_multiple_frames(data)

    def _max_single_frame_payload_size(self):
        return 62 if self.is_fd else 7

    # Handles both CAN FD and CAN Classic single frame sending
    def _send_single_frame(self, data):
        pci = self._create_single_frame_pci(self.length)
        payload = pci + list(data)
        payload = self._pad_payload(payload)
        self._send_can_message(payload)
        print("Sender - Finished")
        
    def _create_single_frame_pci(self, length):
        if self.is_fd and length > 7:
            return [(FrameType.SINGLE_FRAME.value << 4) , (length & 0xFF)]  # CAN FD uses 2 bytes for length
        return [(FrameType.SINGLE_FRAME.value << 4) | (length & 0x0F)]  # CAN Classic

    def _pad_payload(self, payload):
        for pad in self.desired_lengths:
            if pad >= len(payload):
                return payload + [0x00] * (pad - len(payload))
        return payload

    # Handles both CAN FD and CAN Classic multiple frame sending
    def _send_multiple_frames(self, data):
        self._send_first_frame(data)
        self._send_following_frames(data)

    def _send_first_frame(self, data):
        pci = self._prepare_first_frame_pci(self.length)
        first_frame_data = data[:self._first_frame_payload_size(self.length)]
        payload = pci + list(first_frame_data)
        self.idx = len(first_frame_data)
        self._send_can_message(payload)

    def _prepare_first_frame_pci(self, length):
        if length <= 4095:
            # For lengths up to 4095, CAN uses 2 bytes for PCI
            pci_1 = (FrameType.FIRST_FRAME.value << 4) | ((length >> 8) & 0xF)
            pci_2 = length & 0xFF
            return [pci_1, pci_2]
        else:
            # For lengths greater than 4095, CAN FD requires more bytes for PCI
            pci_1 = (FrameType.FIRST_FRAME.value << 4)
            pci_2 = 0x00  
            pci_3 = (length >> 24) & 0xFF
            pci_4 = (length >> 16) & 0xFF
            pci_5 = (length >> 8) & 0xFF
            pci_6 = length & 0xFF
            return [pci_1, pci_2, pci_3, pci_4, pci_5, pci_6]

    def _first_frame_payload_size(self, length):
        if self.is_fd:
            # CAN FD: Payload size is 62 if length <= 4095, otherwise 58
            return 62 if length <= 4095 else 58
        else:
            # CAN Classic: Payload size is 6 if length <= 4095, otherwise 2
            return 6 if length <= 4095 else 2

    def _send_following_frames(self, data):
        while not self.finish_flag:
            flow_control = self._receive_flowcontrol_frame()
            if not flow_control:
                print("Sender - No flow control frame received. Timeout")
                break
            fs, bs, st = flow_control
            self._handle_flow_control(fs, bs, st, data)
        print("Sender- Finished")

    def _handle_flow_control(self, fs, bs, st, data):
        send_consecutive_time = self._handle_st_(st)
        if fs == FlowState.FS_CTS.value:
            print("Sender - Continue to send state received.")
            for _ in range(bs):
                time.sleep(send_consecutive_time)
                self._send_consecutive_frame(data)
                if self.finish_flag:
                    break
        elif fs == FlowState.FS_WAIT.value:
            print("Sender - Wait state received.")
        elif fs == FlowState.FS_OVFLW.value:
            self.finish_flag = True
            print("Sender - Overflow state received.")

    def _handle_st_(self, st):
        if 0x00 <= st <= 0x7F:
            return st / 1000
        elif 0xF1 <= st <= 0xF9:
            return (st - 0xF0) / 10000
        else:
            return 0
        
    def _send_consecutive_frame(self, data):
        self.sequence_number = (self.sequence_number + 1) & 0xF
        pci = [(FrameType.CONSECUTIVE_FRAME.value << 4) | self.sequence_number]
        consecutive_frame_data = data[self.idx : self.idx + self._consecutive_frame_payload_size()]
        self.idx += len(consecutive_frame_data)
        if self.idx >= self.length:
            self.finish_flag = True
        payload = pci + list(consecutive_frame_data)
        payload = self._pad_payload(payload)
        self._send_can_message(payload)

    def _consecutive_frame_payload_size(self):
        return 63 if self.is_fd else 7

    def _send_can_message(self, payload):
        print(f"Sender - send frame with payload: {payload}")
        message = can.Message(arbitration_id=self.arbitration_id, data=payload, is_extended_id=self.is_extended_id, is_fd=self.is_fd)
        self.bus.send(message)

    def _receive_flowcontrol_frame(self):
        time_start = time.time()
        while (time.time() - time_start) <= TimeType.N_BS.value:
            message : can.Message = self.bus.recv(timeout=1)
            if message and message.arbitration_id == FLOWCONTROL_ARBITRATION_ID:
                return self._parse_flowcontrol_frame(message)
        return None

    def _parse_flowcontrol_frame(self, message):
        pci = message.data[0] >> 4
        if pci == FrameType.FLOW_CONTROL.value:
            return message.data[0] & 0x0F, message.data[1], message.data[2]
        return None
