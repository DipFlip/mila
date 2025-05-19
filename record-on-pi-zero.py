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
from gpiozero import RGBLED
import os
from dotenv import load_dotenv

load_dotenv()

# Print available audio devices
print("Available audio devices:")
print(sd.query_devices())
print("-------------------------")

# Query and print capabilities of device 1 (USB PnP Sound Device)
try:
    device_info = sd.query_devices(1, 'input')
    print(f"Capabilities of 'USB PnP Sound Device' (device 1):")
    print(f"  Default sample rate: {device_info['default_samplerate']} Hz")
    # Note: sd.query_devices doesn't always list all supported sample rates directly.
    # For more detailed info, 'arecord --dump-hw-params -D hw:1,0' can be used in terminal.
except Exception as e:
    print(f"Could not query device 1: {e}")
print("-------------------------")

# define LED for Raspberry Pi
led = RGBLED(14, 15, 18, active_high=False)
led_controller = LEDController(led, is_virtual=False)

# Define colors corresponding to each emotion (in RGB format)
emotion_colors = {
    'Anger': (255, 0, 0),
    'Calmness': (0, 255, 0),
    'Embarrassment': (255, 255, 0),
    'Excitement': (255, 128, 0),
    'Romance': (255, 0, 255),
    'Sadness': (0, 0, 255)
}

# Audio recording parameters - aligned with virtual LED script
SAMPLERATE = 16000  # Hertz
CHANNELS = 1
WINDOW_DURATION = 3  # seconds: The duration of audio to analyze
STEP_DURATION = 1    # seconds: How often to analyze a new window
WINDOW_SAMPLES = SAMPLERATE * WINDOW_DURATION
FILENAME = 'output_chunk_pi.wav' # Filename for temporary audio chunks (can be different if needed)

EMOTION_THRESHOLD = 0.1 # Aligned with virtual LED script
WHITE_COLOR = (255, 255, 255) # Aligned with virtual LED script

# Global circular buffer for audio - from virtual LED script
audio_buffer = collections.deque(maxlen=WINDOW_SAMPLES)

# Callback function for the audio stream - from virtual LED script
def stream_audio_callback(indata, frames, time_info, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    audio_buffer.extend(indata.flatten())

# Function to encode audio (base64 encoding)
def encode_audio(filename_to_encode): # Renamed parameter for clarity
    with open(filename_to_encode, 'rb') as audio_file:
        return base64.b64encode(audio_file.read())

# Get the HumeStreamClient key from the environment variable
hume_stream_client_key = os.getenv("HUME_STREAM_CLIENT_KEY")

# Hume API interaction - structure adapted from virtual LED script
async def main():
    led_controller.start_update_task()
    client = HumeStreamClient(hume_stream_client_key)
    burst_config = BurstConfig()
    prosody_config = ProsodyConfig()

    # Audio stream setup - from virtual LED script
    try:
        stream = sd.InputStream(
            device=1, # Explicitly select the USB microphone by its index
            samplerate=SAMPLERATE,
            channels=CHANNELS,
            callback=stream_audio_callback,
            blocksize=int(SAMPLERATE * 0.1)  # Smaller blocks for faster buffer fill
        )
    except sd.PortAudioError as e:
        if e.args[1] == sd.PaErrorCode.paInvalidSampleRate:
            print(f"Error: The configured SAMPLERATE ({SAMPLERATE} Hz) is not supported by the microphone.")
            print(f"Try changing SAMPLERATE in the script to the device's default sample rate (see above) or another supported rate.")
        else:
            print(f"PortAudioError opening stream: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error setting up audio stream: {e}")
        sys.exit(1)

    try:
        stream.start()
        print("Audio stream started.")
        print(f"Buffering initial {WINDOW_DURATION} seconds of audio...")

        while len(audio_buffer) < WINDOW_SAMPLES:
            await asyncio.sleep(0.1)
        print("Initial audio buffer filled. Starting analysis loop.")

        last_analysis_start_time = time.monotonic()

        while True:
            try:
                async with client.connect([burst_config, prosody_config]) as socket:
                    print("Successfully connected to Hume API.")
                    last_analysis_start_time = time.monotonic()
                    while True:
                        loop_start_time = time.monotonic()
                        
                        time_since_last_analysis = loop_start_time - last_analysis_start_time
                        sleep_needed = STEP_DURATION - time_since_last_analysis
                        
                        if sleep_needed > 0:
                            await asyncio.sleep(sleep_needed)
                        
                        last_analysis_start_time = time.monotonic()
                        current_cycle_log_time_ref = last_analysis_start_time

                        if len(audio_buffer) < WINDOW_SAMPLES:
                            print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] Waiting for more audio data...")
                            await asyncio.sleep(0.1)
                            last_analysis_start_time = time.monotonic() # Reset if we had to wait
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
                            led_controller.set_goal_color(WHITE_COLOR, emotion_name="Neutral (No Prediction)") # Set to white on no prediction
                            continue
                        
                        emotions = result['prosody']['predictions'][0]['emotions']
                        
                        # Using relevant_emotions_config from virtual LED for consistency
                        relevant_emotions_config = [
                            ('Anger', 4, emotion_colors['Anger']),
                            ('Calmness', 9, emotion_colors['Calmness']),
                            ('Embarrassment', 22, emotion_colors['Embarrassment']),
                            ('Excitement', 26, emotion_colors['Excitement']),
                            ('Romance', 38, emotion_colors['Romance']),
                            ('Sadness', 39, emotion_colors['Sadness'])
                        ]

                        emotion_scores_for_led = [] # Renamed from emotion_bar_data for clarity

                        for name, hume_index, color_rgb in relevant_emotions_config:
                            score = 0.0
                            # Attempt to find by name first, then fall back to index if necessary
                            matching_emotion = next((e for e in emotions if e['name'].lower() == name.lower()), None)
                            if matching_emotion:
                                score = matching_emotion['score']
                            else:
                                # Fallback to index if name not found (Hume might change name casing or exact names)
                                if hume_index < len(emotions):
                                    score = emotions[hume_index]['score']
                                # else:
                                    # print(f"Warning: Hume index {hume_index} for {name} out of bounds for Pi.")
                            
                            emotion_scores_for_led.append({'name': name, 'score': score, 'color': color_rgb})

                        # New logic with thresholding and blinking - from virtual LED script
                        strong_emotions = []
                        for data in emotion_scores_for_led:
                            if data['score'] >= EMOTION_THRESHOLD:
                                strong_emotions.append(data)
                        
                        strong_emotions.sort(key=lambda x: x['score'], reverse=True)

                        if not strong_emotions:
                            led_controller.set_goal_color(WHITE_COLOR, emotion_name="Neutral")
                            print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] No emotions above threshold {EMOTION_THRESHOLD}. Setting LED to White.")
                        elif len(strong_emotions) == 1:
                            emotion = strong_emotions[0]
                            led_controller.set_goal_color(emotion['color'], emotion_name=emotion['name'])
                            print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] Dominant Emotion for LED: {emotion['name']} ({emotion['score']:.3f})")
                        else: # Two or more emotions above threshold
                            emotion1 = strong_emotions[0]
                            emotion2 = strong_emotions[1]
                            # Physical LED controller might not have set_blinking_colors if not updated
                            # However, the shared led_controller.py should have it
                            if hasattr(led_controller, 'set_blinking_colors'):
                                led_controller.set_blinking_colors(
                                    emotion1['color'], 
                                    emotion2['color'],
                                    emotion_name_one=emotion1['name'],
                                    emotion_name_two=emotion2['name']
                                )
                                print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] Blinking between: {emotion1['name']} ({emotion1['score']:.3f}) and {emotion2['name']} ({emotion2['score']:.3f})")
                            else: # Fallback if method somehow doesn't exist
                                led_controller.set_goal_color(emotion1['color'], emotion_name=emotion1['name'])
                                print(f"[{time.monotonic() - current_cycle_log_time_ref:.3f}s] (Fallback) Dominant Emotion for LED: {emotion1['name']} ({emotion1['score']:.3f}) - Blinking not available.")
            
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
        if hasattr(led_controller, 'stop_update_task'): # Check if method exists
            await led_controller.stop_update_task()


# Run the 'main' coroutine - aligned with virtual LED script
if __name__ == '__main__':
    if not hume_stream_client_key:
        print("Error: HUME_STREAM_CLIENT_KEY environment variable not set.")
        print("Please set it in your .env file or environment.")
    else:
        asyncio.run(main())
