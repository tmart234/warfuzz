#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <usb.h>

#define CMD_STROBE 0x30
#define CMD_WRITE 0x40
#define CMD_READ 0x80
#define CC2500_CHANNR 0x0A
#define CC2500_RSSI 0x34
#define CC2500_RXBYTES 0x3B

void send_command(usb_dev_handle *dev, uint8_t cmd, uint8_t *data, int length) {
    usb_control_msg(dev, 0x40, cmd, 0, 0, (char *)data, length, 5000);
}

int read_response(usb_dev_handle *dev, uint8_t *buffer, int length) {
    return usb_control_msg(dev, 0xC0, CMD_READ, 0, 0, (char *)buffer, length, 5000);
}

void reset_cc2500(usb_dev_handle *dev) {
    uint8_t cmd = 0x30;
    send_command(dev, CMD_STROBE, &cmd, 1);
    usleep(100000);
}

void configure_cc2500_ism(usb_dev_handle *dev) {
    uint8_t config[][2] = {
        {0x00, 0x29},
        {0x01, 0x2E},
        {0x02, 0x06},
        {0x0B, 0x1D},
        // Add more ISM-specific configurations here
    };
    for (int i = 0; i < sizeof(config) / sizeof(config[0]); i++) {
        send_command(dev, CMD_WRITE, config[i], 2);
    }
}

void configure_cc2500_srd(usb_dev_handle *dev) {
    uint8_t config[][2] = {
        {0x00, 0x29},
        {0x01, 0x2E},
        {0x02, 0x06},
        {0x0B, 0x0A},
        // Add more SRD-specific configurations here
    };
    for (int i = 0; i < sizeof(config) / sizeof(config[0]); i++) {
        send_command(dev, CMD_WRITE, config[i], 2);
    }
}

int scan_for_devices(usb_dev_handle *dev) {
    uint8_t buffer[1];
    for (uint8_t channel = 0; channel < 255; channel++) {
        send_command(dev, CMD_WRITE, (uint8_t[]){CC2500_CHANNR, channel}, 2);
        send_command(dev, CMD_STROBE, (uint8_t[]){0x34}, 1); // SRX
        usleep(10000);
        read_response(dev, buffer, 1);
        uint8_t rssi = buffer[0];
        read_response(dev, buffer, 1);
        uint8_t rx_bytes = buffer[0] & 0x7F; // Get RX bytes
        send_command(dev, CMD_STROBE, (uint8_t[]){0x36}, 1); // SIDLE
        if (rssi >= 0x80 && rx_bytes > 0) {
            return channel;
        }
    }
    return 0xFF;
}

void fuzz_device(usb_dev_handle *dev) {
    while (1) {
        // Random packet size and payload
        uint8_t packet[256];
        int packet_length = rand() % 64 + 1;
        for (int i = 0; i < packet_length; i++) {
            packet[i] = rand() % 256;
        }
        send_command(dev, CMD_WRITE, packet, packet_length);
        send_command(dev, CMD_STROBE, (uint8_t[]){0x35}, 1); // STX
        usleep(10000);
        send_command(dev, CMD_STROBE, (uint8_t[]){0x36}, 1); // SIDLE
        usleep(100000);
    }
}

int main() {
    usb_init();
    usb_find_busses();
    usb_find_devices();
    struct usb_bus *busses = usb_get_busses();
    struct usb_device *dev = NULL;
    for (struct usb_bus *bus = busses; bus; bus = bus->next) {
        for (dev = bus->devices; dev; dev = dev->next) {
            if (dev->descriptor.idVendor == 0x0451 && dev->descriptor.idProduct == 0x16AE) {
                break;
            }
        }
    }
    if (!dev) {
        fprintf(stderr, "Device not found\n");
        return 1;
    }
    usb_dev_handle *handle = usb_open(dev);
    if (!handle) {
        fprintf(stderr, "Failed to open device\n");
        return 1;
    }
    usb_set_configuration(handle, 1);
    usb_claim_interface(handle, 0);

    reset_cc2500(handle);

    // Main loop for scanning and fuzzing
    while (1) {
        char mode[4];
        printf("Enter mode (ISM/SRD): ");
        scanf("%s", mode);
        
        if (strcmp(mode, "ISM") == 0) {
            configure_cc2500_ism(handle);
        } else if (strcmp(mode, "SRD") == 0) {
            configure_cc2500_srd(handle);
        } else {
            printf("Invalid mode\n");
            continue;
        }

        int channel = scan_for_devices(handle);
        if (channel != 0xFF) {
            printf("Found device on channel %d\n", channel);
            fuzz_device(handle);
        } else {
            printf("No devices found\n");
        }
    }

    usb_release_interface(handle, 0);
    usb_close(handle);
    return 0;
}
