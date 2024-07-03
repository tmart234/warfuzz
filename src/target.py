import time
import warnings
import logging

logger = logging.getLogger(__name__)

class Target:
    def __init__(self, name: str, rssi: int, baud_rate: int, com_port: str):
        self.name = name
        self.rssi = rssi
        self.baud_rate = baud_rate
        self.com_port = com_port
        self.connection = None
        self.monitors = []
        self.monitor_alive = []
        self.max_recv_bytes = 10000
        self._fuzz_data_logger = None

    def __repr__(self):
        return f"Target(name={self.name}, rssi={self.rssi}, baud_rate={self.baud_rate}, com_port={self.com_port})"

    def add_monitor(self, monitor):
        """Add a monitor to the target."""
        self.monitors.append(monitor)

    def set_fuzz_data_logger(self, fuzz_data_logger):
        """Set the fuzz data logger for sent and received data."""
        self._fuzz_data_logger = fuzz_data_logger

    def open(self):
        """Open the connection to the target."""
        logger.info(f"Opening connection to target {self.name}...")
        if self._fuzz_data_logger:
            self._fuzz_data_logger.log_info(f"Opening connection to target {self.name}...")
        # Simulate opening the connection (implementation-specific)
        self.connection = True  # Replace with actual connection logic
        logger.info(f"Connection to target {self.name} opened.")
        if self._fuzz_data_logger:
            self._fuzz_data_logger.log_info(f"Connection to target {self.name} opened.")

    def close(self):
        """Close the connection to the target."""
        logger.info(f"Closing connection to target {self.name}...")
        if self._fuzz_data_logger:
            self._fuzz_data_logger.log_info(f"Closing connection to target {self.name}...")
        # Simulate closing the connection (implementation-specific)
        self.connection = None  # Replace with actual disconnection logic
        logger.info(f"Connection to target {self.name} closed.")
        if self._fuzz_data_logger:
            self._fuzz_data_logger.log_info(f"Connection to target {self.name} closed.")

    def send(self, data):
        """Send data to the target."""
        if not self.connection:
            raise ConnectionError(f"Target {self.name} is not connected.")
        logger.info(f"Sending data to target {self.name}: {data}")
        if self._fuzz_data_logger:
            self._fuzz_data_logger.log_info(f"Sending data to target {self.name}: {data}")
        # Simulate sending data (implementation-specific)
        # Replace with actual send logic
        logger.info(f"Data sent to target {self.name}.")
        if self._fuzz_data_logger:
            self._fuzz_data_logger.log_send(data)

    def recv(self, max_bytes=None):
        """Receive data from the target."""
        if not self.connection:
            raise ConnectionError(f"Target {self.name} is not connected.")
        if max_bytes is None:
            max_bytes = self.max_recv_bytes
        logger.info(f"Receiving data from target {self.name} (max {max_bytes} bytes)...")
        if self._fuzz_data_logger:
            self._fuzz_data_logger.log_info(f"Receiving data from target {self.name} (max {max_bytes} bytes)...")
        # Simulate receiving data (implementation-specific)
        data = "data received"  # Replace with actual receive logic
        logger.info(f"Received data from target {self.name}: {data}")
        if self._fuzz_data_logger:
            self._fuzz_data_logger.log_recv(data)
        return data

    def monitors_alive(self):
        """Wait for monitors to become alive and establish a connection."""
        for monitor in self.monitors:
            while not monitor.alive():
                time.sleep(1)
            for cb in self.monitor_alive:
                cb(monitor)
