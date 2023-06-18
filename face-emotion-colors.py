from gpiozero import RGBLED
from time import sleep
import colorsys
import math

# define LED
led = RGBLED(14, 15, 18, active_high=False)

# define colors corresponding to each emotion (in RGB format)
emotion_colors = {
    'Anger': (1,0,0),         # red
    'Calmness': (0,1,0),     # green
    'Embarrassment': (1,1,0), # yellow
    'Excitement': (1,0.5,0),  # orange
    'Romance': (1,0,1),       # pink
    'Sadness': (0,0,1)        # blue
}

emotion_names = ['Anger', 'Calmness', 'Embarrassment', 'Excitement', 'Romance', 'Sadness']
emotion_id = [4, 9, 22, 26, 38, 39]

# these values will come from your Hume API interaction
# emotion_values = [emotions[i]['score'] for i in emotion_id]
emotion_values = [0.02801927875723773, 0.0013877300079911947, 0.16309189796447754, 0.17014056444185105, 0.01567588746547699, 0.004104795400053263]

# normalize the emotion values so they sum to 1
sum_emotion_values = sum(emotion_values)
normalized_emotion_values = [x/sum_emotion_values for x in emotion_values]

# calculate the new LED color as a weighted sum of the emotion colors
led_color = [0, 0, 0]
for name, value in zip(emotion_names, normalized_emotion_values):
    for i in range(3):
        led_color[i] += emotion_colors[name][i] * value

# apply the new color to the LED
led.color = tuple(led_color)

# here, we create a pulsing effect by smoothly changing the lightness in the HLS color space
for i in range(100):
    # convert RGB to HLS, change the lightness, then convert back to RGB
    h, l, s = colorsys.rgb_to_hls(*led.color)
    l = 0.5 + 0.5 * math.sin(2 * math.pi * i / 100)
    led.color = colorsys.hls_to_rgb(h, l, s)
    sleep(0.03)