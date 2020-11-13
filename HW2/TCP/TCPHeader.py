class TCPHeader:
    def __init__(self, sourcePort, destPort, sequenceNumber, ackNumber, ackFlag, synFlag, finFlag, window, checksum=0, headerLength=0, reserved=0, urgFlag=0, resetFlag=0, pushFlag=0, urgentPointer=0):
        self.sourcePort = sourcePort
        self.destPort = destPort
        self.sequenceNumber = sequenceNumber
        self.ackNumber = ackNumber
        self.headerLength = headerLength
        self.reserved = reserved
        self.urgFlag = urgFlag
        self.ackFlag = ackFlag
        self.resetFlag = resetFlag
        self.pushFlag = pushFlag
        self.synFlag = synFlag
        self.finFlag = finFlag
        self.window = window
        self.checksum = checksum
        self.urgentPointer = urgentPointer

    def get(self):
        source_port0 = self.sourcePort % 256
        source_port1 = int(self.sourcePort / 256)
        dest_port0 = self.destPort % 256
        dest_port1 = int(self.destPort / 256)
        seq_num0 = self.sequenceNumber % 256
        seq_num1 = int(self.sequenceNumber / 256) % 256
        seq_num2 = int(int(self.sequenceNumber / 256) / 256) % 256
        seq_num3 = int(int(int(self.sequenceNumber / 256) / 256) / 256)
        ack_num0 = self.ackNumber % 256
        ack_num1 = int(self.ackNumber / 256) % 256
        ack_num2 = int(int(self.ackNumber / 256) / 256) % 256
        ack_num3 = int(int(int(self.ackNumber / 256) / 256) / 256)
        x0 = self.finFlag
        x0 += (self.synFlag << 1)
        x0 += (self.resetFlag << 2)
        x0 += (self.pushFlag << 3)
        x0 += (self.ackFlag << 4)
        x0 += (self.urgFlag << 5)
        x0 += (self.reserved << 6)
        x0 += (self.headerLength << 12)
        x_0 = x0 % 256
        x_1 = int(x0 / 256) % 256
        window0 = self.window % 256
        window1 = int(self.window / 256) % 256
        checksum0 = self.checksum % 256
        checksum1 = int(self.checksum / 256) % 256
        urg_pointer0 = self.urgentPointer % 256
        urg_pointer1 = int(self.urgentPointer / 256) % 256

        return bytes([source_port1, source_port0, dest_port1, dest_port0, seq_num3, seq_num2, seq_num1, seq_num0, ack_num3, ack_num2, ack_num1, ack_num0, x_1, x_0, window1, window0, checksum1, checksum0, urg_pointer1, urg_pointer0])


def make_tcp_from_bytes(bytes_recvd):
    result = 0
    for b in bytes_recvd:
        result = result * 256 + int(b)
    urg_pointer = result % 65536
    result = result >> 16
    checksum = result % 65536
    result = result >> 16
    window = result % 65536
    result = result >> 16
    fin_flag = result % 2
    result = result >> 1
    syn_flag = result % 2
    result = result >> 1
    reset_flag = result % 2
    result = result >> 1
    push_flag = result % 2
    result = result >> 1
    ack_flag = result % 2
    result = result >> 1
    urg_flag = result % 2
    result = result >> 1
    reserved = result % 64
    result = result >> 6
    header_length = result % 16
    result = result >> 4
    ack_number = result % 4294967296
    result = result >> 32
    seq_number = result % 4294967296
    result = result >> 32
    dest_port = result % 65536
    result = result >> 16
    source_port = result % 65536

    return TCPHeader(source_port, dest_port, seq_number, ack_number, ack_flag, syn_flag, fin_flag, window, checksum, header_length, reserved, urg_flag, reset_flag, push_flag, urg_pointer)
