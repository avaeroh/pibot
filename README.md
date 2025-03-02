# pibot

My robot Pi!

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

# Notes

- The frontend is simply html and will be replaced at some point. Ideally the robot will be somewhat autonomous, so it may even be removed.
- I have always used Docker to work with this app, and developed on systems that do not have the pi (due to various hardware issues while I still wanted to code). This has all only been tested via the docker setup.
