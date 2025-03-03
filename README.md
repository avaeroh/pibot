# pibot

My robot Pi! This has been built with:

- Raspi 4B.
- CamJam #3 kit.
- 10mah powerbank (for Pi).
- 4x AA batteries (for motor).
- PiCamera (IR version has not worked).

Current functionality:f

- Webserver to view Pibot camera and control via WASD & buttons
- Tensorflow Lite (for object recognition.)

I have bundled everything as a Docker image as I want to give flexibility to update the Pis with relative ease, or port to other hardware at a later date. I've also added basic mock functionality for Pi-specific imports so I can develop when I don't have my Pi to hand, or my SD card suddenly fails (like now `:(` ).

# Requirements

- Docker
- Pi (working with 4b) with CamJam #3 kit

# Instructions

1. Set your `.env`, something like...

```env
PORTAINER_PORT=9000
PYTHONUNBUFFERED=1
BUTTON_DELAY=0.2
FLASK_PORT=5000
```

2. Run `docker compose up -d --build`
3. Manage containers with portainer
4. Use Flask UI (or API calls to control PI)

## For TFLite

- 1. Do above.
- 2. Run detection with `python3 /tflite/detect.py`

# Notes

- The frontend is simply html and will be replaced at some point. Ideally the robot will be somewhat autonomous, so it may even be removed.
- I have always used Docker to work with this app, and developed on systems that do not have the pi (due to various hardware issues while I still wanted to code). This has all only been tested via the docker setup.
