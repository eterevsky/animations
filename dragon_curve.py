from bisect import bisect
import cairocffi as cairo
from math import cos, exp, log, sin, sqrt
import moviepy.editor as mpy
import numpy
import os
from queue import Queue
from scipy import optimize
import shutil
import sys
import tempfile
import threading

DURATION = 40
FPS = 60
PROCESSES = 4


class Figure(object):
  def __init__(self):
    self._points = [(0, 0), (1, 0)]
    self._right = [0, 1]
    self._top = [0]
    self._left = [0]
    self._bottom = [0]

  def dimensions(self, t):
    while t > len(self._points) - 3:
      self._gen_more_points()
    lox = self._points[self._left[bisect(self._left, t) - 1]][0]
    hix = self._points[self._right[bisect(self._right, t) - 1]][0]
    loy = self._points[self._bottom[bisect(self._bottom, t) - 1]][1]
    hiy = self._points[self._top[bisect(self._top, t) - 1]][1]

    ex, ey = self._get_end(t)

    return min(lox, ex, 0), max(hix, ex, 1), min(loy, ey), max(hiy, ey)

  def draw(self, context, t):
    while t > len(self._points) - 3:
      self._gen_more_points()
    context.move_to(0, 0)
    for px, py in self._points[1:int(t) + 1]:
      context.line_to(px, py)
    ex, ey = self._get_end(t)
    context.line_to(ex, ey)

  def _get_end(self, t):
    while t > len(self._points) - 3:
      self._gen_more_points()
    lx, ly = self._points[int(t)]
    nx, ny = self._points[int(t) + 1]
    dx, dy = nx - lx, ny - ly
    dt = t - int(t)
    ex, ey = lx + dx * dt, ly + dy * dt
    return (ex, ey)

  def _gen_more_points(self):
    sx, sy = self._points[-1]
    q = []
    l = len(self._points)
    for x, y in reversed(self._points[:-1]):
      dx, dy = x - sx, y - sy
      q.append((sx - dy, sy + dx))
    self._points.extend(q)
    for i in range(l, len(self._points)):
      x, y = self._points[i]
      if x > self._points[self._right[-1]][0]:
        self._right.append(i)
      if x < self._points[self._left[-1]][0]:
        self._left.append(i)
      if y > self._points[self._top[-1]][1]:
        self._top.append(i)
      if y < self._points[self._bottom[-1]][1]:
        self._bottom.append(i)


class Viewport(object):
  def __init__(self, figure, w, h, margin=0.1, min_scale=1.0):
    self._figure = figure
    self._screen_w = w
    self._screen_h = h
    self._margin = margin
    self._min_scale = min_scale / min(self._screen_w, self._screen_h)
    self.scale_func = self.default_scale_func
    self.translate_func = self.default_translate_func

  def time_func(self, t):
    return 2 ** (t / 2) - 1

  def approximate_scale_func(self, hi=10):
    v = [self.scale_func(s / 10) for s in range(10 * int(hi) + 1)]

    def get_scale_func(x, limit=False):
      a, b, c = x
      def f(t):
        s = exp(a + b * t + c * sqrt(t))
        if limit and s < self._min_scale:
          return self._min_scale
        else:
          return s

      return f

    def scale_func_err(x):
      f = get_scale_func(x)
      e = 0
      for i in range(len(v)):
        t = i / 10
        try:
          e += log(f(t) / v[i]) ** 2
        except ValueError:
          e += 1E10
      return e

    res = optimize.minimize(scale_func_err, (0.1, 0.1, 0), method='cg')
    print('Scale func params:', res.x)

    self.scale_func = get_scale_func(res.x, True)

  def default_scale_func(self, t):
    xmin, xmax, ymin, ymax = self._figure.dimensions(self.time_func(t))
    w = xmax - xmin
    h = ymax - ymin
    s = max(w / self._screen_w, h / self._screen_h) / (1 - 2 * self._margin)

    if s < self._min_scale:
      return self._min_scale
    else:
      return s

  def approximate_translate_func(self, hi=10):
    v = [self.translate_func(s / 10) for s in range(10 * int(hi) + 1)]

    def get_func(x):
      a, b, c, d, e, f, g, h, i, j = x
      return lambda t: ((a + b * t + c * sqrt(t)) * cos(d + e*t),
                        (f + g * t + h * sqrt(t)) * sin(i + j*t))

    def func_err(x):
      f = get_func(x)
      e = 0
      for i in range(len(v)):
        t = i / 10
        tx, ty = v[i]
        fx, fy = f(t)
        e += (tx - fx)**2 + (ty - fy)**2
      return e

    # res = optimize.minimize(func_err, [0]*5)
    res = optimize.basinhopping(func_err, [0]*10)
    print('Translate func params:', res.x, func_err(res.x))

    self.translate_func = get_func(res.x)

  def default_translate_func(self, t):
    """Translate vector.

    With respect to a screen that is scaled by scale_func() and has origin in
    the middle of the screen.
    """
    xmin, xmax, ymin, ymax = self._figure.dimensions(self.time_func(t))
    return numpy.array((-(xmin + xmax) / 2, -(ymax + ymin) / 2))

  def apply(self, context, t):
    scale = self.scale_func(t)
    tx, ty = self.translate_func(t)

    context.scale(1, -1)
    context.translate(self._screen_w / 2, -self._screen_h / 2)
    context.scale(1 / scale)
    context.translate(tx, ty)

  def line_width_func(self, t):
    return 1 - 9 / (9 + self.scale_func(t) / self.scale_func(0))


class Renderer(object):
  def __init__(self, duration=40):
    self._width = 1920
    self._height = 1080
    self.duration = duration
    self.fps = 60
    self._figure = Figure()
    self._viewport = Viewport(self._figure, self._width, self._height)
    self._viewport.approximate_scale_func(self.duration)

  def _init_cairo(self):
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, self._width, self._height)
    context = cairo.Context(surface)
    context.set_source_rgb(1, 1, 1)
    context.rectangle(0, 0, self._width, self._height)
    context.fill()

    context.set_source_rgb(0.957, 0.263, 0.212)
    context.set_line_cap(cairo.LINE_CAP_ROUND)
    context.set_line_join(cairo.LINE_JOIN_ROUND)

    return surface, context

  def _to_nparray(self, surface):
    im = 0 + numpy.frombuffer(surface.get_data(), numpy.uint8)
    im.shape = (surface.get_height(), surface.get_width(), 4)
    return im[:,:,[2,1,0]]  # put RGB back in order

  def make_frame(self, t, to_file=None):
    surface, context = self._init_cairo()
    self._viewport.apply(context, t)
    context.set_line_width(self._viewport.line_width_func(t))

    self._figure.draw(context, self._viewport.time_func(t))
    context.stroke()

    if to_file is None:
      return self._to_nparray(surface)
    surface.write_to_png(target=to_file)


def render_thread(renderer, queue, done_queue):
  while True:
    job = queue.get()
    if job == 'STOP':
      return
    filename, t = job
    renderer.make_frame(t, filename)
    done_queue.put(t)


def write_frames(directory, duration, fps):
  print('Preparing renderer.')
  renderer = Renderer()
  queue = Queue()
  done_queue = Queue()
  processes = []
  print('Starting {} threads.'.format(PROCESSES))
  for i in range(PROCESSES):
    thread = threading.Thread(
        target=render_thread, args=(renderer, queue, done_queue))
    thread.start()
    processes.append(thread)

  filenames = []
  for f in range(duration * fps):
    filename = os.path.join(directory, 'frame{}.png'.format(f))
    queue.put((filename, f / fps))
    filenames.append(filename)

  print('{} jobs queued.'.format(duration * fps))

  done = 0
  while done < duration * fps:
    done_job = done_queue.get()
    done += 1
    sys.stdout.write('\rCompleted images: {}/{}'.format(done, duration * fps))
    sys.stdout.flush()
  print()

  print('Stopping child processes.')
  for p in processes:
    queue.put('STOP')
  for p in processes:
    p.join()
  return filenames


directory = tempfile.mkdtemp()
print('Created temporary directory: {}'.format(directory))
files = write_frames(directory, DURATION, FPS)

#audio = mpy.AudioFileClip('dust.mp3')
#clip = mpy.VideoClip(renderer.make_frame, duration=renderer.duration)
clip = mpy.ImageSequenceClip(files, fps=FPS)
clip.write_videofile('out/dragon1080.mp4', fps=FPS, audio=False)
# clip.write_gif("dragon.gif", fps=FPS)

shutil.rmtree(directory)
