import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
SWITCH_PIN = 17
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

running = False

def toggle_execution(channel):
    global running
    running = not running
    if running:
        print("Code started")
    else:
        print("Code stopped")

GPIO.add_event_detect(SWITCH_PIN, GPIO.FALLING, callback=toggle_execution, bouncetime=300)

try:
    while True:
        if running:
            # Main logic here
            print("Running loop...")
        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()
