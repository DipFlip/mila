import asyncio
import sounddevice as sd
import soundfile as sf
import base64
import websockets.exceptions
import numpy as np
import collections
import sys
import time
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

# Audio recording parameters
SAMPLERATE = 16000  # Hertz
CHANNELS = 1
WINDOW_DURATION = 3  # seconds: The duration of audio to analyze
STEP_DURATION = 1    # seconds: How often to analyze a new window
WINDOW_SAMPLES = SAMPLERATE * WINDOW_DURATION
FILENAME = 'output_chunk.wav' # Filename for temporary audio chunks

# Global circular buffer for audio
audio_buffer = collections.deque(maxlen=WINDOW_SAMPLES)

# Callback function for the audio stream
def stream_audio_callback(indata, frames, time_info, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    audio_buffer.extend(indata.flatten())

# Function to encode audio (base64 encoding)
def encode_audio(filename_to_encode): # Renamed parameter for clarity
    with open(filename_to_encode, 'rb') as audio_file:
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

    stream = sd.InputStream(
        samplerate=SAMPLERATE,
        channels=CHANNELS,
        callback=stream_audio_callback,
        blocksize=int(SAMPLERATE * 0.1)  # Smaller blocks for faster buffer fill
    )

    try:
        stream.start()
        print("Audio stream started.")
        print(f"Buffering initial {WINDOW_DURATION} seconds of audio...")

        # Wait for the buffer to fill initially
        while len(audio_buffer) < WINDOW_SAMPLES:
            await asyncio.sleep(0.1)
        print("Initial audio buffer filled. Starting analysis loop.")

        last_analysis_start_time = time.monotonic() # Initialize before the loop

        while True:
            try:
                async with client.connect([burst_config, prosody_config]) as socket:
                    print("Successfully connected to Hume API.")
                    last_analysis_start_time = time.monotonic() # Reset for each new connection cycle
                    while True:
                        loop_start_time = time.monotonic()
                        
                        # Calculate time to sleep to maintain STEP_DURATION interval
                        # This accounts for the processing time of the previous iteration.
                        # On the very first iteration of this inner loop, time_since_last_analysis might be large
                        # if connection took time, but subsequent ones will be anchored by STEP_DURATION.
                        time_since_last_analysis = loop_start_time - last_analysis_start_time
                        sleep_needed = STEP_DURATION - time_since_last_analysis
                        
                        if sleep_needed > 0:
                            await asyncio.sleep(sleep_needed)
                        
                        # Update last_analysis_start_time for the *next* iteration's calculation
                        # It marks the effective start of this processing window.
                        last_analysis_start_time = time.monotonic() # This is the true start for this cycle
                        current_cycle_log_time_ref = last_analysis_start_time

                        if len(audio_buffer) < WINDOW_SAMPLES:
                            print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] Waiting for more audio data...")
                            await asyncio.sleep(0.1) 
                            last_analysis_start_time = time.monotonic() # Reset if we had to wait extra
                            continue
                        
                        current_audio_window = np.array(list(audio_buffer))
                        sf.write(FILENAME, current_audio_window, SAMPLERATE)
                        # print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] Audio chunk saved.")
                        
                        encoded_audio = encode_audio(FILENAME)
                        print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] Audio encoded. Sending to Hume...")
                        
                        hume_send_time = time.monotonic()
                        await socket.reset_stream()
                        result = await socket.send_bytes(encoded_audio)
                        hume_receive_time = time.monotonic()
                        print(f"[{hume_receive_time - current_cycle_log_time_ref:.3f}s] Received response from Hume. API call took: {hume_receive_time - hume_send_time:.3f}s.")

                        if 'prosody' not in result or 'predictions' not in result['prosody'] or not result['prosody']['predictions']:
                            print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] No prosody predictions.")
                            continue
                        
                        emotions = result['prosody']['predictions'][0]['emotions']
                        
                        relevant_emotions_config = [
                            ('Anger', 4, emotion_colors['Anger']),
                            ('Calmness', 9, emotion_colors['Calmness']),
                            ('Embarrassment', 22, emotion_colors['Embarrassment']),
                            ('Excitement', 26, emotion_colors['Excitement']),
                            ('Romance', 38, emotion_colors['Romance']),
                            ('Sadness', 39, emotion_colors['Sadness'])
                        ]

                        emotion_bar_data = []
                        all_scores_for_max_check = []

                        for name, hume_index, color_rgb in relevant_emotions_config:
                            score = 0.0
                            matching_emotion = next((e for e in emotions if e['name'].lower() == name.lower()), None)
                            if matching_emotion:
                                score = matching_emotion['score']
                            else:
                                if hume_index < len(emotions):
                                    score = emotions[hume_index]['score'] 
                                # else:
                                    # print(f"Warning: Hume index {hume_index} for {name} out of bounds.") # Less verbose
                            
                            emotion_bar_data.append((name, score, color_rgb))
                            all_scores_for_max_check.append(score)

                        if hasattr(led_controller, 'update_emotion_bars'):
                            led_controller.update_emotion_bars(emotion_bar_data)
                        
                        if all_scores_for_max_check:
                            max_emotion_score = max(all_scores_for_max_check)
                            if max_emotion_score > 0:
                                max_emotion_index = all_scores_for_max_check.index(max_emotion_score)
                                max_emotion_name, _, max_emotion_color = relevant_emotions_config[max_emotion_index]
                                led_controller.set_goal_color(max_emotion_color, emotion_name=max_emotion_name)
                                print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] Dominant Emotion for LED: {max_emotion_name} ({max_emotion_score:.3f})")
                            # else:
                                # print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] No dominant emotion above threshold.")
                        # else:
                            # print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] No scores available.")

                        # The dynamic sleep is now at the beginning of the loop iteration,
                        # ensuring the *start* of each cycle is STEP_DURATION apart.

            except websockets.exceptions.ConnectionClosedError:
                print("Hume connection closed. Reconnecting in 3 seconds...")
                await asyncio.sleep(3)
            except Exception as e:
                print(f"An error occurred in the main processing loop: {e}")
                print("Attempting to reset connection in 5 seconds...")
                await asyncio.sleep(5)
    
    finally:
        print("Stopping audio stream...")
        stream.stop()
        stream.close()
        print("Audio stream stopped.")
        if hasattr(led_controller, 'stop_update_task'):
            await led_controller.stop_update_task()


# Run the 'main' coroutine
if __name__ == '__main__':
    if not hume_stream_client_key:
        print("Error: HUME_STREAM_CLIENT_KEY environment variable not set.")
        print("Please set it in your .env file or environment.")
    else:
        asyncio.run(main())
