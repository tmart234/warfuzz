from abc import ABC, abstractmethod
from threading import Thread
import logging
from target import Target
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def update_global_metrics(time: str, packets_sent: int, connected_to_target: bool):
    global metrics
    metrics['time'] = time
    metrics['packets_sent'] = packets_sent
    metrics['connected_to_target'] = connected_to_target

class RadioModule(ABC):
    def __init__(self, identifier: str, config: Dict[str, Any]):
        self.identifier = identifier
        self.config = config
        self.mode = None
        self.attack_type = None
        self.targets: List[Target] = []
        self.packets_sent = 0
        self.packet_count = config.get('packet_count', 10)
        self.baud = config.get('baud', None)
        self.comport = config.get('com', None)

    @abstractmethod
    def scan_for_devices(self) -> List[Target]:
        pass

    def set_mode(self, mode: str, attack_type: str, targets: Optional[List[Target]] = None):
        if mode not in ['fuzzing', 'jamming']:
            logger.error(f"Invalid mode: {mode}")
            raise ValueError("Mode must be 'fuzzing' or 'jamming'")
        if attack_type not in ['targeted', 'selected', 'indiscriminate']:
            logger.error(f"Invalid attack type: {attack_type}")
            raise ValueError("Attack type must be 'targeted', 'selected', or 'indiscriminate'")
        
        self.mode = mode
        self.attack_type = attack_type
        self.targets = targets or []
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

        self._update_metrics()

    def _update_metrics(self):
        update_global_metrics("00:01:00", self.packets_sent, bool(self.targets))

    def _run_targeted_attack(self):
        if not self.targets:
            logger.error("Targets must be provided for targeted attack")
            raise ValueError("Targets must be provided for targeted attack")
        for target in self.targets:
            logger.info(f"Executing targeted attack on {target} with module {self.identifier}")
            self.packets_sent += self.packet_count
            logger.info(f"Sent {self.packet_count} packets to {target}")

    def _run_selected_attack(self):
        logger.info(f"Scanning for devices with module {self.identifier} for selected attack")
        devices = self.scan_for_devices()
        selected_target = self._user_select_target(devices)
        if selected_target:
            self.targets = [selected_target]
            logger.info(f"Executing selected attack on {selected_target} with module {self.identifier}")
            self.packets_sent += self.packet_count
            logger.info(f"Sent {self.packet_count} packets to {selected_target}")

    def _run_indiscriminate_attack(self):
        logger.info(f"Scanning for nearest/highest RSSI device with module {self.identifier} for indiscriminate attack")
        best_target = self._scan_for_nearest_or_highest_rssi_device()
        if best_target:
            self.targets = [best_target]
            logger.info(f"Executing indiscriminate attack on {best_target} with module {self.identifier}")
            self.packets_sent += self.packet_count
            logger.info(f"Sent {self.packet_count} packets to {best_target}")

    def _scan_for_devices(self) -> List[Target]:
        logger.info(f"Scanning for devices with module {self.identifier}")
        return []

    def _user_select_target(self, devices: List[Target]) -> Target:
        logger.info(f"User selecting target from devices: {devices}")
        return devices[0] if devices else None

    def _scan_for_nearest_or_highest_rssi_device(self) -> Target:
        logger.info(f"Scanning for nearest or highest RSSI device with module {self.identifier}")
        devices = self.scan_for_devices()
        return max(devices, key=lambda t: t.rssi) if devices else None

    def start(self):
        thread = Thread(target=self.run)
        thread.start()
