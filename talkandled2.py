async def main():
    client = HumeStreamClient("1Fuo6eVLpIj6ndhmC5VXllArH67eOcaSA0XLX3sHdU2SdEy5")
    burst_config = BurstConfig()
    prosody_config = ProsodyConfig()

    while True:
        try:
            async with client.connect([burst_config, prosody_config]) as socket:
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
                # print emotion names and values
                for name, value in zip(emotion_colors.keys(), emotion_values):
                    print(f"{name}: {value}")
                # find the highest emotion score
                max_emotion_value = max(emotion_values)
                # find the corresponding emotion name
                max_emotion_name = list(emotion_colors.keys())[emotion_values.index(max_emotion_value)]
                # set the LED color to the color of the emotion with the highest score
                led.color = emotion_colors[max_emotion_name]

        except websockets.exceptions.ConnectionClosedError:
            print("Connection was closed unexpectedly. Trying again...")