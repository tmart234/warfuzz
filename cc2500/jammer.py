import serial
import time

# Configure the serial port
ser = serial.Serial('COM3', 115200, timeout=1)  # Replace 'COM3' with your actual COM port

def send_command(command):
    ser.write(command.encode())
    time.sleep(0.05)
    response = ser.read_all()
    print(response.decode('utf-8'))

def init_cc2500():
    # Reset command
    send_command('SRES\n')
    time.sleep(0.1)
    
    # Basic configuration settings (if needed)
    # send_command('SET IOCFG0 0x06\n')  # GDO0 Output Pin Configuration

def set_frequency(frequency):
    freq_setting = int((frequency / 26.0) * 65536)
    freq2 = (freq_setting >> 16) & 0xFF
    freq1 = (freq_setting >> 8) & 0xFF
    freq0 = freq_setting & 0xFF
    
    send_command(f'SET FREQ2 {freq2}\n')
    send_command(f'SET FREQ1 {freq1}\n')
    send_command(f'SET FREQ0 {freq0}\n')

def start_jamming():
    # Enable TX mode
    send_command('STX\n')

def stop_jamming():
    # Reset to stop transmission
    send_command('SRES\n')

def frequency_hopping():
    frequencies = [2435, 2445, 2461]  # Specified frequencies
    hop_interval = 0.05  # 50 milliseconds per frequency
    
    while True:
        for frequency in frequencies:
            set_frequency(frequency)
            start_jamming()
            time.sleep(hop_interval)
            stop_jamming()

if __name__ == "__main__":
    init_cc2500()
    try:
        frequency_hopping()
    except KeyboardInterrupt:
        stop_jamming()
        ser.close()
        print("Jamming stopped")
