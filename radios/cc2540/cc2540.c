#include <stdbool.h>
#include <libusb.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define TIMEOUT 1000

// from https://github.com/andrewdodd/ccsniffpiper/blob/master/ccsniffpiper.py
#define GET_IDENT   0xC0
#define SET_POWER   0xC5
#define GET_POWER   0xC6
#define SET_START   0xD0
#define SET_END     0xD1
#define SET_CHAN    0xD2

#define POWER_RETRIES 10
#define FUZZ_PACKET_SIZE 32

typedef struct BLEDevice {
    uint16_t vid;
    uint16_t pid;
    char name[256];  // Placeholder for device name, if available
    char mac_address[18];  // MAC addresses are 17 characters long + NULL
    int rssi;
    int channel;
    struct BLEDevice* next;  // Link to the next device (simple linked list)
} BLEDevice;

BLEDevice* first_device = NULL;  // Head of the linked list of devices

void add_device(BLEDevice* device) {
    device->next = first_device;
    first_device = device;
}

void print_devices() {
    BLEDevice* device = first_device;
    while (device != NULL) {
        printf("Device: VID=%04X, PID=%04X, Name=%s, MAC=%s, RSSI=%d, Channel=%d\n",
            device->vid, device->pid, device->name, device->mac_address, device->rssi, device->channel);
        device = device->next;
    }
}

void analyze_and_store_data(uint8_t* data, int len, int channel) {
    // Placeholder for packet analysis
    // You would parse the BLE packets here and extract the necessary information
    // For demonstration, let's assume we have a function that can parse and return BLE device info

    BLEDevice* new_device = malloc(sizeof(BLEDevice));
    if (new_device == NULL) return;

    // Simulated data filling
    new_device->vid = 0x451;  // Example VID
    new_device->pid = 0x16B3;  // Example PID
    strcpy(new_device->name, "Example BLE Device");
    strcpy(new_device->mac_address, "AA:BB:CC:DD:EE:FF");
    new_device->rssi = -42;  // Example RSSI
    new_device->channel = channel;

    add_device(new_device);
}

static void bulk_read(libusb_device_handle *dev, int channel) {
    uint8_t data[1024];
    while (1) {
        int xfer = 0;
        int ret = libusb_bulk_transfer(dev, 0x83, data, sizeof(data), &xfer, TIMEOUT);
        if (ret == 0) {
            analyze_and_store_data(data, xfer, channel);
            break;  // Break after one successful read for demo purposes
        }
    }
}

static void send_fuzzed_data(libusb_device_handle *dev, int packet_size) {
    uint8_t fuzz_packet[packet_size];
    srand(time(NULL));  // Seed for random number generator

    for (int i = 0; i < packet_size; i++) {
        fuzz_packet[i] = rand() % 256;  // Generate a random byte
    }

    int ret = libusb_control_transfer(dev, 0x40, 0xC9, 0x00, 0x00, fuzz_packet, packet_size, TIMEOUT);
    if (ret < 0) {
        printf("Failed to send fuzzed data!\n");
    } else {
        printf("Fuzzed data sent successfully!\n");
    }
}

static int get_ident(libusb_device_handle *dev)
{
    uint8_t ident[32];
    int ret;
    
    ret = libusb_control_transfer(dev, 0xC0, GET_IDENT, 0x00, 0x00, ident, sizeof(ident), TIMEOUT);
    if (ret > 0) {
        int i;
        printf("IDENT:");
        for (i = 0; i < ret; i++) {
            printf(" %02X", ident[i]);
        }
        printf("\n");
    }
    return ret;
}

static int set_power(libusb_device_handle *dev, uint8_t power, int retries)
{
    int ret;

   // set power
    ret = libusb_control_transfer(dev, 0x40, SET_POWER, 0x00, power, NULL, 0, TIMEOUT);
    
    // get power until it is the same as configured in set_power
    int i;
    for (i = 0; i < retries; i++) {
        uint8_t data;
        ret = libusb_control_transfer(dev, 0xC0, GET_POWER, 0x00, 0x00, &data, 1, TIMEOUT);
        if (ret < 0) {
            return ret;
        }
        if (data == power) {
            return 0;
        }
    }
    return ret;
}

static int set_channel(libusb_device_handle *dev, uint8_t channel)
{
    int ret;
    uint8_t data;

    data = channel & 0xFF;
    ret = libusb_control_transfer(dev, 0x40, SET_CHAN, 0x00, 0x00, &data, 1, TIMEOUT);
    if (ret < 0) {
        printf("setting channel (LSB) failed!\n");
        return ret;
    }
    data = (channel >> 8) & 0xFF;
    ret = libusb_control_transfer(dev, 0x40, SET_CHAN, 0x00, 0x01, &data, 1, TIMEOUT);
    if (ret < 0) {
        printf("setting channel (LSB) failed!\n");
        return ret;
    }

    return ret;
}

static int setup(libusb_device_handle *dev, int channel)
{
    int ret;
    
    // read ident
    ret = get_ident(dev);
    if (ret < 0) {
        printf("getting identity failed!\n");
        return ret;
    }
    
    // set power
    ret = set_power(dev, 0x04, POWER_RETRIES);
    if (ret < 0) {
        printf("setting power failed!\n");
        return ret;
    }

    // ?
    ret = libusb_control_transfer(dev, 0x40, 0xC9, 0x00, 0x00, NULL, 0, TIMEOUT);
    if (ret < 0) {
        printf("setting reg 0xC9 failed!\n");
        return ret;
    }

    // set capture channel
    ret = set_channel(dev, channel);
    if (ret < 0) {
        printf("setting channel failed!\n");
        return ret;
    }

    // start capture?
    ret = libusb_control_transfer(dev, 0x40, SET_START, 0x00, 0x00, NULL, 0, TIMEOUT);

    return ret;
}

static void bulk_read(libusb_device_handle *dev)
{
    uint8_t data[1024];
    while (1) {
        int xfer = 0;
        int ret = libusb_bulk_transfer(dev, 0x83, data, sizeof(data), &xfer, TIMEOUT);
        if (ret == 0) {
            int i;
            for (i = 0; i < xfer; i++) {
                if ((i % 16) == 0) {
                    printf("\n%04X:", i);
                }
                printf(" %02X", data[i]);
            }
            printf("\n");
        }
    }
}

static void sniff(libusb_context *context, uint16_t pid, uint16_t vid, int channel)
{
    libusb_device_handle *dev = libusb_open_device_with_vid_pid(context, pid, vid);
    if (dev != NULL) {
        printf("Opened USB device %04X:%04X\n", pid, vid);

        int ret;
        ret = setup(dev, channel);
        if (ret < 0) {
            printf("Sniffer setup failed!\n");
        } else {
            bulk_read(dev);
        }

        libusb_close(dev);
    } else {
        printf("USB device %04X:%04X not found!\n", pid, vid);
    }
}

int main(int argc, char *argv[]) {
    int channel = 37;
    if (argc > 1) channel = atoi(argv[1]);

    libusb_context *context;
    libusb_init(&context);
    libusb_set_option(context, LIBUSB_OPTION_LOG_LEVEL, LIBUSB_LOG_LEVEL_WARNING);
    sniff(context, 0x451, 0x16B3, channel);
    print_devices();
    libusb_exit(context);

    return 0;
}