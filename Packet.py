import struct
import Queue

class Packet:
    class PacketHeader:
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
            format_str = '!ii'
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
			return "Left: %i, Right: %i" % (self.left, self.right)

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

