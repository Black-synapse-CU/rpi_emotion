# Raspberry Pi Emotion Recognition Package

This package contains the necessary files to run the emotion recognition and face display system on a Raspberry Pi.

## Hardware

- Raspberry Pi 4
- 3.5 inch touch screen (ADS7846)
- PCA9685 servo driver

## Contents

- `rpi_face/`: Python script to display an interactive face using Pygame.
- `emotion_recognition/`: FastAPI server for audio-based emotion recognition using Wav2Vec2.
- `action_servos/`: Hardware control for PCA9685 servo drivers.

## Preinstalled requirements
Driver for touch screen:
   https://yingkeen.com/setting-up-raspberry-pi-with-3-5-inch-touch-screen-xpt2046.html

Touch screen configuration:

   sudo rm -rf LCD-show
   git clone https://github.com/goodtft/LCD-show.git
   chmod -R 755 LCD-show
   cd LCD-show/
   sudo ./LCD35-show
   


## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Face Client:
   ```bash
   python rpi_face/face_client.py
   ```

3. (Optional) Run the Emotion Server:
   ```bash
   python emotion_recognition/emotion_server.py
   ```

## Running on the pi 

Login via ssh:
```bash
ssh student@[IP_ADDRESS]
```

Activate the virtual environment:

```bash
 source venv/bin/activate 
```

Run the face client:
```bash
export DISPLAY=:0
export FULLSCREEN=true 
python rpi_face/face_client.py
```

