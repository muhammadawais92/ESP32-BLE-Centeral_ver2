import time
import board
import busio
import neopixel
import adafruit_apds9960.apds9960
from adafruit_ble import BLERadio
from adafruit_ble.services import Service
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.uuid import VendorUUID  # VendorUUID (128-bit)

# Initialize I2C for APDS9960
i2c = busio.I2C(board.SCL, board.SDA)
apds = adafruit_apds9960.apds9960.APDS9960(i2c)
apds.enable_proximity = True

# Initialize onboard NeoPixel
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

# Proximity threshold
THRESHOLD = 5

# Initialize BLE
ble = BLERadio()

# Define 128-bit UUIDs
SERVICE_UUID = VendorUUID("12345678-1234-5678-1234-56789abcdef0")
CHAR_UUID    = VendorUUID("12345678-1234-5678-1234-56789abcdef1")

# Custom BLE Service using VendorUUID
class SpotService(Service):
    uuid = SERVICE_UUID
    status = Characteristic(
        uuid=CHAR_UUID,
        properties=Characteristic.READ | Characteristic.NOTIFY,
        max_length=1
    )

# Create service instance and advertisement
spot_service = SpotService()
advertisement = ProvideServicesAdvertisement(spot_service)
ble.start_advertising(advertisement)

print("BLE advertising started...")

# Track last sent status to avoid repeated notifications
last_status = None

while True:
    if not ble.connected:
        try:
            ble.start_advertising(advertisement)
        except Exception:
            pass
    
    # Read proximity
    proximity = apds.proximity

    # Determine current status
    if proximity > THRESHOLD:
        status = 1
        pixel.fill((255, 0, 0))  # Red = occupied
    else:
        status = 0
        pixel.fill((0, 255, 0))  # Green = free

# Only update BLE characteristic if status changed
    if status != last_status:
        spot_service.status = bytes([status])
        last_status = status
        print("Proximity:", proximity, "Status changed:", status)
    else:
        print("Proximity:", proximity, "Status unchanged:", status)

    time.sleep(0.2)
