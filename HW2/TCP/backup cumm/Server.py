import socket
import threading
import time
from pprint import pprint

import TCPHeader

states = ['CLOSED', 'LISTENING', 'SYN_RCVD', 'ESTABLISHED', 'FIN_WAIT1', 'CLOSE_WAIT', 'LAST_ACK']

main_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address_port = ('localhost', 10000)
main_server_socket.bind(server_address_port)
port = 10000


def new_port():
    global port
    port += 1
    return port


def main_receiver():
    global main_server_socket
    while True:
        data, address = main_server_socket.recvfrom(20)
        data = TCPHeader.make_tcp_from_bytes(data)
        if data.synFlag:
            print("Received in main receiver", data)
            thread = threading.Thread(target=client_receiver, args=(data, address))
            thread.start()


def send_ack(server_socket, data, last_sent_ack, client_port, server_port, initial_sequence_number, address, ack_to_send):
    # if data.sequenceNumber == last_sent_ack + 1:
    #     ack_to_send = data.sequenceNumber + 1
    #     packet = TCPHeader.TCPHeader(client_port, server_port, initial_sequence_number, ack_to_send, 1, 0, 0,
    #                                  1000).get()
    #     server_socket.sendto(packet, address)
    #     last_sent_ack += 1
    # else:
    #     ack_to_send = last_sent_ack + 1
    #     packet = TCPHeader.TCPHeader(client_port, server_port, initial_sequence_number, ack_to_send, 1, 0, 0,
    #                                  1000).get()
    #     server_socket.sendto(packet, address)

    packet = TCPHeader.TCPHeader(client_port, server_port, initial_sequence_number, data.sequenceNumber+1, 1, 0, 0, 1000).get()
    server_socket.sendto(packet, address)

    return ack_to_send, last_sent_ack


def client_receiver(data, address):
    pprint(vars(data))
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_port = new_port()
    server_new_address_port = ('localhost', server_port)
    server_socket.bind(server_new_address_port)
    state = states[1]
    last_sent_ack = None
    client_port = address[1]
    initial_sequence_number = 0
    ack_to_send = data.sequenceNumber+1
    packet = TCPHeader.TCPHeader(client_port, server_port, initial_sequence_number, ack_to_send, 1, 1, 0, 1000).get()
    server_socket.sendto(packet, address)
    last_sent_ack = ack_to_send-1
    state = states[2]
    tmp = 2
    while state == states[2]:
        data, address = server_socket.recvfrom(20)
        data = TCPHeader.make_tcp_from_bytes(data)
        if data.ackFlag and data.ackNumber == initial_sequence_number+1:
            state = states[3]
            ack_to_send, last_sent_ack = send_ack(server_socket, data, last_sent_ack, client_port, server_port, initial_sequence_number, address, ack_to_send)
    fin_time = 0
    print("Y")
    # tmp = 2
    while state == states[3] or (state == states[4] and time.time() - fin_time < 1):
        # print(state, fin_time, time.time())
        # print("Z")
        data, address = server_socket.recvfrom(20)
        # print("P")
        data = TCPHeader.make_tcp_from_bytes(data)
        # if tmp == 1:
        #     pprint(vars(data))
        # if data.finFlag and tmp > 0:
        #     print("HOOOOOOOOOY", tmp)
        #     print("aCKK tO sEnD", ack_to_send)
        #     tmp -= 1
        #     continue
        ack_to_send, last_sent_ack = send_ack(server_socket, data, last_sent_ack, client_port, server_port, initial_sequence_number, address, ack_to_send)
        if data.finFlag and state != states[4]:
            # print("W")
            state = states[4]
            fin_time = time.time()

    print("X")
    tmp = 2
    state = states[5]
    initial_sequence_number += 1
    packet = TCPHeader.TCPHeader(client_port, server_port, initial_sequence_number, ack_to_send, 0, 0, 1, 1000).get()
    server_socket.sendto(packet, address)
    print(initial_sequence_number+1)
    while state == states[5]:
        data, address = server_socket.recvfrom(20)
        data = TCPHeader.make_tcp_from_bytes(data)
        print("S")
        if data.ackFlag and data.ackNumber == initial_sequence_number+1:
            if tmp > 2:
                tmp -= 1
                continue
            state = states[6]
            print("Done")


main_receiver()