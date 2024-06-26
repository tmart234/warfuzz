from radioModule import RadioModule
import logging 
from typing import List, Dict, Any, Optional


logger = logging.getLogger(__name__)

class WardriverManager:
    def __init__(self):
        self.radio_modules: List[RadioModule] = []

    def load_radio_modules(self, configs: List[Dict[str, Any]]):
        for config in configs:
            module = RadioModule(config['identifier'], config)
            self.radio_modules.append(module)
            logger.info(f"Loaded radio module: {module.identifier}")

    def configure_module(self, identifier: str, mode: str, attack_type: str, target: Optional[Any] = None):
        module = self._find_module_by_id(identifier)
        if module:
            module.set_mode(mode, attack_type, target)

    def run_modules(self):
        for module in self.radio_modules:
            module.run()

    def _find_module_by_id(self, identifier: str) -> RadioModule:
        for module in self.radio_modules:
            if module.identifier == identifier:
                return module
        logger.error(f"Radio module with identifier {identifier} not found")
        return None