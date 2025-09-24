import RPi.GPIO as GPIO
import time

# --- Setup ---
LDR_PIN = 17  # GPIO connected to DO
GPIO.setmode(GPIO.BCM)
GPIO.setup(LDR_PIN, GPIO.IN)

try:
    while True:
        if GPIO.input(LDR_PIN):
            print("Bright light detected")
        else:
            print("Dark / Low light detected")
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopping LDR monitoring...")
finally:
    GPIO.cleanup()
