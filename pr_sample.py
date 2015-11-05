import argparse
import logging
import os

import pyrend

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--luxrender', metavar='DIR',
                      help='path to luxrender directory')
  parser.add_argument('--output', '-o', default='output.png',
                      metavar='FILE', help='output file')
  parser.add_argument('--scene', '-s', default=None,
                      help='output lxs scene file')
  parser.add_argument('--generate-only', '-g', default=False,
                      action='store_true', help='only generate the scene file')
  args = parser.parse_args()

  if args.luxrender:
    luxconsole = os.path.join(args.luxrender, 'luxconsole')
  else:
    luxconsole = None

  renderer = pyrend.LuxRenderer(luxconsole=luxconsole,
                                output_file=args.output,
                                scene_file=args.scene)
  scene = pyrend.Scene()
  renderer.render(scene, generate_only=args.generate_only)


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  main()
