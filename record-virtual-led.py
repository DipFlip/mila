import asyncio
import sounddevice as sd
import soundfile as sf
import base64
import websockets.exceptions
import numpy as np
import threading
from hume import HumeStreamClient
from hume.models.config import BurstConfig, ProsodyConfig
from led_controller import LEDController
import os
from dotenv import load_dotenv

load_dotenv()

led_controller = LEDController(is_virtual=True)

emotion_colors = {
    'Anger': (255, 0, 0),
    'Calmness': (0, 255, 0),
    'Embarrassment': (255, 255, 0),
    'Excitement': (255, 128, 0),
    'Romance': (255, 0, 255),
    'Sadness': (0, 0, 255)
}

samplerate = 16000  # Hertz
duration = 3  # seconds
filename = 'output.wav'

# Function to record audio in a separate thread
def thread_record_audio(duration, samplerate, filename):
    myrecording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, blocking=False)
    # await asyncio.sleep(duration)
    print("Recording complete. Saving the audio as output.wav")
    sf.write(filename, myrecording, samplerate)

async def record_audio(duration, samplerate, filename):
    loop = asyncio.get_running_loop()
    event = asyncio.Event()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        loop.call_soon_threadsafe(event.set)

    with sd.InputStream(samplerate=samplerate, channels=1, callback=callback):
        await event.wait()  # Wait until the first callback is invoked
        myrecording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1)
        await asyncio.sleep(duration)  # Wait for the duration of the recording
        sf.write(filename, myrecording, samplerate)

# Function to encode audio (base64 encoding)
def encode_audio(filename):
    with open(filename, 'rb') as audio_file:
        return base64.b64encode(audio_file.read())

load_dotenv()

# Get the HumeStreamClient key from the environment variable
hume_stream_client_key = os.getenv("HUME_STREAM_CLIENT_KEY")

# Hume API interaction
async def main():
    led_controller.start_update_task()
    client = HumeStreamClient(hume_stream_client_key)
    burst_config = BurstConfig()
    prosody_config = ProsodyConfig()

    while True:
        try:
            async with client.connect([burst_config, prosody_config]) as socket:
                while True:
                    print(f"Recording for {duration} seconds...")
                    # Create and start the recording thread
                    # recording_thread = threading.Thread(target=thread_record_audio, args=(duration, samplerate, filename))
                    # recording_thread.start()
                    await record_audio(duration, samplerate, filename)

                    # Join the thread to ensure it completes
                    # recording_thread.join()

                    encoded_audio = encode_audio(filename)
                    await socket.reset_stream()
                    result = await socket.send_bytes(encoded_audio)
                    print("Received response from Hume")

                    if not 'predictions' in result['prosody']:
                        print('no prediction')
                        continue
                    emotions = result['prosody']['predictions'][0]['emotions']
                    
                    # Define the emotions we are interested in and their corresponding indices in the Hume API response
                    # Mapping: Name, Hume Index, Display Color (RGB)
                    # Note: Using the same colors as defined in `emotion_colors` for consistency
                    relevant_emotions_config = [
                        ('Anger', 4, emotion_colors['Anger']),
                        ('Calmness', 9, emotion_colors['Calmness']),
                        ('Embarrassment', 22, emotion_colors['Embarrassment']),
                        ('Excitement', 26, emotion_colors['Excitement']),
                        ('Romance', 38, emotion_colors['Romance']),
                        ('Sadness', 39, emotion_colors['Sadness'])
                        # Add more emotions here if needed, following the pattern: (Name, HumeIndex, RGB_Color)
                    ]

                    emotion_bar_data = []
                    all_scores_for_max_check = [] # To find the max emotion for the main LED

                    print("\n--- Hume API Response Processed ---")
                    for name, hume_index, color_rgb in relevant_emotions_config:
                        score = 0.0
                        if hume_index < len(emotions):
                            score = emotions[hume_index]['score']
                        else:
                            print(f"Warning: Hume index {hume_index} for {name} is out of bounds.")
                        
                        emotion_bar_data.append((name, score, color_rgb))
                        all_scores_for_max_check.append(score)
                        # print(f"{name}: {score:.3f}") # Replaced by graphical bars

                    # Update the graphical emotion bars
                    if hasattr(led_controller, 'update_emotion_bars'):
                        led_controller.update_emotion_bars(emotion_bar_data)
                    
                    # Determine the dominant emotion for the main LED
                    if all_scores_for_max_check:
                        max_emotion_score = max(all_scores_for_max_check)
                        max_emotion_index = all_scores_for_max_check.index(max_emotion_score)
                        max_emotion_name, _, max_emotion_color = relevant_emotions_config[max_emotion_index]
                        
                        print(f"Dominant Emotion for LED: {max_emotion_name} ({max_emotion_score:.3f})")
                        led_controller.set_goal_color(max_emotion_color, emotion_name=max_emotion_name)
                    else:
                        print("No scores available to determine dominant emotion.")
                        # Optionally, set a default color or state for the LED
                        # led_controller.set_goal_color((100, 100, 100), emotion_name="Neutral")

                    # The old text-based printing loop has been removed.
                    # The max emotion logic for the main LED is now integrated above.

        except websockets.exceptions.ConnectionClosedError:
            print("Connection was closed unexpectedly. Trying to reconnect in 5 seconds...")
            await asyncio.sleep(3)

# Run the 'main' coroutine
if __name__ == '__main__':
    asyncio.run(main())
