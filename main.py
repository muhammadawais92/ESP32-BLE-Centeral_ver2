import network
import time
import ntptime
import json
import uasyncio as asyncio
import aioble
import bluetooth
import gc
import _thread
from umqtt.robust import MQTTClient


# Wifi credentials

WIFI_SSID = "Redmi Note 10"
WIFI_PASSWORD = "01130113"


# HiveMQ Cloud credentials

MQTT_BROKER = "bf05acb5ee194085a7731e5ca603fe6c.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_CLIENT_ID = "esp32_parking"
MQTT_USER = "aawaiss011"
MQTT_PASSWORD = "Awais0113"
TOPIC_PREFIX = "parking/"

# France timezone (UTC+1 winter, UTC+2 summer)
#TIMEZONE_OFFSET = 1  # adjust to 2 for DST


# BLE UUIDs

DEVICE_SERVICES = {
    bluetooth.UUID("12345678-1234-5678-1234-56789abcdef0"): "spot1",
    bluetooth.UUID("87654321-4321-5678-4321-0fedcba98765"): "spot2"
}
CHAR_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789abcdef1")
connected_devices = {}

# status queue
status_queue = []

def queue_put(item):
    status_queue.append(item)
    print(f"Queue added: {item} | size={len(status_queue)}")

def queue_get():
    while len(status_queue) == 0:
        time.sleep(0.1)
    item = status_queue.pop(0)
    print(f"Queue got: {item} | size={len(status_queue)}")
    return item


# Wi-Fi connection handling
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            time.sleep(0.5)
            timeout -= 1
        print()
    if wlan.isconnected():
        print("Wi-Fi connected:", wlan.ifconfig())

# Sync time via NTP
#         try:
#             ntptime.settime()  # sets ESP32 RTC to UTC
#             print("Time synchronized via NTP")
#         except Exception as e:
#             print("NTP sync failed:", e)
            
        return True
    else:
        print("Wi-Fi connection failed")
        return False


# MQTT Worker (runs in separate thread)

ssl_params = {
    "server_hostname": MQTT_BROKER
}
def mqtt_worker():
    try:
        client = MQTTClient(
            client_id=MQTT_CLIENT_ID,
            server=MQTT_BROKER,
            port=MQTT_PORT,
            user=MQTT_USER,
            password=MQTT_PASSWORD,
            ssl=True,
            ssl_params=ssl_params,
        )
        client.connect()
        print("MQTT connected (TLS)")
    except Exception as e:
        print("MQTT connect failed:", e)
        return

    while True:
        spot, status = queue_get()
        
        # Get current time
#         t = time.localtime(time.time() + TIMEZONE_OFFSET * 3600)
#         timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
#             t[0], t[1], t[2], t[3], t[4], t[5]
#         )
#         
        
        # Create MQTT topic
        topic = f"{TOPIC_PREFIX}{spot}/status"
        payload = '{"spot":"%s","status":%d}' % (spot, status)

#         # JSON payload with timestamp
#         payload = json.dumps({
#             "spot": spot,
#             "status": status,
#             "timestamp": timestamp
#         })
        try:
            client.publish(topic, payload)
            print(f"Published: {payload} to {topic}")
        except Exception as e:
            print("MQTT publish error:", e)
        finally:
            gc.collect()

# BLE Device Handler (async)
async def handle_device(spot_label, device, service_uuid):
    addr_str = ":".join("{:02X}".format(b) for b in device.addr)
    print(f"Connecting to {spot_label} ({addr_str})...")
    try:
        conn = await device.connect()
        async with conn:
            svc = await conn.service(service_uuid)
            char = await svc.characteristic(CHAR_UUID)
            await char.subscribe(notify=True)
            print(f"{spot_label} subscribed")
            while True:
                try:
                    val = await char.notified(timeout_ms=1000)
                    if val:
                        status = val[0]
                        print(f"{spot_label} status: {'Occupied' if status else 'Free'}")
                        queue_put((spot_label, status))
                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    print(f"{spot_label} notify error:", e)
                    break
    except Exception as e:
        print(f"{spot_label} connection failed:", e)
    finally:
        print(f"{spot_label} disconnected")
        if spot_label in connected_devices:
            del connected_devices[spot_label]

# BLE Worker (async)

async def ble_worker():
    while True:
        if len(connected_devices) < len(DEVICE_SERVICES):
            print("Scanning BLE devices...")
            try:
                async with aioble.scan(duration_ms=5000, interval_us=50000, window_us=30000, active=True) as scanner:
                    async for res in scanner:
                        for svc_uuid in res.services():
                            if svc_uuid in DEVICE_SERVICES:
                                spot_label = DEVICE_SERVICES[svc_uuid]
                                if spot_label not in connected_devices:
                                    connected_devices[spot_label] = res.device
                                    # start device handler as independent task
                                    asyncio.create_task(handle_device(spot_label, res.device, svc_uuid))
            except Exception as e:
                print("BLE scan error:", e)
        await asyncio.sleep(2)

async def main():
    if not connect_wifi():
        return

# Start MQTT worker in separate thread
    _thread.start_new_thread(mqtt_worker, ())

# Start BLE worker (async)
    await ble_worker()

asyncio.run(main())

