import argparse
import logging
import os

import pyrene

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--config', metavar='FILE', default='./pyrene.json',
                      help='pyrene renderer config')
  parser.add_argument('--output', '-o', default='out/output.png',
                      metavar='FILE', help='output file')
  parser.add_argument('--scene', '-s', default=None,
                      help='output lxs scene file')
  parser.add_argument('--generate-only', '-g', default=False,
                      action='store_true', help='only generate the scene file')
  args = parser.parse_args()

  with open(args.config) as config_file:
    config = config_file.read()

  renderer = pyrene.create_renderer(config=config,
                                    output_file=args.output,
                                    scene_file=args.scene,
                                    samples_per_pixel=10000)
  scene = pyrene.Scene()
  scene.camera = pyrene.Camera(loc=(0, -10, 0), to=(0, 0, 0))
  scene.objects.append(pyrene.Sphere())
  scene.objects.append(pyrene.Sphere(center=(1, -1, 0.5), radius=0.5,
                                     light=pyrene.AreaLight(color=(1, 1, 1))))
  renderer.render(scene, generate_only=args.generate_only)


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  main()
