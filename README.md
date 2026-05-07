# Raspberry Pi Emotion Recognition Package

This package contains the necessary files to run the emotion recognition and face display system on a Raspberry Pi.

## Hardware

- Raspberry Pi 4
- 3.5 inch touch screen (ADS7846)
- PCA9685 servo driver

## Contents

- `rpi_face/`: Python script to display an interactive face using Pygame and FastAPI.

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

1. Activate the virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate 
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Face Service:
   ```bash
   python rpi_face/face_service.py
   ```



## Running on the pi 

Login via ssh:
```bash
ssh student@[IP_ADDRESS]
```

Activate the virtual environment:

```bash
python3 -m venv venv
 source venv/bin/activate 
```

Run the face service:
```bash
export DISPLAY=:0
export FULLSCREEN=true 
python rpi_face/face_service.py
```

