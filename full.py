# ===========================================
# PART 5: Main Execution Loop with GPIO Switch & LED Feedback
# ===========================================

import RPi.GPIO as GPIO
import board
import neopixel
import time

# LED Setup
LED_COUNT = 7
LED_PIN = board.D18
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=0.3, auto_write=False)

def flash_green():
    pixels.fill((0, 255, 0))
    pixels.show()
    time.sleep(1)
    pixels.fill((0, 0, 0))
    pixels.show()

# GPIO Setup
SWITCH_PIN = 23  # GPIO 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# KML Log
kml_path = init_kml_log()

# Main Loop
try:
    print("SAFE-T System Ready. Flip switch to start.")
    while True:
        if GPIO.input(SWITCH_PIN) == GPIO.LOW:
            print("📡 STARTING SIGNAL MONITORING...")
            time.sleep(1)  # debounce delay

            while GPIO.input(SWITCH_PIN) == GPIO.LOW:
                raw_samples = sdr.rx()
                bits = bpsk_demodulate(raw_samples, samples_per_symbol=20)
                
                if len(bits) >= 144:
                    try:
                        beacon_info = extract_beacon_fields(bits)
                        display_beacon_info(beacon_info)
                        log_beacon_to_kml(kml_path, beacon_info)
                        flash_green()
                        time.sleep(15)  # SARSAT beacon transmits every 15 seconds
                    except Exception as e:
                        print("⚠️ Error decoding beacon:", e)
                else:
                    print("...Listening, no valid packet detected")
                time.sleep(0.5)

        time.sleep(0.1)  # idle loop delay

except KeyboardInterrupt:
    print("\n🛑 Exiting... Cleaning up.")
    finalize_kml_log(kml_path)
    GPIO.cleanup()
    pixels.fill((0, 0, 0))
    pixels.show()
