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

# Define colors corresponding to each emotion (in RGB format)
emotion_colors = {
    'Anger': (255, 0, 0),        # red
    'Calmness': (0, 255, 0),     # green
    'Embarrassment': (255, 255, 0), # yellow
    'Excitement': (255, 128, 0),  # orange
    'Romance': (255, 0, 255),     # pink
    'Sadness': (0, 0, 255)        # blue
}

# Record audio
samplerate = 16000  # Hertz
duration = 3  # seconds
filename = 'output.wav'

# Function to record audio asynchronously
async def record_audio(duration, samplerate, filename):
    # Create an event to notify when recording is finished
    finished_recording = asyncio.Event()

    # Define the callback function for the InputStream
    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        sf.write(filename, indata, samplerate, format='WAV', subtype='PCM_16')
        finished_recording.set()

    # Open the InputStream with the callback
    stream = sd.InputStream(samplerate=samplerate, channels=1, callback=callback)
    with stream:
        # Clear the event in case it was previously set
        finished_recording.clear()
        # Start the stream
        stream.start()
        # Record for the specified duration
        await asyncio.sleep(duration)
        # Stop the stream after recording
        stream.stop()
        # Wait for the callback to signal that it has finished writing the file
        await finished_recording.wait()

# Function to encode audio (base64 encoding)
def encode_audio(filename):
    with open(filename, 'rb') as audio_file:
        return base64.b64encode(audio_file.read())

# Hume API interaction
async def main():
    led_controller.start_update_task()  # Start the update task inside the main coroutine
    client = HumeStreamClient("1Fuo6eVLpIj6ndhmC5VXllArH67eOcaSA0XLX3sHdU2SdEy5")
    burst_config = BurstConfig()
    prosody_config = ProsodyConfig()

    while True:
        try:
            async with client.connect([burst_config, prosody_config]) as socket:
                while True:
                    # Start recording in a non-blocking manner
                    print(f"Recording for {duration} seconds...")
                    # Start recording and wait for it to finish
                    print(f"Recording for {duration} seconds...")
                    await record_audio(duration, samplerate, filename)
                    print("Recording complete.")
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
                    led_controller.set_goal_color(emotion_colors[max_emotion_name], emotion_name=max_emotion_name)

        except websockets.exceptions.ConnectionClosedError:
            print("Connection was closed unexpectedly. Trying to reconnect in 5 seconds...")
            await asyncio.sleep(3)

# Run the 'main' coroutine
if __name__ == '__main__':
    asyncio.run(main())
