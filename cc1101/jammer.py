import serial
import time
import logging
from registers import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_serial(port, baudrate):
    try:
        ser = serial.Serial(port, baudrate, timeout=0)  # Set timeout to 0 for non-blocking mode
        if ser.is_open:
            logging.info(f"Serial port {port} opened successfully")
        return ser
    except Exception as e:
        logging.error(f"Error opening serial port: {e}")
        return None

def spi_transfer(ser, data, sleep_duration=0.0001):
    ser.write(data)
    time.sleep(sleep_duration)  # Minimal sleep duration for your hardware
    response = ser.read(len(data))
    logging.debug(f"SPI transfer data sent: {data}, received: {response}")
    return response

def reset_cc1101(ser):
    logging.info("Resetting CC1101")
    spi_transfer(ser, bytes([CC1101_SRES]), sleep_duration=0.1)
    time.sleep(0.1)
    logging.info("CC1101 reset complete")

def batch_write_registers(ser, register_values):
    for addr, value in register_values:
        addr = addr & 0x3F  # Ensure address is within range
        spi_transfer(ser, bytes([addr, value]), sleep_duration=0.0001)

def configure_cc1101(ser):
    logging.info("Configuring CC1101")
    register_values = [
        (CC1101_IOCFG2, 0x29),
        (CC1101_IOCFG0, 0x06),
        (CC1101_FIFOTHR, 0x47),
        (CC1101_PKTLEN, 0x3D),
        (CC1101_PKTCTRL1, 0x04),
        (CC1101_PKTCTRL0, 0x05),
        (CC1101_FREQ2, 0x10),
        (CC1101_FREQ1, 0xA7),
        (CC1101_FREQ0, 0x62),
        (CC1101_MDMCFG4, 0xF5),
        (CC1101_MDMCFG3, 0x83),
        (CC1101_MDMCFG2, 0x13),
        (CC1101_MDMCFG1, 0x22),
        (CC1101_MDMCFG0, 0xF8),
        (CC1101_DEVIATN, 0x15),
        (CC1101_MCSM0, 0x18),
        (CC1101_FOCCFG, 0x1D),
        (CC1101_BSCFG, 0x1C),
        (CC1101_AGCCTRL2, 0xC7),
        (CC1101_AGCCTRL1, 0x00),
        (CC1101_AGCCTRL0, 0xB2),
        (CC1101_FSCAL3, 0xEA),
        (CC1101_FSCAL2, 0x0A),
        (CC1101_FSCAL1, 0x00),
        (CC1101_FSCAL0, 0x11),
        (CC1101_TEST2, 0x81),
        (CC1101_TEST1, 0x35),
        (CC1101_TEST0, 0x09)
    ]
    batch_write_registers(ser, register_values)
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

def jam_frequencies(ser, raw_frequencies, packets_per_freq=10, spi_sleep=0.0001):
    frequencies = [convert_frequency_to_registers(freq) for freq in raw_frequencies]
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

if __name__ == "__main__":
    port = "COM4"  # Adjust as necessary for your system
    baudrate = 115200  # Maximum supported baud rate

    ser = init_serial(port, baudrate)
    if ser:
        reset_cc1101(ser)
        configure_cc1101(ser)
        
        # Define the raw frequencies to jam
        raw_frequencies = [433.0, 433.1, 433.2, 433.3, 433.4]  # Frequencies in MHz
        
        # Jam the defined frequencies with more packets per frequency
        jam_frequencies(ser, raw_frequencies, packets_per_freq=10, spi_sleep=0.0001)
