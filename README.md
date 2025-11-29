# Smart Parking System using ESP32

## Overview

This project implements a Smart Parking System that monitors parking spot occupancy in real-time. The system uses an ESP32 Huzzah Fruitboard as a central hub that receives parking sensor notifications from nRF52840 Bluefruit Adafruit boards via Bluetooth Low Energy (BLE). The ESP32 then publishes the parking status updates to an MQTT broker (HiveMQ Cloud) for cloud connectivity and remote monitoring.

## System Architecture

```
┌─────────────────────┐
│  nRF52840 Sensor 1  │──┐
│  (Parking Spot 1)   │  │
└─────────────────────┘  │
                         │ BLE
┌─────────────────────┐  │
│  nRF52840 Sensor 2  │──┼──► ESP32 Huzzah ──► Wi-Fi ──► MQTT Broker
│  (Parking Spot 2)   │  │     Fruitboard      (HiveMQ Cloud)
└─────────────────────┘  │
                         │
┌─────────────────────┐  │
│  nRF52840 Sensor N  │──┘
│  (Parking Spot N)   │
└─────────────────────┘
```

## Hardware Requirements

### Central Device
- **ESP32 Huzzah Fruitboard** (Adafruit)
  - ESP32 microcontroller with Wi-Fi and BLE capabilities
  - Used as the central BLE device and MQTT client

### Sensor Devices
- **nRF52840 Bluefruit Adafruit boards** (one per parking spot)
  - nRF52840 microcontroller with BLE capabilities
  - Equipped with **APDS9960 proximity sensor** for parking detection
  - Built-in NeoPixel LED for visual status indication
  - Acts as BLE peripheral devices broadcasting parking status

### Additional Components
- Wi-Fi network for internet connectivity
- Power supply for ESP32 and sensor boards
- **APDS9960 Proximity and Gesture Sensor** (integrated on nRF52840 boards or connected via I2C)

## Software Requirements

### Central Device (ESP32)
- **MicroPython** (latest stable version)
  - Required for ESP32 Huzzah Fruitboard
  - Download from: https://micropython.org/download/esp32/

### Sensor Devices (nRF52840)
- **CircuitPython** (latest stable version)
  - Required for nRF52840 Bluefruit Adafruit boards
  - Download from: https://circuitpython.org/board/adafruit_feather_nrf52840/
  - CircuitPython libraries bundle required

### Development Tools
- **Python 3.x** (for development and testing)
- **MQTT Broker Account** (HiveMQ Cloud or similar)
  - Free tier available at: https://www.hivemq.com/mqtt-cloud-broker/

## Libraries and Dependencies

### Required Libraries

1. **aioble** (v0.6.1)
   - Bluetooth Low Energy library for MicroPython
   - Provides BLE central and peripheral functionality
   - Located in `lib/aioble/`

2. **umqtt.robust** (v1.0.2)
   - Robust MQTT client library for MicroPython
   - Handles MQTT connections with automatic reconnection
   - Located in `lib/umqtt/robust.py`

3. **ssd1306** (v0.1.0) - Optional
   - OLED display driver library
   - Located in `lib/ssd1306.py`

### CircuitPython Libraries (for nRF52840 Sensors)

The sensor code requires the following CircuitPython libraries (install via CircuitPython library bundle):

1. **adafruit_ble** - BLE functionality for CircuitPython
2. **adafruit_apds9960** - APDS9960 proximity sensor driver
3. **neopixel** - NeoPixel LED control (usually built-in)

### Library Installation

#### ESP32 (MicroPython)
The required libraries are already included in the `lib/` directory. If you need to install them manually:

1. Copy the `aioble` folder to your ESP32's `lib/` directory
2. Copy `umqtt/robust.py` to your ESP32's `lib/umqtt/` directory
3. Ensure all dependencies are properly installed on your MicroPython device

#### nRF52840 (CircuitPython)
1. Follow the installation guide at: [Feather Sense CircuitPython Libraries](https://learn.adafruit.com/adafruit-feather-sense/feather-sense-circuitpython-libraries)
2. Copy the following libraries to your nRF52840's `lib/` directory:
   - `adafruit_ble/`
   - `adafruit_apds9960.mpy`
   - `neopixel.mpy` (if not built-in)

## Configuration

### Wi-Fi Configuration

Edit `main.py` and update the following variables:

```python
WIFI_SSID = "your_wifi_ssid"
WIFI_PASSWORD = "your_wifi_password"
```

### MQTT Configuration

Edit `main.py` and update the following variables:

```python
MQTT_BROKER = "your_broker.hivemq.cloud"
MQTT_PORT = 8883
MQTT_CLIENT_ID = "esp32_parking"
MQTT_USER = "your_mqtt_username"
MQTT_PASSWORD = "your_mqtt_password"
TOPIC_PREFIX = "parking/"
```

### BLE Configuration

The system is configured to connect to multiple parking sensors. Each sensor uses a unique service UUID:

```python
DEVICE_SERVICES = {
    bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0"): "spot1",
    bluetooth.UUID("87654321-4321-5678-4321-0fedcba98765"): "spot2"
}
CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")
```

**Note:** Update these UUIDs to match your nRF52840 sensor configurations.

## How It Works

1. **Initialization**: The ESP32 connects to Wi-Fi and establishes an MQTT connection to the broker.

2. **BLE Scanning**: The ESP32 continuously scans for BLE devices advertising the configured service UUIDs.

3. **Device Connection**: When a parking sensor (nRF52840) is detected, the ESP32 connects to it and subscribes to notifications.

4. **Status Monitoring**: Each sensor sends parking status updates (occupied/free) via BLE notifications.

5. **MQTT Publishing**: Received status updates are queued and published to MQTT topics in the format:
   - Topic: `parking/{spot_name}/status`
   - Payload: `{"spot":"spot1","status":1}` (1 = occupied, 0 = free)

6. **Multi-threading**: 
   - BLE operations run in an async event loop
   - MQTT publishing runs in a separate thread for better performance

## Sensor Code Implementation

The sensor code files are located in separate folders:
- `BLE-Sensor-1/` - Contains `code.py` for Parking Spot 1 (Sensor 1)
- `BLE-Sensor-2/` - Contains `code.py` for Parking Spot 2 (Sensor 2)

Each `code.py` file contains the CircuitPython code for the nRF52840 Bluefruit Adafruit sensor boards. This code implements:

### Key Features

1. **APDS9960 Proximity Detection**
   - Uses I2C communication to read proximity values
   - Configurable threshold (default: 5) to determine occupancy
   - Proximity > threshold = Occupied (status = 1)
   - Proximity ≤ threshold = Free (status = 0)

2. **BLE Peripheral Service**
   - Custom BLE service with 128-bit Vendor UUID
   - Service UUID: `12345678-1234-5678-1234-56789abcdef0` (for spot1)
   - Characteristic UUID: `12345678-1234-5678-1234-56789abcdef1`
   - Supports READ and NOTIFY properties
   - Automatically advertises when not connected

3. **Visual Feedback**
   - NeoPixel LED indicates parking status:
     - **Red** = Occupied
     - **Green** = Free

4. **Status Change Detection**
   - Only sends BLE notifications when status changes
   - Reduces unnecessary BLE traffic
   - Updates every 200ms

### Sensor Code Configuration

To configure multiple sensors with different UUIDs, modify the following in `code.py`:

```python
# For Sensor 1 (Spot 1)
SERVICE_UUID = VendorUUID("12345678-1234-5678-1234-56789abcdef0")

# For Sensor 2 (Spot 2) - use different UUID
SERVICE_UUID = VendorUUID("87654321-4321-5678-4321-0fedcba98765")

# Proximity threshold (adjust based on sensor placement)
THRESHOLD = 5
```

### Deploying Sensor Code

1. **Flash CircuitPython** to your nRF52840 Bluefruit board
2. **Install CircuitPython libraries** following the guide at: [Feather Sense CircuitPython Libraries](https://learn.adafruit.com/adafruit-feather-sense/feather-sense-circuitpython-libraries)
3. **Upload `code.py`** from the appropriate folder:
   - Use `BLE-Sensor-1/code.py` for Parking Spot 1
   - Use `BLE-Sensor-2/code.py` for Parking Spot 2
4. The code will run automatically once uploaded to the board

**Note:** Each sensor folder contains a pre-configured `code.py` with the appropriate service UUID matching the configuration in `main.py`.

## Usage

1. **Flash MicroPython** to your ESP32 Huzzah Fruitboard

2. **Upload files** to the ESP32:
   - `main.py`
   - `boot.py`
   - `lib/` directory with all libraries

3. **Configure** Wi-Fi and MQTT credentials in `main.py`

4. **Deploy sensor code** to nRF52840 boards:
   - Flash CircuitPython to each nRF52840 board
   - Install required CircuitPython libraries (see [Feather Sense CircuitPython Libraries](https://learn.adafruit.com/adafruit-feather-sense/feather-sense-circuitpython-libraries))
   - Upload `code.py` from `BLE-Sensor-1/` folder to Sensor 1 board
   - Upload `code.py` from `BLE-Sensor-2/` folder to Sensor 2 board

5. **Power on** the ESP32 and sensors

6. **Monitor** MQTT topics to receive parking status updates

## MQTT Topics

The system publishes to the following MQTT topics:

- `parking/spot1/status` - Status updates for parking spot 1
- `parking/spot2/status` - Status updates for parking spot 2
- Additional topics for each configured parking spot

### Message Format

```json
{
  "spot": "spot1",
  "status": 1
}
```

Where:
- `spot`: Parking spot identifier (e.g., "spot1", "spot2")
- `status`: `1` = Occupied, `0` = Free

## Features

- ✅ Multi-sensor BLE connectivity
- ✅ Automatic device discovery and connection
- ✅ Real-time parking status monitoring
- ✅ MQTT cloud integration
- ✅ Robust error handling and reconnection
- ✅ Async BLE operations for efficient resource usage
- ✅ Thread-safe status queue for MQTT publishing

## Troubleshooting

### Wi-Fi Connection Issues
- Verify SSID and password are correct
- Check Wi-Fi signal strength
- Ensure 2.4GHz Wi-Fi is available (ESP32 doesn't support 5GHz)

### BLE Connection Issues
- Verify sensor service UUIDs match the configuration in both `main.py` and the `code.py` files in `BLE-Sensor-1/` and `BLE-Sensor-2/` folders
- Check that sensors are powered on and advertising (NeoPixel should be lit)
- Ensure sensors are within BLE range (~10 meters)
- Verify CircuitPython is properly flashed on nRF52840 boards
- Check that APDS9960 sensor is properly connected via I2C

### MQTT Connection Issues
- Verify broker address, port, username, and password
- Check SSL/TLS certificate requirements
- Ensure internet connectivity is available

## Future Enhancements

- [ ] Add OLED display support for local status display
- [ ] Implement BLE security/pairing
- [ ] Add battery level monitoring for sensors
- [ ] Implement sensor calibration features
- [ ] Add web dashboard for parking monitoring
- [ ] Support for more parking spots

## License

This project is part of an academic/research project. Please refer to your institution's guidelines for usage and distribution.

## Author

University of Jordan - Masters in Embedded Programming

## References

- [MicroPython Documentation](https://docs.micropython.org/)
- [CircuitPython Documentation](https://docs.circuitpython.org/)
- [ESP32 Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
- [Adafruit Feather nRF52840 Sense](https://learn.adafruit.com/adafruit-feather-sense)
- [Adafruit ESP32 Huzzah](https://learn.adafruit.com/adafruit-huzzah32-esp32-feather)
- [APDS9960 Sensor Guide](https://learn.adafruit.com/adafruit-apds9960-breakout)
- [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/)


