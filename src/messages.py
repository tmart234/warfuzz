from abc import ABC, abstractmethod
from scapy.packet import Packet
from scapy.all import raw
import logging

logger = logging.getLogger(__name__)

class Message(ABC):
    def __init__(self, packet: Packet):
        self.packet = packet

    @abstractmethod
    def to_raw(self) -> bytes:
        pass

    @abstractmethod
    def from_raw(self, data: bytes) -> Packet:
        pass

class ScapyMessage(Message):
    def to_raw(self) -> bytes:
        return raw(self.packet)

    def from_raw(self, data: bytes) -> Packet:
        self.packet = Packet(data)
        return self.packet
