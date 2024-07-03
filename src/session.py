import logging
from typing import Dict, Any, Optional
from threading import Thread
from connection import Connection
from target import Target
from radio import RadioModule

logger = logging.getLogger(__name__)

class Session:
    def __init__(self):
        self.radio_module: Optional[RadioModule] = None
        self.connection: Optional[Connection] = None
        self.thread: Optional[Thread] = None
        self.running = False

    def set_radio_module(self, module: RadioModule):
        try:
            self.radio_module = module
            logger.info(f"Loaded radio module: {module.identifier}")
        except Exception as e:
            logger.error(f"Failed to set radio module: {e}")

    def set_connection(self, host: str, port: int):
        try:
            self.connection = Connection(host, port)
            logger.info(f"Initialized connection to {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to set connection: {e}")

    def start(self):
        if self.thread and self.thread.is_alive():
            logger.warning("Session is already running.")
            return

        self.running = True
        self.thread = Thread(target=self._run)
        self.thread.start()

    def _run(self):
        if self.connection:
            self.connection.open()
            logger.info(f"Opened connection to {self.connection.host}:{self.connection.port}")

        try:
            if self.radio_module:
                self.radio_module.start()
        finally:
            if self.connection:
                self.connection.close()
                logger.info(f"Closed connection to {self.connection.host}:{self.connection.port}")

    def stop(self):
        self.running = False
        if self.radio_module:
            self.radio_module.stop()

        if self.thread and self.thread.is_alive():
            self.thread.join()

    def set_mode(self, mode: str, attack_type: str, target: Optional[Target] = None):
        if not self.radio_module:
            logger.error("No radio module set")
            raise ValueError("Radio module must be set before setting mode")

        self.radio_module.set_mode(mode, attack_type, target)
        logger.info(f"Set mode {mode} with attack type {attack_type} on radio module {self.radio_module.identifier}")
