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
    'Anger': (255, 0, 0),        # red
    'Calmness': (0, 255, 0),     # green
    'Embarrassment': (255, 255, 0), # yellow
    'Excitement': (255, 128, 0),  # orange
    'Romance': (255, 0, 255),     # pink
    'Sadness': (0, 0, 255)        # blue
}

from led_controller import LEDController

# Setup tkinter for the virtual LED
root = tk.Tk()
root.title("Virtual LED")
canvas = tk.Canvas(root, width=200, height=200)
canvas.pack()
virtual_led = canvas.create_oval(50, 50, 150, 150, fill="white")
led_controller = LEDController(canvas, is_virtual=True)
led_controller.virtual_led = virtual_led  # Assign the virtual LED object to the controller

# Label for displaying the emotion name
emotion_label = tk.Label(root, text="", font=("Helvetica", 14))
emotion_label.pack()

def interpolate_color(start_color, end_color, step, total_steps):
    delta = [(ec - sc) / total_steps for sc, ec in zip(start_color, end_color)]
    return [int(sc + delta[i] * step) for i, sc in enumerate(start_color)]

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

async def update_virtual_led(target_color, emotion_name):
    current_color = canvas.itemcget(virtual_led, "fill")
    current_color = root.winfo_rgb(current_color)  # Get RGB values of current color
    current_color = (current_color[0] // 256, current_color[1] // 256, current_color[2] // 256)
    
    steps = 50  # Number of steps in the transition
    for step in range(steps):
        new_color = interpolate_color(current_color, target_color, step, steps)
        canvas.itemconfig(virtual_led, fill=rgb_to_hex(new_color))
        emotion_label.config(text=emotion_name)
        root.update()
        await asyncio.sleep(0.05)  # Wait a bit before next update

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
                    # Update the virtual LED color smoothly and set the emotion name
                    await led_controller.update_led(emotion_colors[max_emotion_name])
                    emotion_label.config(text=max_emotion_name)

        except websockets.exceptions.ConnectionClosedError:
            print("Connection was closed unexpectedly. Trying to reconnect in 5 seconds...")
            await asyncio.sleep(3)

# Function to run asyncio event loop tasks from Tkinter's event loop
def run_asyncio_tasks():
    try:
        loop.call_soon(asyncio.ensure_future, main())
        loop.run_forever()
    except RuntimeError as e:
        print("Asyncio loop stopped: ", e)

# Create an asyncio event loop
loop = asyncio.get_event_loop()

# Schedule the run_asyncio_tasks function to be called by Tkinter's event loop
root.after(100, run_asyncio_tasks)

# Start the Tkinter mainloop in the main thread
root.mainloop()
