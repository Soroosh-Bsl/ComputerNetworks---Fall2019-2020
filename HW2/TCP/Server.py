from __future__ import print_function
import socket
import threading
import time
from pprint import pprint

import TCPHeader

states = ['CLOSED', 'LISTENING', 'SYN_RCVD', 'ESTABLISHED', 'FIN_WAIT1', 'CLOSE_WAIT', 'LAST_ACK']

main_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address_port = ('', 47749)
main_server_socket.bind(server_address_port)
port = 47749


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
            test_file = open('test.txt', 'w+')
            thread = threading.Thread(target=client_receiver, args=(data, address))
            thread.start()


def send_ack(server_socket, data, last_sent_ack, client_port, server_port, initial_sequence_number, address, ack_to_send):
    if data.sequenceNumber == last_sent_ack + 1:
        ack_to_send = data.sequenceNumber + 1
        packet = TCPHeader.TCPHeader(client_port, server_port, initial_sequence_number, ack_to_send, 1, 0, 0,
                                     1000).get()
        # print("Sent ack {}".format(ack_to_send))
        server_socket.sendto(packet, address)
        last_sent_ack += 1
    else:
        ack_to_send = last_sent_ack + 1
        packet = TCPHeader.TCPHeader(client_port, server_port, initial_sequence_number, ack_to_send, 1, 0, 0,
                                     1000).get()
        server_socket.sendto(packet, address)
    return ack_to_send, last_sent_ack


def client_receiver(data, address):
    server_log = open('server_log.txt', 'w+')
    print("Client {} Connected".format(address[1]))
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
    while state == states[2]:
        data, address = server_socket.recvfrom(20)
        data = TCPHeader.make_tcp_from_bytes(data)
        if data.ackFlag and data.ackNumber == initial_sequence_number+1:
            state = states[3]
            ack_to_send, last_sent_ack = send_ack(server_socket, data, last_sent_ack, client_port, server_port, initial_sequence_number, address, ack_to_send)
    while state == states[3]:
        data, address = server_socket.recvfrom(20)
        data = TCPHeader.make_tcp_from_bytes(data)
        print("Packet {} Received".format(data.sequenceNumber), file=server_log)
        ack_to_send, last_sent_ack = send_ack(server_socket, data, last_sent_ack, client_port, server_port, initial_sequence_number, address, ack_to_send)
        if data.finFlag:
            state = states[4]
    print("Connection Closed")

main_receiver()