from ctypes import c_int, POINTER, Structure, c_char_p, c_void_p, c_uint16
import ctypes

# Define the BLEDevice structure as it appears in C
class BLEDevice(Structure):
    _fields_ = [
        ('vid', c_uint16),
        ('pid', c_uint16),
        ('name', c_char_p),
        ('mac_address', c_char_p),
        ('rssi', c_int),
        ('channel', c_int),
        ('next', POINTER(BLEDevice))  # Pointer to the next device (simple linked list)
    ]

# Load the shared library
lib = ctypes.CDLL('./cc2540.so')

# Set argument types and return types for the functions
lib.libusb_init.argtypes = [c_void_p]
lib.libusb_init.restype = None

lib.sniff.argtypes = [c_void_p, c_uint16, c_uint16, c_int]
lib.sniff.restype = None

lib.print_devices.argtypes = []
lib.print_devices.restype = None

# Initialize libusb (assuming there's a relevant function exposed)
lib.libusb_init(None)

# Start the sniffer
lib.sniff(None, 0x451, 0x16B3, 37)

# Print devices
lib.print_devices()