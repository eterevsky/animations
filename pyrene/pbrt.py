import logging
import numpy as np
import os
import subprocess
import tempfile

from . import scene
from . import rman


ZERO = scene.npvector((0, 0, 0))


_film = rman.Identifier(
    'Film', positional=['string'],
    named={
        'xresolution': 'integer',
        'yresolution': 'integer',
        'cropwindow': 'float[4]',
        'filename': 'string'
    })



_look_at = rman.Identifier('LookAt', positional=['point', 'point', 'vector'])

_camera = rman.Identifier(
    'Camera', positional=['string'],
    named={
        'shutteropen': 'float',
        'shutterclose': 'float',
        'lensradius': 'float',
        'focaldistance': 'float',
        'fov': 'float',
        'autofocus': 'bool'
    })

_sampler = rman.Identifier(
    'Sampler', positional=['string'],
    named={
        'pixelsamples': 'integer',
    })

_area_light_source = rman.Identifier(
    'AreaLightSource', positional=['string'],
    named={'L': 'rgb'})

_translate = rman.Identifier('Translate', positional=['vector'])

_rotate = rman.Identifier('Rotate', positional=['float', 'vector'])

_shape = rman.Identifier(
    'Shape', positional=['string'],
    named={
        'radius': 'float',
        'indices': 'integer[]',
        'P': 'point[]'
    })


class PbrtRenderer(object):
  def __init__(self, executable=None, output_file=None, scene_file=None,
               width=384, height=256, samples_per_pixel=None, slaves=None,
               exrpptm=None, exrnormalize=None, exrtopng=None):
    self.executable = executable
    self.output_file = output_file
    self.scene_file = scene_file
    self.width = width
    self.height = height
    self.samples_per_pixel = samples_per_pixel
    self.scene_file_ext = 'pbrt'
    self.exrpptm = exrpptm
    self.exrnormalize = exrnormalize
    self.exrtopng = exrtopng

  @property
  def output_file(self):
    return self._output_file

  @output_file.setter
  def output_file(self, value):
    logging.info('output_file = %s', value)
    if value is None:
      self._output_file = None
      self._exr_file = None
      return
    self._output_file = value
    base, ext = os.path.splitext(value)
    logging.info('base = %s, ext = %s', base, ext)
    assert ext == '.png'
    self._exr_file = base + '.exr'

  def render(self, scene, generate_only=False):
    scene_file = self.scene_file or tempfile.mkstemp()[1]
    logging.info('Created scene file %s', scene_file)
    self._write_scene_file(scene, scene_file)

    if not generate_only:
      self._run_renderer(scene_file)

    if not self.scene_file:
      logging.info('Deleting %s', scene_file)
      os.remove(scene_file)

  def _write_object(self, writer, obj):
    writer.begin_block('Attribute')

    if obj.light is not None:
      color = obj.light.color * obj.light.power
      writer.write(_area_light_source('diffuse', L=obj.light.color))

    if isinstance(obj, scene.Sphere):
      if not np.array_equal(obj.center, ZERO):
        writer.write(_translate(obj.center))
      writer.write(_shape("sphere", radius=obj.radius))
    else:
      assert False, "Unsupported object type"

    writer.end_block('Attribute')

  def _write_scene_file(self, scene, scene_file):
    with rman.FileWriter(scene_file) as writer:
      writer.write(_look_at(scene.camera.loc, scene.camera.to, scene.camera.up))
      writer.write(_film(
          'image',
          xresolution=self.width, yresolution=self.height,
          filename=self._exr_file))
      writer.write(_camera('perspective', fov=scene.camera.fov))
      if self.samples_per_pixel:
        writer.write(_sampler('lowdiscrepancy', pixelsamples=self.samples_per_pixel))

      writer.begin_block('World')
      for obj in scene.objects:
        self._write_object(writer, obj)
      writer.end_block('World')

  def _run_renderer(self, scene_file):
    if self.executable is None:
      logging.error(
          'Trying to call pbrt, but path to the executable is not specified.')
    assert self.executable is not None
    args = [self.executable, scene_file]
    logging.info('Running %s', ' '.join(args))
    subprocess.call(args)

    args = [self.exrpptm, '-c', '1.0', self._exr_file, self._exr_file + '.pp']
    logging.info('Running %s', ' '.join(args))
    subprocess.call(args)
    args = [self.exrnormalize, self._exr_file + '.pp', self._exr_file + '.n']
    logging.info('Running %s', ' '.join(args))
    subprocess.call(args)
    args = [self.exrtopng, self._exr_file + '.n', self.output_file]
    logging.info('Running %s', ' '.join(args))
    subprocess.call(args)

  def batch_render(self, scene_files):
    logging.info('Rendering %d files', len(scene_files))
    for f in scene_files:
      self._run_renderer(f)
