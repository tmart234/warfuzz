import serial
import serial.tools.list_ports
import time
import logging
from registers import *

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def check_cc1101(ser):
    try:
        # Send strobe command to reset the CC1101
        reset_command = bytes([CC1101_SRES])
        reset_response = send_command(ser, reset_command)
        logging.debug(f"Reset response: {reset_response}")

        # Read part number from CC1101
        partnum_command = bytes([CC1101_PARTNUM | 0x80])
        partnum_response = send_command(ser, partnum_command)
        logging.debug(f"Part number response: {partnum_response}")

        if len(partnum_response) < 1 or partnum_response[0] == 0x00:
            logging.error("Failed to read part number from CC1101")
            return False
        
        # Read version number from CC1101
        version_command = bytes([CC1101_VERSION | 0x80])
        version_response = send_command(ser, version_command)
        logging.debug(f"Version number response: {version_response}")

        if len(version_response) < 1 or version_response[0] == 0x00:
            logging.error("Failed to read version number from CC1101")
            return False

        logging.info(f"CC1101 Part Number: {partnum_response[0]}")
        logging.info(f"CC1101 Version: {version_response[0]}")
        return True
    except Exception as e:
        logging.error(f"Error communicating with CC1101: {e}")
        return False

def init_serial(port, baudrate):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)  # Set timeout to 1 second
        if ser.is_open:
            logging.info(f"Serial port {port} opened successfully")
            logging.debug(f"Serial port details: {ser}")
        return ser
    except Exception as e:
        logging.error(f"Error opening serial port {port}: {e}")
        return None
    
def send_command(ser, command):
    logging.debug(f"Sending serial command: {command}")
    ser.write(command)
    time.sleep(0.5)
    response = ser.read(ser.in_waiting or 1)  # Read the response
    logging.debug(f"Command response: {response}")
    if not response:
        logging.error(f"Failed to execute command: {command}")
    return response

def send_strobe_command(ser, command):
    logging.debug(f"Sending strobe command: {command}")
    ser.write(command)
    time.sleep(0.1)  # Shorter delay for strobe commands
    response = ser.read(ser.in_waiting or 1)  # Read the response
    logging.debug(f"Strobe command response: {response}")
    if not response:
        logging.error(f"Failed to execute strobe command: {command}")
    return response

def send_command(ser, command):
    logging.debug(f"Sending serial command: {command}")
    ser.write(command)
    time.sleep(0.5)
    response = ser.read(ser.in_waiting or 1)  # Read the response
    logging.debug(f"Command response: {response}")
    if not response:
        logging.error(f"Failed to execute command: {command}")
    return response

def configure_rf1100_232(ser):
    # Set baud rate to 19200
    baudrate_command = bytes([0xA3, 0x3A, 0x03])
    send_command(ser, baudrate_command)

    # Set channel to 6
    channel_command = bytes([0xA7, 0x7A, 0x06])
    send_command(ser, channel_command)

    # Set TX power to 10 dBm
    tx_power_command = bytes([0xAB, 0xBA, 0x0A])
    send_command(ser, tx_power_command)

    # Set module ID to 0x0008
    module_id_command = bytes([0xA9, 0x9A, 0x00, 0x08])
    send_command(ser, module_id_command)

def check_device_connection(ser):
    # Perform a basic serial communication test
    logging.info("Performing basic serial communication test...")
    ser.write(b'\xA6\x6A')  # Example command to read configuration
    time.sleep(0.5)
    response = ser.read(ser.in_waiting or 1)  # Read the response
    logging.debug(f"Basic serial test response: {response}")
    if response:
        logging.info("Basic serial communication test passed.")
        return True
    else:
        logging.error("Basic serial communication test failed.")
        return False

def find_device():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        ser = init_serial(port.device, 19200)
        if ser:
            if check_device_connection(ser):
                logging.info(f"Device found on {port.device}")
                return ser
            ser.close()
    logging.error("Device not found on any COM port.")
    return None

def reset_cc1101(ser):
    try:
        # Send strobe command to reset the CC1101
        send_strobe_command(ser, CC1101_SRES.to_bytes(1,'big'))
        time.sleep(0.1)

        # Idle the chip
        send_strobe_command(ser, bytes([CC1101_SIDLE]))
        time.sleep(0.1)

        # Flush TX FIFO
        send_strobe_command(ser, bytes([CC1101_SFTX]))
        time.sleep(0.1)

        # Flush RX FIFO
        send_strobe_command(ser, bytes([CC1101_SFRX]))
        time.sleep(0.1)

        # Enable RX
        send_strobe_command(ser, bytes([CC1101_SRX]))
        time.sleep(0.1)

        return True
    except Exception as e:
        logging.error(f"Error resetting CC1101: {e}")
        return False

if __name__ == "__main__":
    ser = find_device()
    if ser:
        configure_rf1100_232(ser)
        if reset_cc1101(ser):
            logging.info("CC1101 device reset successfully.")
        ser.close()