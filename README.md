# moodring
Repo for the Moodring Team project during the Berkeley AI Hackathon 2023

For linux do 
```
sudo apt-get install portaudio19-dev ffmpeg
pip install sounddevice
```
Windows needs to download download a precompiled version of ffmpeg from the official ffmpeg [website](https://ffmpeg.org/download.html#build-windows). After downloading and extracting the files, you'll need to add the bin directory to your system's PATH. Then do
```
pip install sounddevice
```
Mac
```
brew install portaudio ffmpeg
```

Then, create a conda environment and install dependencies with
```
conda create --name moodring python ipython jupyter
conda activate moodring
pip install -r requirements.txt
```
