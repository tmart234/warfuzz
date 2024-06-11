import usb.core
import usb.util
import time
import random

# Constants for CC2500
CMD_STROBE = 0x30
CMD_WRITE = 0x40
CMD_READ = 0x80
CC2500_CHANNR = 0x0A
CC2500_RSSI = 0x34
CC2500_RXBYTES = 0x3B

def send_command(dev, cmd, data):
    dev.ctrl_transfer(0x40, cmd, 0, 0, data, 5000)

def read_response(dev, length):
    return dev.ctrl_transfer(0xC0, CMD_READ, 0, 0, length, 5000)

def reset_cc2500(dev):
    send_command(dev, CMD_STROBE, [0x30])
    time.sleep(0.1)

def configure_cc2500(dev, mode):
    if mode == 'ISM':
        config = [
            [0x00, 0x29], # IOCFG2
            [0x01, 0x2E], # IOCFG1
            [0x02, 0x06], # IOCFG0
            [0x0B, 0x1D], # Example ISM configuration
            # Add more ISM-specific configurations here
        ]
    else:
        config = [
            [0x00, 0x29], # IOCFG2
            [0x01, 0x2E], # IOCFG1
            [0x02, 0x06], # IOCFG0
            [0x0B, 0x0A], # Example SRD configuration
            # Add more SRD-specific configurations here
        ]

    for reg, value in config:
        send_command(dev, CMD_WRITE, [reg, value])

def scan_for_devices(dev):
    for channel in range(255):
        send_command(dev, CMD_WRITE, [CC2500_CHANNR, channel])
        send_command(dev, CMD_STROBE, [0x34])  # SRX
        time.sleep(0.01)
        rssi = read_response(dev, 1)[0]
        rx_bytes = read_response(dev, 1)[0] & 0x7F  # Get RX bytes
        send_command(dev, CMD_STROBE, [0x36])  # SIDLE

        if rssi >= 0x80 and rx_bytes > 0:
            return channel

    return None

def fuzz_device(dev, channel):
    print(f"Fuzzing device on channel {channel}")
    while True:
        # Random packet size and payload
        packet_size = random.randint(1, 64)
        payload = [random.randint(0, 255) for _ in range(packet_size)]

        # Send packet
        send_command(dev, CMD_WRITE, [0x3F] + payload)  # TX FIFO
        send_command(dev, CMD_STROBE, [0x35])  # STX
        time.sleep(0.01)
        send_command(dev, CMD_STROBE, [0x36])  # SIDLE

        # Short delay between fuzzing packets
        time.sleep(0.1)

def main():
    dev = usb.core.find(idVendor=0x0451, idProduct=0x16AE)
    if dev is None:
        raise ValueError('Device not found')

    dev.set_configuration()
    usb.util.claim_interface(dev, 0)

    reset_cc2500(dev)

    while True:
        mode = random.choice(['ISM', 'SRD'])
        configure_cc2500(dev, mode)
        channel = scan_for_devices(dev)
        if channel is not None:
            print(f"Found device on channel {channel} in {mode} mode")
            fuzz_device(dev, channel)

    usb.util.release_interface(dev, 0)
    usb.util.dispose_resources(dev)

if __name__ == "__main__":
    main()
