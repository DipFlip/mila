import asyncio
import sounddevice as sd
import soundfile as sf
import base64
import websockets.exceptions
import numpy as np
from hume import HumeStreamClient
from hume.models.config import BurstConfig, ProsodyConfig
from led_controller import LEDController
led_controller = LEDController(is_virtual=True)


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
