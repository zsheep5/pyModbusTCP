import constants as const
import utils as mu
import socket
import struct
import settings
from threading import Lock, Thread

# for python2 compatibility
try:
    from socketserver import BaseRequestHandler, ThreadingTCPServer
except ImportError:
    from SocketServer import BaseRequestHandler, ThreadingTCPServer


class DataBank:
    """ Data class for thread safe access to bits and words space 
    words space is always kept in bytes  the reason for this every 
    vendor of PLC or other hardware store the data inconsistently 
    so a 16 bit register could have two 8bit ascii characters  with 
    10 registers strung to together to hold 20 char string then the 
    next register holding 16 bit float type the next register two 
    registers holder 32 bit integer. There is no way to tell what data 
    type is being sent so the code was refactored to 
    stop unpacking/converting from byte stream to integer.
    Several classmethods have been added to convert bytes to 
    a respective python data type  but you need to know the data type
    being stored in the register. 
    Need to write several more access and write methods to deal with
    signed integer, float and double types""" 

    bits_lock = Lock()
    bits = [False] * 0x10000
    words_lock = Lock()
    words = [struct.pack('>H', 0)] * 0x10000

    @classmethod
    def clear_registers(cls):
        with cls.words_lock:
            cls.word = [struct.pack('>H', 0)] * 0x10000
        with cls.bits_lock:
            cls.bits = [False] * 0x10000
        return True

    @classmethod
    def get_ascii(cls, pstart, pend):
        with cls.words_lock:
            if (pstart>=0 and pend<=65535) and (pend >=pstart):
                _ascii = b''.join(cls.words[pstart:pend]).decode('ascii')
                ##print(_ascii)
                return _ascii 
            else:
                return None

    @classmethod
    def get_bits(cls, address, number=1):
        with cls.bits_lock:
            if (address >= 0) and (address + number <= len(cls.bits)):
                return cls.bits[address: number + address]
            else:
                return None

    @classmethod
    def get_double(cls, pstart, pend):
        with cls.words_lock:
            if (pstart>=0 and pend<=65535) and (pstart+3 == pend):
                return struct.unpack('>d',cls.words[pstart:pend])[0]
            else:
                return None

    @classmethod
    def get_int2(cls, address):
        with cls.words_lock:
            if (address>=0 and address<=65535):
                return struct.unpack('>H',cls.words[address])[0]
            else:
                return None
    
    @classmethod
    def get_int4(cls, pstart ):
        with cls.words_lock:
            if (pstart>=0 and pstart+1<=65535):
                return struct.unpack('>I',cls.words[pstart:pstart+1])[0]
            else:
                return None

    @classmethod
    def get_float4(cls, pstart):
        with cls.words_lock:
            if (pstart>=0 and pstart+1<=65535):
                return struct.unpack('>f',cls.words[pstart:pstart+1])[0]
            else:
                return None
    
    @classmethod
    def get_words(cls, address, number=1):
        with cls.words_lock:
            if (address >= 0) and (address + number <= len(cls.words)):
                return cls.words[address: number + address]
            else:
                return None

    @classmethod 
    def set_ascii(cls, pstart, pend, pvalue):
        if (pstart>=0 and pend<=65535) and ( (pend-pstart) >= (len(pvalue)/2) ):
            _c_char = mu.ascii_to_char_bit(pvalue)
            if len(_c_char)> (pend-pstart):
                return False
            _i = pstart
            with cls.words_lock:
                for _char in _c_char:
                    cls.words[_i]= _char
                    _i = _i+1
                return True
        return False

    @classmethod
    def set_bits(cls, address, bit_list):
        with cls.bits_lock:
            if (address >= 0) and (address + len(bit_list) <= len(cls.bits)):
                cls.bits[address: address + len(bit_list)] = bit_list
                if settings.SERVER_PRINT_REGISTER_CHANGES:
                    print("Coil Address from %s to %s, boolean values: %s" 
                            % (address, len(bit_list)-1, 
                            ', '.join([str(i) for i in bit_list])
                            )
                    )
                return True
            else:
                return False

    @classmethod
    def set_clear_words(cls, pstart, pend):
        with cls.words_lock:
            if (pstart>=0 and pend<=65535) and (pstart <= pend):
                i = pstart
                while i <= pend :
                    cls.words[i] = 0
                    i = i + 1
                return True
            else:
                return False

    @classmethod
    def set_int2(cls, address, pvalue):
        with cls.words_lock:
            if (address>=0 and address<=65535 and pvalue <= 65535):
                cls.words[address] = struct.pack('>H', pvalue)
                return True
            else:
                return False
    
    @classmethod
    def set_int4(cls, pstart, pvalue):
        with cls.words_lock:
            if (pstart>=0 and pstart+1<=65535)  and (pvalue <= 4294967295):
                cls.words[pstart:pstart+1] = struct.pack('>I', pvalue )
                return True
            else:
                return False

    @classmethod
    def set_float4(cls, pstart,  pvalue):
        with cls.words_lock:
            if (pstart>=0 and pstart+1<=65535)  and isinstance(pvalue, float):
                cls.words[pstart:pstart+1] = struct.pack('>f',pvalue)
                return True
            else:
                return False
   
    @classmethod
    def set_words(cls, address, word_list):
        with cls.words_lock:
            #if (address >= 0) and (address + len(word_list) <= len(cls.words)):
            if (address>=0 and address<=65535):
                #ddcls.words[address: address + len(word_list)] = word_list
                cls.words[address]=word_list 
                if settings.SERVER_PRINT_REGISTER_CHANGES:
                    print(word_list)
                    try:
                        print("Address: %s value: %s" % (address, (b''.join(word_list)).decode('ascii')))
                    except :
                        print("Address: %s value: %s" % (address, struct.unpack('>H', word_list)))
                return True
            else:
                return False

class ModbusServer(object):

    """Modbus TCP server"""

    class ModbusService(BaseRequestHandler):
        
        bytes_to_read = 2 
        def recv_all(self, size):
            if hasattr(socket, "MSG_WAITALL"):
                data = self.request.recv(size, socket.MSG_WAITALL)
            else:
                # Windows lacks MSG_WAITALL
                data = b''
                while len(data) < size:
                    data += self.request.recv(size - len(data))
            return data

        def handle(self):
            while True:
                rx_head = self.recv_all(7)
                # close connection if no standard 7 bytes header
                if not (rx_head and len(rx_head) == 7):
                    break
                # decode header
                (rx_hd_tr_id, rx_hd_pr_id,
                 rx_hd_length, rx_hd_unit_id) = struct.unpack('>HHHB', rx_head)
                # close connection if frame header content inconsistency
                if not ((rx_hd_pr_id == 0) and (2 < rx_hd_length < 256)):
                    break
                # receive body
                rx_body = self.recv_all(rx_hd_length - 1)
                # close connection if lack of bytes in frame body
                if not (rx_body and (len(rx_body) == rx_hd_length - 1)):
                    break
                # body decode: function code
                rx_bd_fc = struct.unpack('B', rx_body[0:1])[0]
                # close connection if function code is inconsistent
                if rx_bd_fc > 0x7F:
                    break
                # default except status
                exp_status = const.EXP_NONE
                # functions Read Coils (0x01) or Read Discrete Inputs (0x02)
                if rx_bd_fc in (const.READ_COILS, const.READ_DISCRETE_INPUTS):
                    (b_address, b_count) = struct.unpack('>HH', rx_body[1:])
                    # check quantity of requested bits
                    if 0x0001 <= b_count <= 0x07D0:
                        bits_l = DataBank.get_bits(b_address, b_count)
                        if bits_l:
                            # allocate bytes list
                            b_size = int(b_count / 8)
                            b_size += 1 if (b_count % 8) else 0
                            bytes_l = [0] * b_size
                            # populate bytes list with data bank bits
                            for i, item in enumerate(bits_l):
                                if item:
                                    byte_i = int(i/8)
                                    bytes_l[byte_i] = mu.set_bit(bytes_l[byte_i], i % 8)
                            # format body of frame with bits
                            tx_body = struct.pack('BB', rx_bd_fc, len(bytes_l))
                            # add bytes with bits
                            for byte in bytes_l:
                                tx_body += struct.pack('B', byte)
                        else:
                            exp_status = const.EXP_DATA_ADDRESS
                    else:
                        exp_status = const.EXP_DATA_VALUE
                # functions Read Holding Registers (0x03) or Read Input Registers (0x04)
                elif rx_bd_fc in (const.READ_HOLDING_REGISTERS, const.READ_INPUT_REGISTERS):
                    (w_address, w_count) = struct.unpack('>HH', rx_body[1:])
                    # check quantity of requested words
                    if 0x0001 <= w_count <= 0x007D:
                        words_l = DataBank.get_words(w_address, w_count)
                        if words_l:
                            # format body of frame with words
                            tx_body = struct.pack('BB', rx_bd_fc, w_count * 2)
                            for word in words_l:
                                tx_body += word
                                #tx_body += struct.pack('>H', word)
                        else:
                            exp_status = const.EXP_DATA_ADDRESS
                    else:
                        exp_status = const.EXP_DATA_VALUE
                # function Write Single Coil (0x05)
                elif rx_bd_fc is const.WRITE_SINGLE_COIL:
                    (b_address, b_value) = struct.unpack('>HH', rx_body[1:])
                    f_b_value = bool(b_value == 0xFF00)
                    if DataBank.set_bits(b_address, [f_b_value]):
                        # send write ok frame
                        tx_body = struct.pack('>BHH', rx_bd_fc, b_address, b_value)
                    else:
                        exp_status = const.EXP_DATA_ADDRESS
                # function Write Single Register (0x06)
                elif rx_bd_fc is const.WRITE_SINGLE_REGISTER:
                    (w_address, w_value) = struct.unpack('>HH', rx_body[1:])
                    #w_address = struct.unpack('>H', rx_body[1:3])
                    #w_value = 
                    print(rx_body[3:5])
                    if DataBank.set_words(w_address, rx_body[3:5]):
                        # send write ok frame
                        #tx_body = struct.pack('>BHH', rx_bd_fc, w_address, w_value)
                        tx_body = struct.pack('>BH', rx_bd_fc, w_address ) + rx_body[3:5]
                    else:
                        exp_status = const.EXP_DATA_ADDRESS
                # function Write Multiple Coils (0x0F)
                elif rx_bd_fc is const.WRITE_MULTIPLE_COILS:
                    (b_address, b_count, byte_count) = struct.unpack('>HHB', rx_body[1:6])
                    # check quantity of updated coils
                    if (0x0001 <= b_count <= 0x07B0) and (byte_count >= (b_count/8)):
                        # allocate bits list
                        bits_l = [False] * b_count
                        # populate bits list with bits from rx frame
                        for i, item in enumerate(bits_l):
                            b_bit_pos = int(i/8)+6
                            b_bit_val = struct.unpack('B', rx_body[b_bit_pos:b_bit_pos+1])[0]
                            bits_l[i] = mu.test_bit(b_bit_val, i % 8)
                        # write words to data bank
                        if DataBank.set_bits(b_address, bits_l):
                            # send write ok frame
                            tx_body = struct.pack('>BHH', rx_bd_fc, b_address, b_count)
                        else:
                            exp_status = const.EXP_DATA_ADDRESS
                    else:
                        exp_status = const.EXP_DATA_VALUE
                # function Write Multiple Registers (0x10)
                elif rx_bd_fc is const.WRITE_MULTIPLE_REGISTERS:
                    (w_address, w_count, byte_count) = struct.unpack('>HHB', rx_body[1:6])
                    # check quantity of updated words
                    if (0x0001 <= w_count <= 0x007B) and (byte_count == w_count * 2):
                        # allocate words list
                        words_l = [0] * w_count
                        # populate words list with words from rx frame
                        for i, item in enumerate(words_l):
                            w_offset = i * 2 + 6
                            # words_l[i] = struct.unpack('>H', rx_body[w_offset:w_offset + 2])[0]
                            # write words to data bank
                            print(w_address)
                            print(rx_body[w_offset:w_offset + self.bytes_to_read])
                            if DataBank.set_words(w_address+i, rx_body[w_offset:w_offset + self.bytes_to_read]):
                            # send write ok frame
                                tx_body = struct.pack('>BHH', rx_bd_fc, w_address, w_count)
                            else:
                                exp_status = const.EXP_DATA_ADDRESS
                    else:
                        exp_status = const.EXP_DATA_VALUE
                else:
                    exp_status = const.EXP_ILLEGAL_FUNCTION
                # check exception
                if exp_status != const.EXP_NONE:
                    # format body of frame with exception status
                    tx_body = struct.pack('BB', rx_bd_fc + 0x80, exp_status)
                # build frame header
                tx_head = struct.pack('>HHHB', rx_hd_tr_id, rx_hd_pr_id, len(tx_body) + 1, rx_hd_unit_id)
                # send frame
                self.request.send(tx_head + tx_body)
            self.request.close()

    def __init__(self, host='localhost', port=const.MODBUS_PORT, no_block=False, ipv6=False, register_width=16):
        """Constructor
        Modbus server constructor.
        :param host: hostname or IPv4/IPv6 address server address (optional)
        :type host: str
        :param port: TCP port number (optional)
        :type port: int
        :param no_block: set no block mode, in this mode start() return (optional)
        :type no_block: bool
        :param ipv6: use ipv6 stack
        :type ipv6: bool
        :param register_width: how many bits the server expects for each word sent default 16 or 32 bit
        :type register_width: integer 
        """
        # public
        self.host = host
        self.port = port
        self.no_block = no_block
        self.ipv6 = ipv6
        self.register_width = register_width
        # private
        self._running = False
        self._service = None
        self._serve_th = None


    def start(self):
        """Start the server.
        Do nothing if server is already running.
        This function will block if no_block is not set to True.
        """
        if not self.is_run:
            # set class attribute
            ThreadingTCPServer.address_family = socket.AF_INET6 if self.ipv6 else socket.AF_INET
            ThreadingTCPServer.daemon_threads = True
            # init server
            self._service = ThreadingTCPServer((self.host, self.port), self.ModbusService, bind_and_activate=False)
            # set socket options
            self._service.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._service.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # TODO test no_delay with bench
            self._service.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            # bind and activate
            self._service.server_bind()
            self._service.server_activate()
            # serve request
            if self.no_block:
                self._serve_th = Thread(target=self._serve)
                self._serve_th.daemon = True
                self._serve_th.start()
            else:
                self._serve()

    def stop(self):
        """Stop the server.
        Do nothing if server is already not running.
        """
        if self.is_run:
            self._service.shutdown()
            self._service.server_close()

    @property
    def is_run(self):
        """Return True if server running.
        """
        return self._running

    def _serve(self):
        try:
            self._running = True
            self._service.serve_forever()
        except:
            self._service.server_close()
            raise
        finally:
            self._running = False