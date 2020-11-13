from __future__ import print_function
import socket
import threading
import time
from pprint import pprint
import TCPHeader

states = ['CLOSED', 'SYN_SENT', 'ESTABLISHED', 'FIN_WAIT1', 'FIN_WAIT2', 'TIME_WAIT']
server_ip = '10.0.0.2'
server_port = 47749
server_ip_port = (server_ip, server_port)
client_port = 1000
udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
udp_client_socket.bind(('', 47750))
udp_client_socket.setblocking(False)
establish_time = 0
state = states[0]
initial_sequence_number = 0
done = False
last_acked = 3
fin_recvd = False
last_received = None
timeout = 1
window = 1
base = 1
base_time = 0
last_sent = 0
last_sent_time = 0
sent_time = {}
alpha = 0.125
beta = 0.25
estimated_rtt = 1
dev_rtt = 0
dropped = []
fin_number = None
window_log = open('window_log.txt', 'w+')
sample_log = open('sample_log.txt', 'w+')
client_log = open('client_log.txt', 'w+')


def receiver():
    global state, states, server_ip, server_port, server_ip_port, client_port, udp_client_socket, establish_time, initial_sequence_number, last_acked, fin_recvd, last_received, base_time, base, window, alpha, beta, dev_rtt, estimated_rtt, timeout, dropped, fin_number, sample_log, window_log
    while not fin_recvd:
        try:
            received_packet, address = udp_client_socket.recvfrom(20)
        except:
            continue
        received_tcp = TCPHeader.make_tcp_from_bytes(received_packet)
        if received_tcp.ackFlag:
            if received_tcp.ackNumber > last_acked:
                window = min(window + (received_tcp.ackNumber - last_acked), 20)
                for i in range(last_acked, received_tcp.ackNumber):
                    if i not in dropped:
                        sent_time_set = False
                        while not sent_time_set:
                            try:
                                sample = time.time() - sent_time[str(i)]
                                sent_time_set = True
                            except KeyError:
                                sent_time_set = False
                        print(sample, file=sample_log)
                        estimated_rtt = (1-alpha) * estimated_rtt + alpha*sample
                        dev_rtt = (1 - beta) * dev_rtt + beta*(abs(sample - estimated_rtt))
                        timeout = estimated_rtt + 4 * dev_rtt
                # print("Timeout = {}".format(timeout))
                # print("Window = {}".format(window))
            last_acked = received_tcp.ackNumber
            if received_tcp.ackNumber > base:
                base_time = time.time()
                base = received_tcp.ackNumber
        if received_tcp.sequenceNumber == last_received+1 or last_received is None:
            last_received = received_tcp.sequenceNumber
    return


def sender():
    global state, states, server_ip, server_port, server_ip_port, client_port, udp_client_socket, establish_time, initial_sequence_number, window, last_sent, last_sent_time, base, base_time, last_received
    while not done:
        dif_time = time.time() - base_time
        if dif_time > timeout:
            print(dif_time, timeout)
            if base not in dropped:
                dropped.append(base)
                print("Packet {} Dropped".format(base), file=client_log)
            window = max(window//2, 1)
            last_sent = base - 1
            packet = TCPHeader.TCPHeader(client_port, server_port, last_sent + 1, last_received + 1, 1, 0, 0, 1000).get()
            udp_client_socket.sendto(packet, server_ip_port)
            last_sent_time = time.time()
            last_sent += 1
            base_time = last_sent_time
        else:
            if last_acked - 1 + window > last_sent and time.time() - last_sent_time > 0.1:
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
            except:
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
                fin_recvd = True
                receiver_thread.join()
                state = states[0]
            else:
                if time.time() - base_time > timeout:
                    packet = TCPHeader.TCPHeader(client_port, server_port, last_sent, 0, 0, 0, 1, 100).get()
                    sent_time[str(last_sent)] = time.time()
                    base = last_sent + 1
                    base_time = sent_time[str(last_sent)]
                    udp_client_socket.sendto(packet, server_ip_port)

    return True


def log():
    global fin_recvd, window_log, window
    now = time.time()
    while not fin_recvd:
        time.sleep(0.1)
        print(window, file=window_log)


def run():
    global state, states, server_ip, server_port, server_ip_port, client_port, udp_client_socket, establish_time, initial_sequence_number, done
    if handshake():
        print("Connection Established")
        log_thread = threading.Thread(target=log)
        receiver_thread = threading.Thread(target=receiver, args=())
        sender_thread = threading.Thread(target=sender, args=())
        log_thread.start()
        receiver_thread.start()
        sender_thread.start()
        while True:
            time_passed = time.time() - establish_time
            if time_passed > 30:
                done = True
                sender_thread.join()
                close(receiver_thread)
                break
    print("Connection Closed")

run()
