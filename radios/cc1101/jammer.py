import serial
import time
import logging

import usb.core
import usb.util
from registers import *
import sys

'''
cp2102 USB to UART + CC1101 UART module
'''
# Configure logging
logging.basicConfig(level=logging.DEBUG)

def init_serial(port, baudrate):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)  # Set timeout to 1 second
        if ser.is_open:
            logging.info(f"Serial port {port} opened successfully")
        return ser
    except Exception as e:
        logging.error(f"Error opening serial port: {e}")
        return None

def spi_transfer(ser, data, sleep_duration=0.01):
    logging.debug(f"Sending SPI data: {data}")
    ser.write(data)
    time.sleep(sleep_duration)
    response = ser.read(len(data))
    logging.debug(f"SPI transfer response: {response}")
    if not response:
        logging.error(f"No response received for SPI transfer with data: {data}")
        return bytes([0])
    return response

def reset_cc1101(ser):
    logging.info("Resetting CC1101")
    spi_transfer(ser, bytes([CC1101_SRES]), sleep_duration=0.1)
    time.sleep(0.1)
    logging.info("CC1101 reset complete")

def batch_write_registers(ser, register_values):
    for addr, value in register_values:
        addr = addr & 0x3F  # Ensure address is within range
        response = spi_transfer(ser, bytes([addr, value]), sleep_duration=0.01)
        if response[0] != value:
            logging.warning(f"Write verification failed for register {addr}: expected {value}, got {response[0]}")

def configure_cc1101(ser):
    logging.info("Configuring CC1101")
    register_values = [
        (CC1101_IOCFG2, 0x29),      # GDO2 output pin configuration
        (CC1101_IOCFG0, 0x06),      # GDO0 output pin configuration
        (CC1101_FIFOTHR, 0x47),     # RX FIFO and TX FIFO thresholds
        (CC1101_PKTLEN, 0x3D),      # Packet length
        (CC1101_PKTCTRL1, 0x04),    # Packet automation control
        (CC1101_PKTCTRL0, 0x05),    # Packet automation control
        (CC1101_MDMCFG4, 0xF5),     # Modem configuration
        (CC1101_MDMCFG3, 0x83),     # Modem configuration
        (CC1101_MDMCFG2, 0x13),     # Modem configuration
        (CC1101_MDMCFG1, 0x22),     # Modem configuration
        (CC1101_MDMCFG0, 0xF8),     # Modem configuration
        (CC1101_DEVIATN, 0x15),     # Modem deviation setting
        (CC1101_MCSM0, 0x18),       # Main Radio Control State Machine configuration
        (CC1101_FOCCFG, 0x1D),      # Frequency Offset Compensation configuration
        (CC1101_BSCFG, 0x1C),       # Bit Synchronization configuration
        (CC1101_AGCCTRL2, 0xC7),    # AGC control
        (CC1101_AGCCTRL1, 0x00),    # AGC control
        (CC1101_AGCCTRL0, 0xB2),    # AGC control
        (CC1101_FSCAL3, 0xEA),      # Frequency synthesizer calibration
        (CC1101_FSCAL2, 0x0A),      # Frequency synthesizer calibration
        (CC1101_FSCAL1, 0x00),      # Frequency synthesizer calibration
        (CC1101_FSCAL0, 0x11),      # Frequency synthesizer calibration
        (CC1101_TEST2, 0x81),       # Various test settings
        (CC1101_TEST1, 0x35),       # Various test settings
        (CC1101_TEST0, 0x09),       # Various test settings
        (CC1101_SYNC1, 0xD3),       # Sync word, high byte
        (CC1101_SYNC0, 0x91)        # Sync word, low byte
    ]
    batch_write_registers(ser, register_values)
    # Set PATABLE for maximum output power
    max_power = 0xC0  # value for maximum power
    spi_transfer(ser, bytes([CC1101_PATABLE, max_power]))
    logging.info("CC1101 configuration complete")

def set_frequency(ser, freq2, freq1, freq0):
    logging.info(f"Setting frequency to: FREQ2=0x{freq2:02X}, FREQ1=0x{freq1:02X}, FREQ0=0x{freq0:02X}")
    batch_write_registers(ser, [(CC1101_FREQ2, freq2), (CC1101_FREQ1, freq1), (CC1101_FREQ0, freq0)])

def convert_frequency_to_registers(frequency_mhz):
    # Convert the frequency to the CC1101 register values
    f_xosc = 26.0  # Crystal oscillator frequency in MHz
    freq = int((frequency_mhz * (2**16)) / f_xosc)
    freq2 = (freq >> 16) & 0xFF
    freq1 = (freq >> 8) & 0xFF
    freq0 = freq & 0xFF
    return freq2, freq1, freq0

def jam_frequencies(ser, raw_frequencies, packets_per_freq=10, spi_sleep=0.0005):
    frequencies = [convert_frequency_to_registers(freq) for freq in raw_frequencies]
    if not frequencies:
        logging.error("No frequencies provided for jamming.")
        return
    try:
        while True:
            for raw_freq, freq in zip(raw_frequencies, frequencies):
                set_frequency(ser, *freq)
                for _ in range(packets_per_freq):
                    spi_transfer(ser, bytes([CC1101_STX]), sleep_duration=spi_sleep)  # Enter TX mode
                    logging.info(f"Jamming frequency: {raw_freq} MHz, registers: {freq}")
                    spi_transfer(ser, bytes([CC1101_SIDLE]), sleep_duration=spi_sleep)  # Exit TX mode
    except KeyboardInterrupt:
        logging.info("Jamming stopped by user")
    finally:
        ser.close()
        logging.info("Serial port closed")

def read_rssi(ser):
    response = spi_transfer(ser, bytes([CC1101_RSSI | 0x80]), sleep_duration=0.001)
    if len(response) < 1:
        logging.error("Failed to read RSSI value")
        return -255  # Return a very low RSSI value to indicate failure
    rssi = response[0]
    if rssi >= 128:
        rssi -= 256
    return rssi / 2 - 74  # RSSI offset adjustment as per CC1101 datasheet

def check_carrier_sense(ser):
    response = spi_transfer(ser, bytes([CC1101_PKTSTATUS | 0x80]), sleep_duration=0.001)
    if len(response) < 1:
        logging.error("Failed to read carrier sense status")
        return False
    pktstatus = response[0]
    carrier_sense = pktstatus & 0x40  # Carrier sense bit
    return carrier_sense != 0

def find_highest_rssi_channel(ser, frequency_range):
    max_rssi = -float('inf')
    best_freq_mhz = None
    best_freq_regs = None
    for freq_mhz in frequency_range:
        freq2, freq1, freq0 = convert_frequency_to_registers(freq_mhz)
        set_frequency(ser, freq2, freq1, freq0)
        spi_transfer(ser, bytes([CC1101_SRX]), sleep_duration=0.001)  # Enter RX mode
        time.sleep(0.1)  # Wait for the CC1101 to settle in RX mode
        rssi = read_rssi(ser)
        carrier_sense = check_carrier_sense(ser)
        logging.info(f"Scanned frequency: {freq_mhz} MHz, RSSI: {rssi} dBm, Carrier Sense: {carrier_sense}")
        if carrier_sense and rssi > max_rssi:
            max_rssi = rssi
            best_freq_mhz = freq_mhz
            best_freq_regs = (freq2, freq1, freq0)
    if best_freq_regs is None:
        logging.error("No valid frequencies found during RSSI scan.")
        return None 
    logging.info(f"Highest RSSI found: {max_rssi} dBm at frequency {best_freq_regs}")
    return best_freq_mhz


def check_uart_bridge(ser):
    # Simple check to ensure UART bridge is operational
    try:
        ser.write(b'AT\r\n')
        response = ser.read(64)
        logging.debug(f"UART bridge response: {response}")
        return response != b''
    except Exception as e:
        logging.error(f"Error checking UART bridge: {e}")
        return False
    
def check_cc1101(ser):
    try:
        # Send strobe command to reset the CC1101
        reset_response = spi_transfer(ser, bytes([CC1101_SRES]), sleep_duration=0.1)
        logging.debug(f"Reset response: {reset_response}")

        # Read part number from CC1101
        partnum = spi_transfer(ser, bytes([CC1101_PARTNUM | 0x80]), sleep_duration=0.01)
        logging.debug(f"Part number response: {partnum}")

        if len(partnum) < 1 or partnum[0] == 0x00:
            logging.error("Failed to read part number from CC1101")
            return False
        
        # Read version number from CC1101
        version = spi_transfer(ser, bytes([CC1101_VERSION | 0x80]), sleep_duration=0.01)
        logging.debug(f"Version number response: {version}")

        if len(version) < 1 or version[0] == 0x00:
            logging.error("Failed to read version number from CC1101")
            return False

        logging.info(f"CC1101 Part Number: {partnum[0]}")
        logging.info(f"CC1101 Version: {version[0]}")
        return True
    except Exception as e:
        logging.error(f"Error communicating with CC1101: {e}")
        return False

def check_device_connection(port, baudrate):
    # Check CC1101 connection via CP2102
    ser = init_serial(port, baudrate)
    if not ser:
        return False
    
    logging.info("Checking CC1101 connection...")
    
    # Test communication by sending a basic command and reading back a response
    test_command = bytes([CC1101_SRES])
    logging.debug(f"Test command: {test_command}")
    response = spi_transfer(ser, test_command)
    logging.debug(f"Test command response: {response}")
    
    if not check_cc1101(ser):
        ser.close()
        return False
    
    ser.close()
    return True
    
    
if __name__ == "__main__":
    port = "COM4"  # Adjust as necessary for your system
    baudrate = 115200  # Maximum supported baud rate

    if check_device_connection(port, baudrate):
        logging.info("CC1101 device is connected and operational")
    else:
        logging.error("CC1101 device is not connected or failed to initialize")
        sys.exit()

    ser = init_serial(port, baudrate)
    if ser:
        reset_cc1101(ser)
        configure_cc1101(ser)
        
        # Define the raw frequencies to jam
        #raw_frequencies = [433.0, 433.1, 433.2, 433.3, 433.4]  # Frequencies in MHz
        raw_frequencies = None
        
        # Find the highest RSSI channel if no frequencies are passed in
        if not raw_frequencies:
            frequency_range = [433.05 + 0.025 * i for i in range(int((434.775 - 433.05) / 0.025) + 1)]
            best_freq = find_highest_rssi_channel(ser, frequency_range)
            raw_frequencies = [best_freq]
        
        # Jam the defined frequencies
        jam_frequencies(ser, raw_frequencies, packets_per_freq=10, spi_sleep=0.0005)