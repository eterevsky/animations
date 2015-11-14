import logging
import math

import pyrene


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
  config_path = os.path.dirname(os.path.realpath(__file__))
  with open(config_path) as config_file:
    config = config_file.read()
  renderer = pyrene.create_renderer(
      config=config, samples_per_pixel=20, width=1280, height=720)
  movie = pyrene.Movie(renderer=renderer, fps=60)
  movie.render_clip(0.0, 4.0, gen_frame)
  movie.write('out/light2.mp4')


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  main()
