import logging
from typing import List, Dict, Any, Optional
from threading import Thread
from connection import Connection
from target import Target
from radio import RadioModule

logger = logging.getLogger(__name__)

class Session:
    def __init__(self):
        self.radio_modules: List[RadioModule] = []
        self.connections: List[Connection] = []
        self.running = False

    def add_radio_module(self, identifier: str, config: Dict[str, Any]):
        try:
            module = RadioModule(identifier, config)
            self.radio_modules.append(module)
            logger.info(f"Loaded radio module: {module.identifier}")
        except Exception as e:
            logger.error(f"Failed to add radio module: {e}")

    def add_connection(self, host: str, port: int):
        try:
            connection = Connection(host, port)
            self.connections.append(connection)
            logger.info(f"Initialized connection to {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to add connection: {e}")

    def start(self):
        self.running = True
        self.open_connections()
        threads = []
        for module in self.radio_modules:
            thread = Thread(target=module.start)
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()

    def stop(self):
        self.running = False
        for module in self.radio_modules:
            module.stop()
        self.close_connections()

    def open_connections(self):
        for connection in self.connections:
            connection.open()
            logger.info(f"Opened connection to {connection.host}:{connection.port}")

    def close_connections(self):
        for connection in self.connections:
            connection.close()
            logger.info(f"Closed connection to {connection.host}:{connection.port}")

    def set_mode(self, identifier: str, mode: str, attack_type: str, target: Optional[Target] = None):
        for module in self.radio_modules:
            if module.identifier == identifier:
                module.set_mode(mode, attack_type, target)
                return
        logger.error(f"Radio module with identifier {identifier} not found")
        raise ValueError("Invalid radio module identifier")
