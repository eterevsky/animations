This repository is for scripts that generate geometric animations and images.
All scripts are written in Python and require Python 3.2 or later (tested on
Python 3.4).

## dragon_curve

Generates a video with the construction of the
[dragon curve](http://en.wikipedia.org/wiki/Dragon_curve).
Here's [the resulting video](https://youtu.be/m4-ILvsOFGo).

The requirements to run this script:

- `cairo-cffi`
- `moviepy`
- `numpy`
- `scipy`

## hexagons

Simple 3D image with colored hexagons. [LuxRender](http://www.luxrender.net/)
required for rendering.

    python3 hexagons.py
    luxconsole hexagons.lxs
