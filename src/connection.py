import serial
import socket
import logging
from typing import Union
from message import Message

logger = logging.getLogger(__name__)

class Connection:
    def __init__(self, host: str = None, port: int = None, comport: str = None, baudrate: int = 9600):
        self.host = host
        self.port = port
        self.comport = comport
        self.baudrate = baudrate
        self.serial_conn = None
        self.socket_conn = None

    def open(self):
        if self.comport:
            self.serial_conn = serial.Serial(self.comport, self.baudrate, timeout=1)
            logger.info(f"Opened serial connection on {self.comport}")
        elif self.host and self.port:
            self.socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_conn.connect((self.host, self.port))
            logger.info(f"Opened socket connection to {self.host}:{self.port}")

    def close(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            logger.info(f"Closed serial connection on {self.comport}")
        elif self.socket_conn:
            self.socket_conn.close()
            logger.info(f"Closed socket connection to {self.host}:{self.port}")

    def send(self, message: Message):
        data = message.to_raw()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(data)
            logger.info(f"Sent data over serial: {data}")
        elif self.socket_conn:
            self.socket_conn.sendall(data)
            logger.info(f"Sent data over socket: {data}")

    def recv(self, buffer_size: int = 1024) -> bytes:
        if self.serial_conn and self.serial_conn.is_open:
            data = self.serial_conn.read(buffer_size)
            logger.info(f"Received data over serial: {data}")
            return data
        elif self.socket_conn:
            data = self.socket_conn.recv(buffer_size)
            logger.info(f"Received data over socket: {data}")
            return data
        return b''
