import asyncio
import sounddevice as sd
import soundfile as sf
import base64
import websockets.exceptions
import numpy as np
from hume import HumeStreamClient
from hume.models.config import BurstConfig, ProsodyConfig
import tkinter as tk

# Define colors corresponding to each emotion (in RGB format)
emotion_colors = {
    'Anger': "red",
    'Calmness': "green",
    'Embarrassment': "yellow",
    'Excitement': "orange",
    'Romance': "pink",
    'Sadness': "blue"
}

# Setup tkinter for the virtual LED
root = tk.Tk()
root.title("Virtual LED")
canvas = tk.Canvas(root, width=200, height=200)
canvas.pack()
virtual_led = canvas.create_oval(50, 50, 150, 150, fillw="hite")

# Label for displaying the emotion name
emotion_label = tk.Label(root, text="", font=("Helvetica", 14))
emotion_label.pack()

def update_virtual_led(color, emotion_name):
    canvas.itemconfig(virtual_led, fill=color)
    emotion_label.config(text=emotion_name)
    root.update()

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

    while True:
        try:
            async with client.connect([burst_config, prosody_config]) as socket:
                while True:
                    print(f"Recording for {duration} seconds...")
                    myrecording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, blocking=True)
                    print("Recording complete. Saving the audio as output.wav")
                    sf.write(filename, myrecording, samplerate)
                    encoded_audio = encode_audio(filename)
                    await socket.reset_stream()
                    result = await socket.send_bytes(encoded_audio)
                    print("Received response from Hume")

                    # Interpret the emotion results
                    if not 'predictions' in result['prosody']:
                        print('no prediction')
                        continue
                    emotions = result['prosody']['predictions'][0]['emotions']
                    emotion_id = [4, 9, 22, 26, 38, 39]
                    emotion_values = [emotions[i]['score'] for i in emotion_id]
                    # Print emotion names and values
                    for name, value in zip(emotion_colors.keys(), emotion_values):
                        print(f"{name}: {value}")
                    # Find the highest emotion score
                    max_emotion_value = max(emotion_values)
                    # Find the corresponding emotion name
                    max_emotion_name = list(emotion_colors.keys())[emotion_values.index(max_emotion_value)]
                    # Update the virtual LED color and emotion name
                    update_virtual_led(emotion_colors[max_emotion_name], max_emotion_name)

        except websockets.exceptions.ConnectionClosedError:
            print("Connection was closed unexpectedly. Trying to reconnect in 5 seconds...")
            await asyncio.sleep(3)

# Run the tkinter mainloop in a separate thread
import threading
threading.Thread(target=root.mainloop).start()

# Create an event loop and run 'main'
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
