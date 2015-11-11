import logging
import math
import moviepy.editor as mpy
import os
import shutil
import tempfile

from .lux import LuxRenderer
from .scene import Camera, Sphere, AreaLight, Scene


class Movie(object):
  def __init__(self, renderer, fps=60):
    self.renderer = renderer
    self.fps = fps
    self.dir = tempfile.TemporaryDirectory()
    self.frames = []
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
      self.frames.append(frame_path)
      self.renderer.output_file = frame_path
      scene = frame_func(start + f / self.fps)
      self.renderer.render(scene, generate_only=False)

  def write(self, output):
    clip = mpy.ImageSequenceClip(self.frames, fps=self.fps)
    clip.write_videofile(output, fps=self.fps, audio=False)
