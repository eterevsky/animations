import logging
import numpy as np
import os
import subprocess
import tempfile

from . import scene


ZERO = scene.npvector((0, 0, 0))


class LuxIdentifier(object):
  def __init__(self, name, positional=None, named=None):
    self._name = name
    self._positional = positional or []
    self._named = named or {}

  def __call__(self, *args, **kwargs):
    s = self._name
    logging.debug('Creating luxrender identifier %s %s %s',
                  self._name, args, kwargs)
    assert len(args) == len(self._positional)
    for t, arg in zip(self._positional, args):
      if t == 'integer':
        s += '  {:d}'.format(arg)
      elif t == 'float':
        s += '  {:f}'.format(arg)
      elif t in ('point', 'vector', 'normal', 'color'):
        s += '  ' + ' '.join('{:f}'.format(a) for a in arg)
      elif t == 'bool':
        s += '  "true"' if arg else '  "false"'
      elif t == 'string':
        s += '  "{}"'.format(arg)
      else:
        assert False, 'Unexpected type name'

    for n, v in kwargs.items():
      t = self._named[n]
      s += '  "{t} {n}"'.format(t=t, n=n)
      if t == 'integer':
        s += ' {:d}'.format(v)
      elif t == 'float':
        s += ' [{:f}]'.format(v)
      elif t in ('point', 'vector', 'normal', 'color'):
        s += ' [' + ' '.join('{:f}'.format(a) for a in v) + ']'
      elif t == 'bool':
        s += ' ["true"]' if v else '  ["false"]'
      elif t == 'string':
        s += ' "{}"'.format(v)
      else:
        assert False, 'Unexpected type name'

    return s


_film = LuxIdentifier(
    'Film', positional=['string'],
    named={
        'xresolution': 'integer',
        'yresolution': 'integer',
        'cropwindow': 'float[4]',
        'gamma': 'float',
        'haltspp': 'integer',
        'filename': 'string'
    })

_look_at = LuxIdentifier('LookAt', positional=['point', 'point', 'vector'])

_camera = LuxIdentifier(
    'Camera', positional=['string'],
    named={
        'hither': 'float',
        'yon': 'float',
        'shutteropen': 'float',
        'shutterclose': 'float',
        'lensradius': 'float',
        'focaldistance': 'float',
        'fov': 'float',
        'autofocus': 'bool'
    })

_area_light_source = LuxIdentifier(
    'AreaLightSource', positional=['string'],
    named={'L': 'color', 'power': 'float'})

_translate = LuxIdentifier('Translate', positional=['vector'])

_rotate = LuxIdentifier('Rotate', positional=['float', 'vector'])

_shape = LuxIdentifier(
    'Shape', positional=['string'],
    named={
        'radius': 'float',
        'indices': 'integer[]',
        'P': 'point[]'
    })


class LuxFileWriter(object):
  def __init__(self, path):
    self.path = path
    self.indent = 0

  def __enter__(self):
    self.out = open(self.path, 'w')
    return self

  def __exit__(self, *args):
    self.out.close()

  def _write_indent(self):
    self.out.write(' ' * self.indent)

  def begin_block(self, block):
    self._write_indent()
    self.out.write(block + 'Begin\n')
    self.indent += 2

  def end_block(self, block):
    self.indent -= 2
    self._write_indent()
    self.out.write(block + 'End\n')

  def write(self, s):
    self._write_indent()
    self.out.write(s + '\n')


class LuxRenderer(object):
  def __init__(self, luxconsole=None, output_file=None, scene_file=None,
               width=384, height=256, samples_per_pixel=10, slaves=None):
    self.luxconsole = luxconsole
    self.output_file = output_file
    self.scene_file = scene_file
    self.width = width
    self.height = height
    self.samples_per_pixel = samples_per_pixel
    self.slaves = slaves or []
    logging.info('__init__ slaves: %s', slaves)

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
      writer.write(_area_light_source('area', L=obj.light.color, power=obj.light.power))

    if isinstance(obj, scene.Sphere):
      if not np.array_equal(obj.center, ZERO):
        writer.write(_translate(obj.center))
      writer.write(_shape("sphere", radius=obj.radius))
    else:
      assert False, "Unsupported object type"

    writer.end_block('Attribute')

  def _stripped_output(self):
    if self.output_file is None:
      return None
    if self.output_file.endswith('.png'):
      return self.output_file[:-4]
    else:
      return self.output_file

  def _write_scene_file(self, scene, scene_file):
    with LuxFileWriter(scene_file) as writer:
      writer.write(_look_at(scene.camera.loc, scene.camera.to, scene.camera.up))
      writer.write(_film(
          'fleximage',
          xresolution=self.width, yresolution=self.height,
          haltspp=self.samples_per_pixel, filename=self._stripped_output()))
      writer.write(_camera('perspective', fov=scene.camera.fov))

      writer.begin_block('World')
      for obj in scene.objects:
        self._write_object(writer, obj)
      writer.end_block('World')

  def _run_renderer(self, scene_file):
    logging.debug('Output file: `%s`', self.output_file)
    if self.luxconsole is None:
      logging.error(
          'Trying to call LuxRender, but path to luxconsole is not specified.')
    assert self.luxconsole is not None
    args = [self.luxconsole, scene_file]
    if self.output_file:
      args.extend(['-o', os.path.abspath(self._stripped_output())])
    if self.slaves:
      for s in self.slaves:
        args.extend(['-u', s])
    logging.info('Running %s', ' '.join(args))
    subprocess.call(args)

  def batch_render(self, scene_files):
    logging.info('Rendering %d files', len(scene_files))
    if self.luxconsole is None:
      logging.error(
          'Trying to call LuxRender, but path to luxconsole is not specified.')
    assert self.luxconsole is not None
    list_file = tempfile.mkstemp()[1]
    lf = open(list_file, 'w+')
    lf.write('\n'.join(scene_files))
    lf.close()
    args = [self.luxconsole, '-L', list_file, '-i', '10']
    if self.slaves:
      for s in self.slaves:
        args.extend(['-u', s])
    logging.info('Running %s', ' '.join(args))
    subprocess.call(args)
