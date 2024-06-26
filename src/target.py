
class Target:
    def __init__(self, identifier: str, rssi: int):
        self.identifier = identifier
        self.rssi = rssi

    def __repr__(self):
        return f"Target(identifier={self.identifier}, rssi={self.rssi})"
