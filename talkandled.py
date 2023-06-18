import asyncio
import traceback
import sounddevice as sd
import soundfile as sf
import base64
import colorsys
import math
import numpy as np
from gpiozero import RGBLED
from hume import HumeStreamClient
from hume.models.config import BurstConfig, ProsodyConfig

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

# Record audio
samplerate = 16000  # Hertz
duration = 3  # seconds
filename = 'output.wav'

# Function to encode audio (base64 encoding)
def encode_audio(filename):
    with open(filename, 'rb') as audio_file:
        return base64.b64encode(audio_file.read())

# Hume API interaction
async def main():
    client = HumeStreamClient("1Fuo6eVLpIj6ndhmC5VXllArH67eOcaSA0XLX3sHdU2SdEy5")
    burst_config = BurstConfig()
    prosody_config = ProsodyConfig()
    async with client.connect([burst_config, prosody_config]) as socket:
        while True:
            print(f"Recording for {duration} seconds...")
            myrecording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=2, blocking=True)
            print("Recording complete. Saving the audio as output.wav")
            sf.write(filename, myrecording, samplerate)
            encoded_audio = encode_audio(filename)
            await socket.reset_stream()
            result = await socket.send_bytes(encoded_audio)
            print("Received response from Hume")

            # interpret the emotion results
            if not 'predictions' in result['prosody']:
                print('no prediction')
                continue
            emotions = result['prosody']['predictions'][0]['emotions']
            emotion_id = [4, 9, 22, 26, 38, 39]
            emotion_values = [emotions[i]['score'] for i in emotion_id]
            # print emotion names and values and color
            for name, value in zip(emotion_colors.keys(), emotion_values):
                print(f"{name}: {value}")
            # normalize the emotion values so they sum to 1
            for i, v in enumerate(emotion_values):
                if v < 0.15:
                   emotion_values[i] = 0
            sum_emotion_values = np.sum(emotion_values)
            normalized_emotion_values = np.divide(emotion_values, sum_emotion_values)

            # calculate the new LED color as a weighted sum of the emotion colors
            led_color = np.zeros(3)
            for name, value in zip(emotion_colors.keys(), normalized_emotion_values):
                led_color = np.add(led_color, np.multiply(emotion_colors[name], value))

            # apply the new color to the LED
            led.color = tuple(led_color)
            
            # # here, we create a pulsing effect by smoothly changing the lightness in the HLS color space
            # for i in range(100):
            #     # convert RGB to HLS, change the lightness, then convert back to RGB
            #     h, l, s = colorsys.rgb_to_hls(*led.color)
            #     l = 0.5 + 0.5 * math.sin(2 * math.pi * i / 100)
            #     led.color = colorsys.hls_to_rgb(h, l, s)
            #     await asyncio.sleep(0.03)

# Create an event loop and run 'main'
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
