# Mila - give color to your authentic voice
Repo for the Mila Team project during the Berkeley AI Hackathon 2023

1. Install prerequisites
	-  For linux:
		- `sudo apt-get install portaudio19-dev ffmpeg`
		- `pip install sounddevice`
	-  For Windows
		- Download a precompiled version of ffmpeg from the official ffmpeg [website](https://ffmpeg.org/download.html#build-windows). After downloading and extracting the files, you'll need to add the bin directory to your system's PATH. Then do
		- ```pip install sounddevice```
	- For Mac
		- ```brew install portaudio ffmpeg```
2. Create a conda environment and install dependencies with
```
conda create --name mila python ipython jupyter
conda activate mila
pip install -r requirements.txt
```
