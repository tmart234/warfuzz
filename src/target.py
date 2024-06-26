class Target:
    def __init__(self, name: str, rssi: int, id: str):
        self.name = name
        self.rssi = rssi
        self.id = id

    def __repr__(self):
        return f"Target(identifier={self.id}, rssi={self.rssi}, name={self.name})"
