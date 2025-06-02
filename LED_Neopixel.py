import time
import board
import neopixel

# Constants
LED_COUNT = 7       # Number of NeoPixels
LED_PIN = board.D18 # GPIO18 (physical pin 12)

LED_BRIGHTNESS = 0.2
LED_ORDER = neopixel.GRB  # Adjusts LEDs

pixels = neopixel.NeoPixel(
    LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS,
    auto_write=False, pixel_order=LED_ORDER
)

def color_wipe(color, delay=0.1):
    for i in range(LED_COUNT):
        pixels[i] = color
        pixels.show()
        time.sleep(delay)

def rainbow_cycle(wait=0.05):
    for j in range(255):
        for i in range(LED_COUNT):
            rc_index = (i * 256 // LED_COUNT) + j
            pixels[i] = wheel(rc_index & 255)
        pixels.show()
        time.sleep(wait)

def wheel(pos):
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    else:
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)

try:
    print("Starting LED cycle. Press Ctrl+C to stop.")
    while True:
        color_wipe((255, 0, 0))  # Red
        color_wipe((0, 255, 0))  # Green
        color_wipe((0, 0, 255))  # Blue
        rainbow_cycle()

except KeyboardInterrupt:
    print("\nExiting and turning off LEDs.")
    pixels.fill((0, 0, 0))
    pixels.show()
