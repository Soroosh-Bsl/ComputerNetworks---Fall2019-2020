import socket
import threading
import time
from pprint import pprint

import TCPHeader

states = ['CLOSED', 'SYN_SENT', 'ESTABLISHED', 'FIN_WAIT1', 'FIN_WAIT2', 'TIME_WAIT']
server_ip = 'localhost'
server_port = 10000
server_ip_port = (server_ip, server_port)
client_port = 1000
udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp_client_socket.setblocking(False)
establish_time = 0
state = states[0]
initial_sequence_number = 0
done = False
last_acked = 3
fin_recvd = False
last_received = None
timeout = 4
window = 1
base = 1
base_time = 0
last_sent = 0
last_sent_time = 0
sent_time = {}
alpha = 0.125
beta = 0.25
estimated_rtt = 4
dev_rtt = 0
dropped = []
fin_number = None


def receiver():
    global state, states, server_ip, server_port, server_ip_port, client_port, udp_client_socket, establish_time, initial_sequence_number, last_acked, fin_recvd, last_received, base_time, base, window, alpha, beta, dev_rtt, estimated_rtt, timeout, dropped, fin_number
    while not fin_recvd:
        try:
            received_packet, address = udp_client_socket.recvfrom(20)
        except BlockingIOError:
            continue
        received_tcp = TCPHeader.make_tcp_from_bytes(received_packet)
        if received_tcp.ackFlag:
            if received_tcp.ackNumber > last_acked:
                window = min(window + (received_tcp.ackNumber - last_acked), 20)
                for i in range(last_acked, received_tcp.ackNumber):
                    if i not in dropped:
                        print(received_tcp.ackNumber, last_acked)
                        sent_time_set = False
                        while not sent_time_set:
                            try:
                                sample = time.time() - sent_time[str(i)]
                                sent_time_set = True
                            except KeyError:
                                sent_time_set = False
                        estimated_rtt = (1-alpha) * estimated_rtt + alpha*sample
                        dev_rtt = (1 - beta) * dev_rtt + beta*(abs(sample - estimated_rtt))
                        timeout = estimated_rtt + 4 * dev_rtt
            last_acked = received_tcp.ackNumber
            if received_tcp.ackNumber > base:
                base_time = time.time()
                base = received_tcp.ackNumber
        if received_tcp.finFlag:
            fin_recvd = True
            fin_number = received_tcp.sequenceNumber
        if received_tcp.sequenceNumber == last_received+1 or last_received is None:
            last_received = received_tcp.sequenceNumber
            print(last_received)
    return


def sender():
    global state, states, server_ip, server_port, server_ip_port, client_port, udp_client_socket, establish_time, initial_sequence_number, window, last_sent, last_sent_time, base, base_time, last_received
    while not done:
        if time.time() - base_time > timeout:
            if base not in dropped:
                dropped.append(base)
            window /= 2
            last_sent = base - 1
            packet = TCPHeader.TCPHeader(client_port, server_port, last_sent + 1, last_received + 1, 1, 0, 0, 1000).get()
            udp_client_socket.sendto(packet, server_ip_port)
            last_sent_time = time.time()
            last_sent += 1
            base_time = last_sent_time
        else:
            if last_acked - 1 + window > last_sent and time.time() - last_sent_time > 1:
                if last_sent+1 in dropped:
                    dropped.remove(last_sent+1)
                packet = TCPHeader.TCPHeader(client_port, server_port, last_sent + 1, last_received + 1, 1, 0, 0, 1000).get()
                udp_client_socket.sendto(packet, server_ip_port)
                last_sent_time = time.time()
                sent_time[str(last_sent + 1)] = last_sent_time
                last_sent += 1
    return


def handshake():
    global state, states, server_ip, server_port, server_ip_port, client_port, udp_client_socket, establish_time, initial_sequence_number, last_acked, last_sent, base_time, base, last_sent_time, last_sent, last_received
    while state != states[2]:
        if state == states[0]:
            initial_sequence_number = 1
            expected_ack = initial_sequence_number + 1
            packet = TCPHeader.TCPHeader(client_port, server_port, initial_sequence_number, 0, 0, 1, 0, 1000).get()
            udp_client_socket.sendto(packet, server_ip_port)
            last_sent = initial_sequence_number
            sent_time[str(last_sent)] = time.time()
            last_sent_time = sent_time[str(last_sent)]
            base = initial_sequence_number
            base_time = last_sent_time
            state = states[1]
        elif state == states[1]:
            if time.time() - base_time > timeout:
                packet = TCPHeader.TCPHeader(client_port, server_port, initial_sequence_number, 0, 0, 1, 0, 1000).get()
                udp_client_socket.sendto(packet, server_ip_port)
                last_sent = initial_sequence_number
                sent_time[str(last_sent)] = time.time()
                last_sent_time = sent_time[str(last_sent)]
                base = initial_sequence_number
                base_time = last_sent_time
                continue
            try:
                received_packet, address = udp_client_socket.recvfrom(20)
            except BlockingIOError:
                continue
            server_port = address[1]
            server_ip = address[0]
            server_ip_port = (server_ip, server_port)
            received_tcp = TCPHeader.make_tcp_from_bytes(received_packet)
            if received_tcp.ackFlag and received_tcp.ackNumber == expected_ack and received_tcp.synFlag:
                last_acked = expected_ack
                establish_time = time.time()
                last_received = received_tcp.sequenceNumber
                ack_to_send = received_tcp.sequenceNumber + 1
                packet = TCPHeader.TCPHeader(client_port, server_port, expected_ack, ack_to_send, 1, 0, 0, 1000).get()
                initial_sequence_number = expected_ack
                last_sent = expected_ack
                sent_time[str(expected_ack)] = time.time()
                udp_client_socket.sendto(packet, server_ip_port)
                base = last_sent
                base_time = sent_time[str(expected_ack)]
                state = states[2]
    return True


def close(receiver_thread):
    global state, states, server_ip, server_port, server_ip_port, client_port, udp_client_socket, establish_time, initial_sequence_number, last_acked, fin_recvd, last_received, last_sent, sent_time, fin_number, base, base_time, timeout, time_wait_start, time_two_msl
    timeout = 4
    while state != states[0]:
        if state == states[2]:
            packet = TCPHeader.TCPHeader(client_port, server_port, last_sent+1, 0, 0, 0, 1, 1500).get()
            last_sent += 1
            sent_time[str(last_sent)] = time.time()
            base = last_sent
            base_time = sent_time[str(last_sent)]
            udp_client_socket.sendto(packet, server_ip_port)
            state = states[3]
        elif state == states[3]:
            if last_acked == last_sent+1:
                receiver_thread.join()
                state = states[0]
            else:
                if time.time() - base_time > timeout:
                    packet = TCPHeader.TCPHeader(client_port, server_port, last_sent, 0, 0, 0, 1, 100).get()
                    sent_time[str(last_sent)] = time.time()
                    base = last_sent + 1
                    base_time = sent_time[str(last_sent)]
                    udp_client_socket.sendto(packet, server_ip_port)
        #
        # elif state == states[4]:
        #     if fin_recvd:
        #         print(fin_number+1)
        #         packet = TCPHeader.TCPHeader(client_port, server_port, 0, fin_number+1, 1, 0, 0, 700).get()
        #         udp_client_socket.sendto(packet, server_ip_port)
        #         print("From4Close", TCPHeader.make_tcp_from_bytes(packet).sequenceNumber)
        #         time_wait_start = time.time()
        #         fin_recvd = False
        #         state = states[5]
        #
        # elif state == state[5]:
        #     if fin_recvd:
        #         print(fin_number+1)
        #         packet = TCPHeader.TCPHeader(client_port, server_port, 0, fin_number+1, 1, 0, 0, 700).get()
        #         udp_client_socket.sendto(packet, server_ip_port)
        #         print("From4Close", TCPHeader.make_tcp_from_bytes(packet).sequenceNumber)
        #         fin_recvd = False
        #
        #     if time.time() - time_wait_start > time_two_msl:
        #         state = state[0]

    return True


def run():
    global state, states, server_ip, server_port, server_ip_port, client_port, udp_client_socket, establish_time, initial_sequence_number, done
    if handshake():
        print("handshake done")
        receiver_thread = threading.Thread(target=receiver, args=())
        sender_thread = threading.Thread(target=sender, args=())
        receiver_thread.start()
        sender_thread.start()
        while True:
            time_passed = time.time() - establish_time
            if time_passed > 30:
                print("Entered")
                done = True
                sender_thread.join()
                print("Sender Joined")
                close(receiver_thread)
                break


run()
# TODO handle handshake and close packets timeout
