# Mila - give color to your authentic voice
Repo for the [Mila Team](https://devpost.com/software/qw-qox4r8) project during the Berkeley AI Hackathon 2023

### Installation
1. Install prerequisites
	-  For linux:
		- `sudo apt-get install portaudio19-dev ffmpeg`
	-  For Windows
		- Download a precompiled version of ffmpeg from the official ffmpeg [website](https://ffmpeg.org/download.html#build-windows). After downloading and extracting the files, you'll need to add the bin directory to your system's PATH.
	- For Mac
		- ```brew install portaudio ffmpeg```
2. Create a conda environment and install dependencies with
```bash
conda create --name mila python ipython jupyter
conda activate mila
pip install -r requirements.txt

```
3. Set the `HUME_STREAM_CLIENT_KEY` variable in `.env` to your Hume API key. 

### Running virtual mila (without hardware)
You can test mila without an actual device with the following command:
```bash
python record-virtual-led.py
```
A virtual LED will show on the display, as the physical one would on a real Mila device.
### Running physical mila
Set your raspberry pi to run on boot:
```bash
python record-on-pi-zero.py
```