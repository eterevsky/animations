import logging
import os
import subprocess
import tempfile


class LuxRenderer(object):
  def __init__(self, luxconsole=None, output_file=None, scene_file=None):
    self.luxconsole = luxconsole
    self.output_file = output_file
    self.scene_file = scene_file

  def write_scene_file(self, scene, scene_file):
    with open(scene_file, 'w') as out:
      out.write('hi')

  def render(self, scene):
    scene_file = self.scene_file or tempfile.mkstemp()[1]
    logging.info('Created scene file %s', scene_file)
    self.write_scene_file(scene, scene_file)

    if self.output_file:
      self._run_renderer(scene_file)

    if not self.scene_file:
      logging.info('Deleting %s', scene_file)
      os.remove(scene_file)

  def _run_renderer(self, scene_file):
    args = [self.luxconsole, scene_file]
    logging.info('Running %s', ' '.join(args))
    subprocess.call(args)


class Scene(object):
  def __init__(self):
    pass


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  renderer = LuxRenderer()
  renderer.render(None)
