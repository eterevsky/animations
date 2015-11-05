import logging
import numpy as np
import os
import subprocess
import tempfile


def npvector(s):
  return np.array(s, dtype='float64')


def space_separated(v):
  return ' '.join(map(str, v))


FILM_SPEC = """
Film "fleximage"
  "integer xresolution" [{width}] "integer yresolution" [{height}]
  "integer haltspp" [{spp}] "string filename" ["{filename}"]
""".lstrip()

class LuxRenderer(object):
  def __init__(self, luxconsole=None, output_file=None, scene_file=None,
               width=384, height=256, samples_per_pixel=10):
    self.luxconsole = luxconsole
    self.output_file = output_file
    self.scene_file = scene_file
    self.width = width
    self.height = height
    self.samples_per_pixel = samples_per_pixel

  def render(self, scene, generate_only=False):
    scene_file = self.scene_file or tempfile.mkstemp()[1]
    logging.info('Created scene file %s', scene_file)
    self._write_scene_file(scene, scene_file)

    if not generate_only:
      self._run_renderer(scene_file)

    if not self.scene_file:
      logging.info('Deleting %s', scene_file)
      os.remove(scene_file)

  def _write_scene_file(self, scene, scene_file):
    with open(scene_file, 'w') as out:
      out.write(FILM_SPEC.format(
          width=self.width, height=self.height, spp=self.samples_per_pixel,
          filename=self.output_file))
      out.write('LookAt {loc}  {to}  {up}\n'.format(
          loc=space_separated(scene.camera.loc),
          to=space_separated(scene.camera.to),
          up=space_separated(scene.camera.up)))
      out.write('Camera "perspective" "float fov" [{fov}]'.format(
          fov=scene.camera.fov))


  def _run_renderer(self, scene_file):
    args = [self.luxconsole, scene_file]
    logging.info('Running %s', ' '.join(args))
    subprocess.call(args)


class Camera(object):
  def __init__(self, fov=30, loc=(0, -1, 0), to=(0, 0, 0), up=(0, 0, 1)):
    self.fov = fov
    self.loc = npvector(loc)
    self.to = npvector(to)
    self.up = npvector(up)


class Scene(object):
  def __init__(self):
    self.camera = Camera()


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  renderer = LuxRenderer()
  renderer.render(None)
