from abc import abstractmethod
import logging
from target import Target
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def update_global_metrics(time: str, packets_sent: int, connected_to_target: bool):
    global metrics
    metrics['time'] = time
    metrics['packets_sent'] = packets_sent
    metrics['connected_to_target'] = connected_to_target

class RadioModule:
    def __init__(self, identifier: str, config: Dict[str, Any]):
        self.identifier = identifier
        self.config = config
        self.mode = None
        self.attack_type = None
        self.current_target = None # pointer to current target object
        self.packets_sent = 0
        self.packet_count = config.get('packet_count', 10)  # Default to 10 if not specified
        self.targets: List[Target] = []  # List to hold Target objects
        self.baud = config.get('baud', None)
        self.comport = config.get('com', None)

    @abstractmethod
    def scan_for_devices(self) -> List[Target]:
        pass

    def set_mode(self, mode: str, attack_type: str, target: Optional[Any] = None):
        if mode not in ['fuzzing', 'jamming']:
            logger.error(f"Invalid mode: {mode}")
            raise ValueError("Mode must be 'fuzzing' or 'jamming'")
        if attack_type not in ['targeted', 'selected', 'indiscriminate']:
            logger.error(f"Invalid attack type: {attack_type}")
            raise ValueError("Attack type must be 'targeted', 'selected', or 'indiscriminate'")
        
        self.mode = mode
        self.attack_type = attack_type
        self.target = target
        logger.info(f"Radio module {self.identifier} set to {self.mode} mode with {self.attack_type} attack")

    def run(self):
        if self.mode is None or self.attack_type is None:
            logger.error("Mode and attack type must be set before running")
            raise RuntimeError("Mode and attack type must be set before running")
        
        logger.info(f"Running {self.mode} mode with {self.attack_type} attack on module {self.identifier}")
        if self.attack_type == 'targeted':
            self._run_targeted_attack()
        elif self.attack_type == 'selected':
            self._run_selected_attack()
        elif self.attack_type == 'indiscriminate':
            self._run_indiscriminate_attack()

        # Update global metrics after running the attack
        self._update_metrics()

    def _update_metrics(self):
        update_global_metrics("00:01:00", self.packets_sent, self.target is not None)


    def _run_targeted_attack(self):
        if self.target is None:
            logger.error("Target must be provided for targeted attack")
            raise ValueError("Target must be provided for targeted attack")
        logger.info(f"Executing targeted attack on {self.target} with module {self.identifier}")
        self.packets_sent += self.packet_count  # Use the packet count from the configuration
        logger.info(f"Sent {self.packet_count} packets to {self.target}")

    def _run_selected_attack(self):
        logger.info(f"Scanning for devices with module {self.identifier} for selected attack")
        devices = self.scan_for_devices()
        selected_target = self._user_select_target(devices)
        self.target = selected_target
        logger.info(f"Executing selected attack on {self.target} with module {self.identifier}")
        self.packets_sent += self.packet_count  # Use the packet count from the configuration
        logger.info(f"Sent {self.packet_count} packets to {self.target}")

    def _run_indiscriminate_attack(self):
        logger.info(f"Scanning for nearest/highest RSSI device with module {self.identifier} for indiscriminate attack")
        best_target = self._scan_for_nearest_or_highest_rssi_device()
        self.target = best_target
        logger.info(f"Executing indiscriminate attack on {self.target} with module {self.identifier}")
        self.packets_sent += self.packet_count  # Use the packet count from the configuration
        logger.info(f"Sent {self.packet_count} packets to {self.target}")
  
    def _scan_for_devices(self) -> List[Any]:
        # Simulated scanning implementation
        logger.info(f"Scanning for devices with module {self.identifier}")
        return ['device1', 'device2', 'device3']

    def _user_select_target(self, devices: List[Target]) -> Target:
        # This method will be called from the frontend
        return devices[0] if devices else None

    def _scan_for_nearest_or_highest_rssi_device(self) -> Target:
        logger.info(f"Scanning for nearest or highest RSSI device with module {self.identifier}")
        devices = self.scan_for_devices()
        # Return the device with the highest RSSI (highest RSSI is the least negative value)
        best_target = max(devices, key=lambda t: t.rssi)
        logger.info(f"Best target based on RSSI: {best_target}")
        return best_target