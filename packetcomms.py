# Packet-based communications module
# Copyright Brian Starkey <stark3y@gmail.com> 2014

"""
This module provides classes to facilitate socket-based communication using
'packets'. The packets are simply data structures which are packed and
unpacked using the struct module
"""

import logging
import Queue
import select
import socket
import struct

class Packet:
    """
    Base class for packets

    A packet can be instantiated by providing a string representing the
    packet header. unpack_body() can then be called to generate a specialised
    packet instance determined by the type data in the header
    """
    class PacketHeader:
        """
        Packet header class

        The packet header has a fixed size, and is used to determine the type
        of a packet, and the total size of it. A PacketHeader should only be
        directly instantiated by subclasses of Packet. The Packet constructor
        should be used in all other cases.
        """
        struct = struct.Struct("!4sI")
        size = struct.size

        def __init__(self, type = 'none', size = 0, header_data = None):
            if header_data:
                self.packet_type, self.body_size = \
                        Packet.PacketHeader.struct.unpack(header_data)
            else:
                self.packet_type = type
                self.body_size = size

        def pack(self):
            return Packet.PacketHeader.struct.pack(self.packet_type, \
                    self.body_size)

    class PacketBody:
        def size(self):
            raise NotImplementedError

        def pack(self):
            raise NotImplementedError

        def unpack(self):
            raise NotImplementedError

        def __str__(self):
            raise NotImplementedError

    def __init__(self, header_data):
        self.header = Packet.PacketHeader(header_data = header_data)

    def unpack_body(self, body_data):
        global packet_types
        if not packet_types.has_key(self.type()):
            raise KeyError
        self.body = packet_types[self.header.packet_type].Body()
        self.body.unpack(body_data)

    def pack_body(self):
        return self.body.pack()

    def pack(self):
        body = self.body.pack()
        self.header.body_size = len(body)
        return ''.join([ self.header.pack(), body ])

    def type(self):
        return self.header.packet_type

    def __str__(self):
        return "Type: %s\ndata: %s" % (self.header.packet_type, \
                str(self.body))

class TextPacket(Packet):
    """
    A simple text packet class

    This type of packet contains a single string as its data
    """
    class Body(Packet.PacketBody):
        def __init__(self, data = ''):
            self.data = data

        def size(self):
            return len(self.data)

        def pack(self):
            return struct.pack('!%ds' % len(self.data), self.data)

        def unpack(self, data):
            self.data = data

        def __str__(self):
            return "'%s'" % self.data

    def __init__(self, text):
        self.body = TextPacket.Body(text)
        self.header = Packet.PacketHeader('text', self.body.size())

class EchoPacket(TextPacket):
    def __init__(self, text):
        self.body = EchoPacket.Body(text)
        self.header = Packet.PacketHeader('echo', self.body.size())

class SpamPacket(TextPacket):
    def __init__(self, text):
        self.body = SpamPacket.Body(text)
        self.header = Packet.PacketHeader('spam', self.body.size())

class ListPacket(Packet):
    """
    Base class for general list-type packets

    List packets can be used for lists of a single data type
    """
    type_str = 'ilst'
    class Body:
        format_char = 'i'
        def __init__(self, vals = []):
            format_str = '!I%d%c' % (len(vals), self.format_char)
            self.struct = struct.Struct(format_str)
            self.vals = vals

        def size(self):
            return self.struct.size

        def pack(self):
            return self.struct.pack(len(self.vals), *self.vals)

        def unpack(self, data):
            n = struct.unpack('!I', data[:struct.calcsize('!I')])[0]
            items = struct.unpack('!%d%c' % (n, self.format_char),\
                    data[struct.calcsize('!I'):])
            self.vals = [v for v in items]
            format_str = '!I%d%c' % (len(self.vals), self.format_char)
            self.struct = struct.Struct(format_str)

        def __str__(self):
            return str(self.vals)

    def __init__(self, vals = []):
        self.body = self.Body(vals)
        self.header = Packet.PacketHeader(self.type_str, self.body.size())

class IntListPacket(ListPacket):
    pass

class UintListPacket(ListPacket):
    type_str = 'ulst'
    class Body(ListPacket.Body):
        format_char = 'I'

class FloatListPacket(ListPacket):
    type_str = 'flst'
    class Body(ListPacket.Body):
        format_char = 'f'

class DblListPacket(ListPacket):
    type_str = 'dlst'
    class Body(ListPacket.Body):
        format_char = 'd'

class TelecommandPacket(Packet):
    class Body:
        def __init__(self, left = 0, right = 0):
            format_str = '!ff'
            self.struct = struct.Struct(format_str)
            self.left = left
            self.right = right

        def size(self):
            return self.struct.size

        def pack(self):
            return self.struct.pack(self.left, self.right)

        def unpack(self, data):
			self.left, self.right = self.struct.unpack(data)

        def __str__(self):
			return "Left: %f, Right: %f" % (self.left, self.right)

    def __init__(self, left = 0, right = 0):
        self.body = self.Body(left, right)
        self.header = Packet.PacketHeader('tcmd', self.body.size())

packet_types = {
 'text': TextPacket,
 'echo': EchoPacket,
 'spam': SpamPacket,
 'ilst': IntListPacket,
 'ulst': UintListPacket,
 'flst': FloatListPacket,
 'dlst': DblListPacket,
 'tcmd': TelecommandPacket,
}

class Session():
    """
    Session class for the Server

    This keeps track of a particular client connection. The server-side
    application should not intantiate this directly.

    It may be desireable to instantiate this in a client application to get
    access to the send/receive methods. In this case, the sessionids need to
    be managed by the application
    """
    def __init__(self, socket, address, sessionid):
        tag = '%s' % str(sessionid)
        self.logger = logging.getLogger('%s.%s' % \
                (self.__class__.__name__, tag))
        self.client_address = address
        self.sessionid = sessionid
        self.socket = socket
        self.socket.setblocking(0)
        self.tx_queue = Queue.Queue()
        self.tx_ctx = ''
        self.rx_ctx = ''
        self.rx_hdr = None
        self.logger.debug("New session '%s', from %s", str(sessionid), address)

    def _dequeue(self):
        return self.tx_queue.get()

    def enqueue(self, packet):
        self.tx_queue.put(packet)

    def shutdown(self):
        self.logger.info("Shutdown")
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
                self.logger.debug("Received:\n%s", str(packet))
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

class Server():
    """
    A Server class for sending and receiving packets

    This class does session management and send/receive operations with client
    Sessions. A thread should be spawned for the loop function, which will
    handle connections forever
    """
    def __init__(self, server_address = socket.gethostname(), port = 9001,\
            max_connections = 5):
        tag = "%s:%i" % (server_address, port)
        self.logger = logging.getLogger('%s.%s' % \
                (self.__class__.__name__, tag))
        self.logger.info("New server at (%s:%d)", server_address, port)
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

    def _setup_cmd_socket(self):
        self.cmd_socket_client = socket.socket(socket.AF_INET, \
                socket.SOCK_STREAM)
        self.cmd_socket_client.connect((self.server_address, self.port))
        (sock, addr) = self.server_socket.accept()
        self.logger.debug("Opened cmd_socket at %s", str(addr))
        sock.setblocking(0)
        return sock

    def shutdown(self):
        self.logger.info("Shutting down")
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
        self.logger.info("Done.")

    def socket_to_session(self, socket):
        return self.session_sockets[socket]

    def new_sessionid(self):
        sessionid = self.seed
        self.seed = self.seed + 1
        self.logger.debug("Generated new sessionid: %s",
                str(sessionid))
        return sessionid

    def send(self, (sessionid, packet)):
        if sessionid:
            self.logger.debug("Send '%s' packet to session '%s'",
                    packet.type(), str(sessionid))
            self.sessions[sessionid].enqueue(packet)
        else:
            self.logger.debug("Broadcast send '%s' packet", packet.type())
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
        self.logger.info("Terminating session '%s'", str(sesh.sessionid))
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
                self.logger.error("Got an error socket")
                raise IOError

            try:
                for w in to_write:
                    sesh = self.socket_to_session(w)
                    self.logger.debug("Send for session '%s'",
                            str(sesh.sessionid))
                    sesh.do_send()

                for r in to_read:
                    if r == self.server_socket:
                        (socket, addr) = self.server_socket.accept()
                        self.logger.info("New connection from '%s'", str(addr))
                        sessionid = self.new_sessionid()
                        new_session = Session(socket, addr, sessionid)
                        if (new_session):
                            self.logger.debug("New session: '%s'",
                                    str(sessionid))
                            self.session_sockets[socket] = new_session
                            self.sessions[sessionid] = new_session
                        else:
                            self.logger.error("Session creation failed")
                            socket.shutdown(socket.SHUT_RDWR)
                            socket.close()
                    elif r == self.cmd_socket:
                        data = r.recv(128)
                        if not data:
                            raise IOError
                        self.logger.debug("Got '%s' from cmd socket", str(data))
                    else:
                        sesh = self.socket_to_session(r)
                        self.logger.debug("Receive on session '%s'",
                                str(sesh.sessionid))
                        packet = sesh.do_recv()
                        if packet:
                            self.rx_queue.put((sesh.sessionid, packet))
            except IOError:
                self.logger.error("Operation failed on session '%s'",
                        str(sesh.sessionid))
                self.terminate_session(sesh)


