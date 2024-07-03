from radio import RadioModule
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class WardriverManager:
    def __init__(self):
        self.radio_modules: List[RadioModule] = []

    def load_radio_modules(self, configs: List[Dict[str, Any]]):
        for config in configs:
            module = self._create_module(config)
            if module:
                self.radio_modules.append(module)
                logger.info(f"Loaded radio module: {module.identifier}")

    def _create_module(self, config: Dict[str, Any]) -> Optional[RadioModule]:
        module_type = config.get('module_type')
        if module_type == 'cc2500':
            return RadioModule(config['identifier'], config)  # Placeholder, replace with actual class later
        elif module_type == 'cc2540':
            return RadioModule(config['identifier'], config)  # Placeholder, replace with actual class later
        elif module_type == 'cc1101':
            return RadioModule(config['identifier'], config)  # Placeholder, replace with actual class later
        else:
            logger.error(f"Unknown module type: {module_type}")
            return None

    def configure_module(self, identifier: str, mode: str, attack_type: str, target: Optional[Any] = None):
        module = self._find_module_by_id(identifier)
        if module:
            module.set_mode(mode, attack_type, target)

    def run_modules(self):
        for module in self.radio_modules:
            module.start()

    def _find_module_by_id(self, identifier: str) -> Optional[RadioModule]:
        for module in self.radio_modules:
            if module.identifier == identifier:
                return module
        logger.error(f"Radio module with identifier {identifier} not found")
        return None

    def scan_drivers(self) -> List[RadioModule]:
        # This method can be used to dynamically scan and load drivers, if needed
        return []
