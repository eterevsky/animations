import json
import logging
import math
import moviepy.editor as mpy
import os
import shutil
import tempfile

from . import lux
from . import pbrt
from .scene import Camera, Sphere, AreaLight, Scene


def create_renderer(renderer=None, config=None, **kwargs):
  assert renderer is not None or config is not None
  if isinstance(config, str):
    config = json.loads(config)
  if renderer is None:
    renderer = config['renderer']

  params = {}
  if 'common' in config:
    params.update(config['common'])
  if renderer in config:
    params.update(config[renderer])
  params.update(kwargs)

  logging.info('Creating a renderer %s with parameters %s', renderer, params)

  if renderer == 'luxrender':
    return lux.LuxRenderer(**params)
  elif renderer == 'pbrt':
    return pbrt.PbrtRenderer(**params)
  raise Exception('Unknown renderer type: {}'.format(renderer))


class Movie(object):
  def __init__(self, renderer, fps=60):
    self.renderer = renderer
    self.fps = fps
    self.dir = tempfile.TemporaryDirectory()
    self.frames = []
    self.scenes = []
    logging.info('Created a temporary directory %s for frame images.',
                 self.dir.name)

  def __del__(self):
    logging.info('Deleting temporary directory %s.', self.dir.name)
    self.dir.cleanup()

  def render_clip(self, start, end, frame_func):
    logging.info('Rendering a clip from %f to %f', start, end)
    for f in range(int(math.ceil((end - start) * self.fps))):
      frame_path = os.path.join(self.dir.name,
                                'f{:05}.png'.format(len(self.frames)))
      scene_path = os.path.join(self.dir.name,
                                'f{:05}.lxs'.format(len(self.scenes)))
      self.scenes.append(scene_path)
      self.frames.append(frame_path)
      self.renderer.output_file = frame_path
      self.renderer.scene_file = scene_path
      scene = frame_func(start + f / self.fps)
      self.renderer.render(scene, generate_only=True)
    self.renderer.batch_render(self.scenes)

  def write(self, output):
    clip = mpy.ImageSequenceClip(self.frames, fps=self.fps)
    clip.write_videofile(output, fps=self.fps, audio=False)
