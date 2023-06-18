import asyncio
import traceback
import sounddevice as sd
from scipy.io.wavfile import write
import base64

from hume import HumeStreamClient
from hume.models.config import BurstConfig, ProsodyConfig

# Record audio
samplerate = 44100  # Hertz
duration = 4  # seconds
filename = 'output.wav'
print(f"Recording for {duration} seconds...")
myrecording = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=2, blocking=True)
print("Recording complete. Saving the audio as output.wav")
write(filename, samplerate, myrecording)

# Function to encode audio (base64 encoding)
def encode_audio(filename):
    with open(filename, 'rb') as audio_file:
        return base64.b64encode(audio_file.read())

# Hume API interaction
async def main():
    try:
        client = HumeStreamClient("1Fuo6eVLpIj6ndhmC5VXllArH67eOcaSA0XLX3sHdU2SdEy5")
        burst_config = BurstConfig()
        prosody_config = ProsodyConfig()
        async with client.connect([burst_config, prosody_config]) as socket:
            encoded_audio = encode_audio(filename)
            await socket.reset_stream()
            result = await socket.send_bytes(encoded_audio)
            print("Received response from Hume")
            return result  # return the result
    except Exception:
        print(traceback.format_exc())

# Create an event loop and run 'main'
loop = asyncio.get_event_loop()
result = loop.run_until_complete(main())

print(result)
