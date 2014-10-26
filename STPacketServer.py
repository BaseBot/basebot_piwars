#!/usr/bin/python2
import SocketServer
import threading
import socket
import select
import Queue

from Packet import *

class STSession():
    def __init__(self, socket, address, sessionid):
        self.client_address = address
        self.sessionid = sessionid
        self.socket = socket
        self.socket.setblocking(0)
        self.tx_queue = Queue.Queue()
        self.tx_ctx = ''
        self.rx_ctx = ''
        self.rx_hdr = None

    def _dequeue(self):
        return self.tx_queue.get()

    def enqueue(self, packet):
        self.tx_queue.put(packet)

    def shutdown(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def has_tx_work(self):
        return bool(len(self.tx_ctx)) or not self.tx_queue.empty()

    def do_send(self):
        if not len(self.tx_ctx):
            self.tx_ctx = self._dequeue().pack()
        sent = self.socket.send(self.tx_ctx)
        if not sent:
            raise IOError
        self.tx_ctx = self.tx_ctx[sent:]

    def do_recv(self):
        if self.rx_hdr:
            # Receive body
            rx_size = self.rx_hdr.header.body_size - len(self.rx_ctx)
            rx_data = self.socket.recv(rx_size)
            if not rx_data:
                raise IOError
            self.rx_ctx = ''.join([self.rx_ctx, rx_data])
            if len(self.rx_ctx) == self.rx_hdr.header.body_size:
                self.rx_hdr.unpack_body(self.rx_ctx)
                packet = self.rx_hdr
                self.rx_hdr = None
                self.rx_ctx = ''
                return packet
        else:
            # Receive header
            rx_size = Packet.PacketHeader.size - len(self.rx_ctx)
            rx_data = self.socket.recv(rx_size)
            if not rx_data:
                raise IOError
            self.rx_ctx = ''.join([self.rx_ctx, rx_data])
            if len(self.rx_ctx) == Packet.PacketHeader.size:
                self.rx_hdr = Packet(self.rx_ctx)
                self.rx_ctx = ''
        return None

class STServer():
    def __init__(self, server_address = socket.gethostname(), port = 9001,\
            max_connections = 5):
        self.server_address = server_address
        self.port = port
        self.max_connections = max_connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,\
                1)
        self.server_socket.bind((server_address, port))
        self.server_socket.listen(max_connections + 1)
        self.cmd_socket = self._setup_cmd_socket()
        # Map of sockets to sessions, for fast socket->session lookups
        self.session_sockets = {}
        # Map of sessionids to sessions
        self.sessions = {}
        self.seed = 1
        self.rx_queue = Queue.Queue()
        print "New server at (%s:%d)" % (server_address, port)

    def _setup_cmd_socket(self):
        self.cmd_socket_client = socket.socket(socket.AF_INET, \
                socket.SOCK_STREAM)
        self.cmd_socket_client.connect((self.server_address, self.port))
        (sock, addr) = self.server_socket.accept()
        print "Opened cmd_socket at {}".format(addr)
        sock.setblocking(0)
        return sock

    def shutdown(self):
        for sesh in self.sessions.values():
            sesh.shutdown()
        self.sessions = {}
        self.session_sockets = {}
        self.cmd_socket_client.shutdown(socket.SHUT_RDWR)
        self.cmd_socket_client.close()
        self.cmd_socket.shutdown(socket.SHUT_RDWR)
        self.cmd_socket.close()
        self.server_socket.shutdown(socket.SHUT_RDWR)
        self.server_socket.close()

    def socket_to_session(self, socket):
        return self.session_sockets[socket]

    def new_sessionid(self):
        sessionid = self.seed
        self.seed = self.seed + 1
        return sessionid

    def send(self, (sessionid, packet)):
        if sessionid:
            self.sessions[sessionid].enqueue(packet)
        else:
            for sesh in self.sessions.values():
                sesh.enqueue(packet)
        sent = 0
        while not sent:
            sent = self.cmd_socket_client.send('!')

    def recv(self):
        return self.rx_queue.get()

    def have_packet(self):
        return not self.rx_queue.empty()

    def terminate_session(self, sesh):
        sesh.shutdown()
        self.session_sockets.pop(sesh.socket)
        self.sessions.pop(sesh.sessionid)

    def loop(self):
        while 1:
            # Find sockets we want to write to
            write_list = [sesh.socket\
                    for sesh in self.sessions.values()\
                    if sesh.has_tx_work()]

            # And sockets we want to read from
            read_list = [sesh.socket\
                    for sesh in self.sessions.values()]
            # If there's nothing to write, select on the command socket too
            if not len(write_list):
                read_list.append(self.cmd_socket)
            read_list.append(self.server_socket)

            # Watch for errors on the set of both
            full_list = list(set(write_list + read_list))

            to_read, to_write, error = select.select(read_list, write_list,\
                    full_list)

            if error:
                print "Got an error socket"
                raise IOError

            try:
                for w in to_write:
                    sesh = self.socket_to_session(w)
                    print "Send for session {}".format(sesh.sessionid)
                    sesh.do_send()

                for r in to_read:
                    print "Socket is ready to read!"
                    if r == self.server_socket:
                        (socket, addr) = self.server_socket.accept()
                        print "New connection from {}".format(addr)
                        sessionid = self.new_sessionid()
                        new_session = STSession(socket, addr, sessionid)
                        if (new_session):
                            print "New session: %s" % str(sessionid)
                            self.session_sockets[socket] = new_session
                            self.sessions[sessionid] = new_session
                        else:
                            print "Session creation failed"
                            socket.shutdown(socket.SHUT_RDWR)
                            socket.close()
                    elif r == self.cmd_socket:
                        data = r.recv(128)
                        if not data:
                            raise IOError
                        print "Got {} from cmd socket".format(data)
                    else:
                        sesh = self.socket_to_session(r)
                        print "Receive for session {}".format(sesh.sessionid)
                        packet = sesh.do_recv()
                        if packet:
                            print "Got {}".format(packet)
                            self.rx_queue.put((sesh.sessionid, packet))
            except IOError:
                print "Operation failed on session %s. Terminating." % \
                        str(sesh.sessionid)
                self.terminate_session(sesh)


