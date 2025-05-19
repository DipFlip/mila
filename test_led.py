from gpiozero import RGBLED
import time

# Set up the RGB LED (GPIO pins 14, 15, 18, active_low)
led = RGBLED(14, 15, 18, active_high=False)

try:
    print("Turning LED green...")
    led.color = (0, 1, 0)  # Green (full green, off red and blue)
    time.sleep(10)         # Keep it on for 10 seconds
finally:
    print("Turning LED off.")
    led.off() 