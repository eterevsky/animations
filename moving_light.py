import logging
import math
import os

import pyrene


# 20 minutes with Lux, 10 minutes with pbrt


def gen_frame(t):
  logging.info('Generating frame for time %f', t)
  scene = pyrene.Scene()
  scene.camera = pyrene.Camera(loc=(0, -10, 0), to=(0, 0, 0))
  scene.objects.append(pyrene.Sphere(
      radius=0.1, light=pyrene.AreaLight(color=(1, 1, 1))))
  scene.objects.append(pyrene.Sphere(
      radius=1, center=(3*math.cos(t), 3*math.sin(t), 0.2*math.cos(t))))
  return scene


def main():
  config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pyrene.json')
  with open(config_path) as config_file:
    config = config_file.read()
  renderer = pyrene.create_renderer(
      renderer='pbrt', config=config, samples_per_pixel=20, width=1280,
      height=720)
  movie = pyrene.Movie(renderer=renderer, fps=60)
  movie.render_clip(0.0, 4.0, gen_frame)
  movie.write('out/lights_pbrt.mp4')


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  main()
