class Router:
    def __init__(self, id):
        self.id = id
        self.link_state_database = []
        self.routing_table = []
        self.interfaces = []
        self.neighbors = []
        self.handshake_states = {}
        self.last_full_time = {}
        self.last_hello_time = {}

    def connect_to_neighbor(self, neighbor, link):
        if hasattr(neighbor, 'id'):
            if link is not None:
                self.interfaces.append(link)
            else:
                for interface in self.interfaces:
                    if hasattr(interface.a, 'id') and interface.a.id == self.id and hasattr(interface.b, 'id') and interface.b.id == neighbor.id:
                        link = interface
                    elif hasattr(interface.b, 'id') and interface.b.id == self.id and hasattr(interface.a, 'id') and interface.a.id == neighbor.id:
                        link = interface
            if ((self.id, neighbor.id, link) not in self.link_state_database) and ((neighbor.id, self.id, link) not in self.link_state_database):
                self.link_state_database.append((self.id, neighbor.id, link))
                self.link_state_database.append((neighbor.id, self.id, link))
                link_adds = ["ADD", (self.id, neighbor.id, link), (neighbor.id, self.id, link)]
                for interface in self.interfaces:
                    if interface != link:
                        if hasattr(interface.a, 'id') and interface.a.id == self.id and hasattr(interface.b, 'id'):
                            packet = Packet(self.id, interface.b.id, "lsa", link_adds)
                            interface.send(packet, self)
                        elif hasattr(interface.b, 'id') and interface.b.id == self.id and hasattr(interface.a, 'id'):
                            packet = Packet(self.id, interface.a.id, "lsa", link_adds)
                            interface.send(packet, self)
        else:
            self.link_state_database.append((self.id, neighbor.ip, link))
            self.link_state_database.append((neighbor.ip, self.id, link))
            link_adds = ["ADD", (self.id, neighbor.ip, link), (neighbor.ip, self.id, link)]
            for interface in self.interfaces:
                if interface != link:
                    if hasattr(interface.a, 'id') and interface.a.id == self.id and hasattr(interface.b, 'id'):
                        packet = Packet(self.id, interface.b.id, "lsa", link_adds)
                        interface.send(packet, self)
                    elif hasattr(interface.b, 'id') and interface.b.id == self.id and hasattr(interface.a, 'id'):
                        packet = Packet(self.id, interface.a.id, "lsa", link_adds)
                        interface.send(packet, self)

    def receive_and_send(self, packet, sender):
        if packet.type == "ping":
            if monitor:
                print("R" + str(self.id) + ": " + str(packet.type).upper() + "SENDER: " + ("R"+str(sender.id)) if hasattr(sender, 'id') else str(sender.ip) + " " + str(packet.text))
            destination = packet.receiver
            for rt in self.routing_table:
                dest_of_rt = rt[0]
                if dest_of_rt == destination:
                    link = rt[1]
                    print("R"+str(self.id), end=', ')
                    link.send(packet, self)
                    return
            print("R" + str(self.id), end=', ')
            print("unreachable")
            return
        elif packet.type == "hello":
            if str(sender.id) not in self.handshake_states.keys() or (self.handshake_states[sender.id] == "down" and str(sender.id) in self.last_full_time.keys()):
                if monitor:
                    string = ""
                    for i in range(len(packet.text)):
                        if i != 0:
                            string += ", " + str(packet.text[i].id)
                        else:
                            string = str(packet.text[i].id)
                    print("R" + str(self.id) + ": " + str(packet.type).upper()+ " SENDER: R" + str(sender.id) +" Neighbors: "+string)
                if sender not in self.neighbors:
                    self.connect_to_neighbor(sender, None)
                    self.neighbors.append(sender)
                packet = Packet(self.id, sender.id, "hello", self.neighbors)
                self.handshake_states[sender.id] = "init"
                sender.receive_and_send(packet, self)
            elif self.handshake_states[sender.id] == "down":
                if self in packet.text:
                    if monitor:
                        string = ""
                        for i in range(len(packet.text)):
                            if i != 0:
                                string += ", " + str(packet.text[i].id)
                            else:
                                string = str(packet.text[i].id)
                        print("R" + str(self.id) + ": " + str(packet.type).upper()+ " SENDER: R" + str(sender.id) +" Neighbors: "+string)
                    if sender not in self.neighbors:
                        self.connect_to_neighbor(sender, None)
                        self.neighbors.append(sender)
                    packet = Packet(self.id, sender.id, "hello", self.neighbors)
                    self.handshake_states[sender.id] = "2-way"
                    sender.receive_and_send(packet, self)
            elif self.handshake_states[sender.id] == "init":
                if self in packet.text:
                    if monitor:
                        string = ""
                        for i in range(len(packet.text)):
                            if i != 0:
                                string += ", " + str(packet.text[i].id)
                            else:
                                string = str(packet.text[i].id)
                        print("R" + str(self.id) + ": " + str(packet.type).upper()+ " SENDER: R" + str(sender.id) +" Neighbors: "+string)
                    self.handshake_states[sender.id] = "2-way"
                    packet = Packet(self.id, sender.id, "dbd", self.link_state_database)
                    sender.receive_and_send(packet, self)
            elif self.handshake_states[sender.id] == "full":
                if monitor:
                    string = ""
                    for i in range(len(packet.text)):
                        if i != 0:
                            string += ", " + str(packet.text[i].id)
                        else:
                            string = str(packet.text[i].id)
                    print("R" + str(self.id) + ": " + str(packet.type).upper() + " SENDER: R" + str(
                        sender.id) + " Neighbors: " + string)
                self.last_full_time[sender.id] = second
                # self.last_hello_time[sender.id] = second
        elif packet.type == "dbd":
            if self.handshake_states[sender.id] == "2-way":
                if monitor:
                    string = ""
                    for i in range(len(packet.text)):
                        if i != 0:
                            string += ", ("+packet.text[i][0]+","+packet.text[i][1]+") "
                        else:
                            string = "("+packet.text[i][0]+","+packet.text[i][1]+") "
                    print("R" + str(self.id) + ": " + str(packet.type).upper() + " SENDER: R" + str(sender.id) + " Table: " + string)
                for entry in packet.text:
                    if entry not in self.link_state_database:
                        self.link_state_database.append(entry)
                packet = Packet(self.id, sender.id, "dbd", self.link_state_database)
                self.handshake_states[sender.id] = "full"
                self.last_full_time[sender.id] = second
                self.last_hello_time[sender.id] = second
                sender.receive_and_send(packet, self)

        elif packet.type == "lsa":
            if packet.text[0] == "ADD":
                if monitor:
                    string = ""
                    for i in range(1, len(packet.text)):
                        if i != 1:
                            string += ", (" + packet.text[i][0] + "," + packet.text[i][1] + ") "
                        else:
                            string = "(" + packet.text[i][0] + "," + packet.text[i][1] + ") "
                    print("R" + str(self.id) + ": " + str(packet.type).upper() + " SENDER: R" + str(
                        sender.id) + " Adding Links: " + string)
                adds = packet.text[1:]
                change_in_my_db = False
                for link in adds:
                    if link not in self.link_state_database:
                        change_in_my_db = True
                        self.link_state_database.append(link)

                if change_in_my_db:
                    for n in self.neighbors:
                        if n.id != sender.id:
                            link = None
                            for link_db in self.link_state_database:
                                if (self.id == link_db[0] and n.id == link_db[1]) or (
                                        n.id == link_db[0] and self.id == link_db[1]):
                                    link = link_db[2]
                                    break
                            if link is not None:
                                packet = Packet(self.id, n.id, "lsa", packet.text)
                                link.send(packet, self)
            else:
                if monitor:
                    string = ""
                    for i in range(1, len(packet.text)):
                        if i != 1:
                            string += ", ("+packet.text[i][0]+","+packet.text[i][1]+") "
                        else:
                            string = "("+packet.text[i][0]+","+packet.text[i][1]+") "
                    print("R" + str(self.id) + ": " + str(packet.type).upper() + " SENDER: R" + str(sender.id) + " Removing Links: " + string)
                removes = packet.text[1:]
                change_in_my_db = False
                for link in removes:
                    if link in self.link_state_database:
                        change_in_my_db = True
                        self.link_state_database.remove(link)

                neighbor_removals = []
                if change_in_my_db:
                    for n in self.neighbors:
                        if n.id != sender.id:
                            link = None
                            for link_db in self.link_state_database:
                                if (self.id == link_db[0] and n.id == link_db[1]) or (n.id == link_db[0] and self.id == link_db[1]):
                                    link = link_db[2]
                                    break
                            if link is not None:
                                packet = Packet(self.id, n.id, "lsa", packet.text)
                                link.send(packet, self)
                            else:
                                neighbor_removals.append(n)
                    for n in neighbor_removals:
                        self.neighbors.remove(n)
                        self.handshake_states.pop(n.id, None)
                        # self.handshake_states[n.id] = "down"

    def start_handshaking(self, new_neighbor_router):
        self.handshake_states[new_neighbor_router.id] = "down"
        packet = Packet(self.id, new_neighbor_router.id, "hello", self.neighbors)
        new_neighbor_router.receive_and_send(packet, self)

    def step_forward(self):
        for interface in self.interfaces:
            if interface.a.id == self.id:
                if second - self.last_hello_time[interface.b.id] == 10:
                    packet = Packet(self.id, interface.b.id, "hello", self.neighbors)
                    self.last_hello_time[interface.b.id] = second
                    interface.send(packet, self)
            else:
                if second - self.last_hello_time[interface.a.id] == 10:
                    packet = Packet(self.id, interface.a.id, "hello", self.neighbors)
                    self.last_hello_time[interface.a.id] = second
                    interface.send(packet, self)

    def step_forward2(self):
        link_db_removes = []
        neighbor_removals = []
        for n in self.neighbors:
            if second - self.last_full_time[n.id] == 30:
                neighbor_removals.append(n)
                self.handshake_states.pop(n.id, None)
                # self.handshake_states[n.id] = "down"
                for link_db in self.link_state_database:
                    if (str(self.id) == str(link_db[0]) and str(n.id) == str(link_db[1])) or (
                            str(n.id) == str(link_db[0]) and str(self.id) == str(link_db[1])):
                        # print("WHAT??", self.id, str(link_db[0]), n.id, str(link_db[1]))
                        link_db_removes.append(link_db)
                    # elif str(n.id) == str(link_db[0]) and str(self.id) ==str(link_db[1]):
                    # print("WHAT??", self.id, str(link_db[0]), n.id, str(link_db[1]))
                    # link_db_removes.append(link_db)
        for link in link_db_removes:
            self.link_state_database.remove(link)
        for n in neighbor_removals:
            self.neighbors.remove(n)
        if len(link_db_removes) >= 1:
            link_db_removes.insert(0, "REMOVE")
            for n in self.neighbors:
                link = None
                for link_db in self.link_state_database:
                    if (self.id == link_db[0] and n.id == link_db[1]) or (n.id == link_db[0] and self.id == link_db[1]):
                        link = link_db[2]
                        break
                packet = Packet(self.id, n.id, "lsa", link_db_removes)
                link.send(packet, self)

    def dijkstra(self):
        N = [self.id]
        N_prime = [self.id]
        for link in self.link_state_database:
            if link[0] not in N:
                N.append(link[0])
            if link[1] not in N:
                N.append(link[1])
        d = {}
        next = {}
        for link in self.link_state_database:
            if self.id == link[0]:
                d[link[1]] = link[2].cost
                next[link[1]] = link[2]
        for node in N:
            if node not in N_prime and node not in d.keys():
                d[node] = float('inf')
                next[node] = None

        while len(N_prime) < len(N):
            minimum_cost = float('inf')
            for node in N:
                if node not in N_prime:
                    if d[node] < minimum_cost:
                        minimum_node = node
                        minimum_cost = d[node]
            for link in self.link_state_database:
                if minimum_node == link[0] and link[1] not in N_prime:
                    if d[link[1]] > d[minimum_node] + link[2].cost:
                        d[link[1]] = d[minimum_node] + link[2].cost
                        next[link[1]] = next[minimum_node]
            N_prime.append(minimum_node)

        self.routing_table = []
        for key in d.keys():
            if next[key] is not None:
                self.routing_table.append((key, next[key]))


class Link:
    def __init__(self, a, b, cost, state):
        self.a = a
        self.b = b
        self.cost = cost
        self.state = state

    def send(self, packet, sender):
        if self.state == "CONNECTED":
            if sender == self.b:
                self.a.receive_and_send(packet, self.b)
            else:
                self.b.receive_and_send(packet, self.a)
        elif self.state == "DISCONNECTED" and packet.type == 'ping':
            print("invalid")


class Client:
    def __init__(self, ip):
        self.ip = ip
        self.router = None
        self.link = None

    def connect_to_router(self, router, link):
        self.router = router
        self.link = link

    def send(self, packet):
        print(self.ip, end=', ')
        if self.link is None:
            print('invalid')
            return
        self.link.send(packet, self)

    def receive_and_send(self, packet, sender):
        if packet.receiver == self.ip:
            print(self.ip)


class Packet:
    def __init__(self, sender, receiver, type, text):
        self.sender = sender
        self.receiver = receiver
        self.type = type
        self.text = text


monitor = False
second = 0


def runner():
    global monitor, second
    registered_router_ids = []
    routers = []
    registered_client_ips = []
    clients = []
    links = []
    while True:
        seconds = 0
        command = list(input().split())
        if command[0] == "sec":
            seconds = int(command[1])
        elif command[0] == "add":
            if command[1] == "router":
                router_id = command[2]
                if router_id not in registered_router_ids:
                    registered_router_ids.append(router_id)
                    router = Router(router_id)
                    routers.append(router)
                else:
                    print("Error ID is not UNIQUE!")
            elif command[1] == "client":
                client_ip = command[2]
                if client_ip not in registered_client_ips:
                    registered_client_ips.append(client_ip)
                    client = Client(client_ip)
                    clients.append(client)
                else:
                    print("Error IP is not UNIQUE!")
        elif command[0] == "connect":
            cost = int(command[3])
            a, b = command[1], command[2]
            try:
                a = str(int(a))
                "a is a router but b can be a router or a client"
                for r in routers:
                    if r.id == a:
                        router_a = r
                        break
                try:
                    b = str(int(b))
                    "b is also a router"
                    for r in routers:
                        if r.id == b:
                            router_b = r
                            break
                    link = Link(router_a, router_b, cost, "CONNECTED")
                    router_a.connect_to_neighbor(router_b, link)
                    router_b.connect_to_neighbor(router_a, link)
                    links.append((router_a.id, router_b.id, link))
                    router_a.start_handshaking(router_b)
                except:
                    "b is a client"
                    for client in clients:
                        if client.ip == b:
                            client_b = client
                            break
                    link = Link(router_a, client_b, cost, "CONNECTED")
                    router_a.connect_to_neighbor(client_b, link)
                    client_b.connect_to_router(router_a, link)
                    links.append((router_a.id, client_b.ip, link))
            except:
                "a is not a router so b must be a router"
                for client in clients:
                    if client.ip == a:
                        client_a = client
                        break
                b = str(int(b))
                for r in routers:
                    if r.id == b:
                        router_b = r
                        break
                link = Link(router_b, client_a, cost, "CONNECTED")
                router_b.connect_to_neighbor(client_a, link)
                client_a.connect_to_router(router_b, link)
                links.append((router_b.id, client_a.ip, link))
        elif command[0] == "link":
            a, b = command[1], command[2]
            for link_tuple in links:
                if (str(a) == str(link_tuple[0]) and str(b) == str(link_tuple[1])) or (str(a) == str(link_tuple[1]) and str(b) == str(link_tuple[0])):
                    link = link_tuple[2]
            if command[3] == "d":
                link.state = "DISCONNECTED"
            elif command[3] == "e":
                link.state = "CONNECTED"
        elif command[0] == "ping":
            sender, receiver = command[1], command[2]
            packet = Packet(sender, receiver, "ping", "")
            for client in clients:
                if client.ip == sender:
                    client.send(packet)
                    break
        elif command[0] == "monitor":
            if command[1] == "d":
                monitor = False
            elif command[1] == "e":
                monitor = True

        for i in range(seconds):
            second += 1
            for router in routers:
                router.step_forward()
            for router in routers:
                router.step_forward2()

        for router in routers:
            router.dijkstra()


runner()
