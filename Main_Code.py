import time
import numpy as np
import board
import neopixel
import RPi.GPIO as GPIO
from datetime import datetime
import adi

# --- LED Setup ---
LED_COUNT = 7
LED_PIN = board.D18
LED_BRIGHTNESS = 0.2
LED_ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS,
    auto_write=False, pixel_order=LED_ORDER
)

def flash_alert(color, flashes=3, delay=0.2):
    for _ in range(flashes):
        pixels.fill(color)
        pixels.show()
        time.sleep(delay)
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(delay)

# --- GPIO Setup for Rocker Switch ---
SWITCH_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

running = False

def toggle_execution(channel):
    global running
    running = not running
    state = "STARTED" if running else "STOPPED"
    print(f"System {state}")

GPIO.add_event_detect(SWITCH_PIN, GPIO.FALLING, callback=toggle_execution, bouncetime=500)

# --- SDR Setup (Pluto+) ---
sdr = adi.Pluto(uri="ip:192.168.2.1")
sdr.rx_lo = int(406.025e6)
sdr.sample_rate = int(1e6)
sdr.rx_rf_bandwidth = int(200e3)
sdr.gain_control_mode = "slow_attack"
sdr.rx_buffer_size = 4096

# --- KML File Setup ---
kml_file = "beacon_locations.kml"
with open(kml_file, 'w') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n')

def append_kml(lat, lon, hex_id):
    with open(kml_file, 'a') as f:
        placemark = (
            f"<Placemark><name>Beacon - {hex_id}</name>"
            f"<Point><coordinates>{lon},{lat},0</coordinates></Point>"
            "</Placemark>\n"
        )
        f.write(placemark)

# --- Main Loop ---
try:
    print("Waiting for switch to start...")
    while True:
        if running:
            samples = sdr.rx()
            signal = np.real(samples)
            if np.max(np.abs(signal)) > 0.5:
                print("406 MHz Beacon Detected!")

                # Dummy hex packet simulation
                hex_packet = 'FFFE2F970E00800127299B1E21F600657969'
                country_code = hex_packet[6:9]
                beacon_hex_id = hex_packet[9:25]
                encoded_location = hex_packet[25:]

                print(f"Country Code: {country_code}")
                print(f"Beacon Hex ID: {beacon_hex_id}")
                print(f"Encoded Location: {encoded_location}")

                # Convert location from hex (simulated)
                lat_hex = encoded_location[:8].ljust(8, '0')
                lon_hex = encoded_location[8:16].ljust(8, '0')
                lat = int(lat_hex, 16) / 1e7
                lon = int(lon_hex, 16) / 1e7

                print(f"Latitude (Decoded): {lat}")
                print(f"Longitude (Decoded): {lon}")

                append_kml(lat, lon, beacon_hex_id)
                flash_alert((0, 255, 0), flashes=5)

            else:
                print("No 406 MHz Beacon Signal")
            time.sleep(0.5)
        else:
            time.sleep(0.2)

except KeyboardInterrupt:
    print("\nShutting down...")
    with open(kml_file, 'a') as f:
        f.write('</Document></kml>\n')
    pixels.fill((0, 0, 0))
    pixels.show()
    GPIO.cleanup()
