# DeepEmotion

DeepEmotion is a web app for detecting emotions in video frames. 

It runs on Flask + Nginx + [Peltarion](peltarion.com) API.

![video-demo example](video-demo_mid.gif)

## Installation

Instructions for installing Nginx and Gunicorn for Flask are available on [Digital Ocean](https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04).

Install with `python setup.py install`, which creates a `config.cfg` file in the root directory. To connect with Peltarion API, add your key to `config.cfg`:

```
EMOTION_API_URL='ENTER_MY_URL'
EMOTION_API_TOKEN='ENTER_MY_TOKEN'
```
