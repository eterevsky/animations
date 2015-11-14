import numpy as np


def npvector(s):
  return np.array(s, dtype='float64')


class Camera(object):
  def __init__(self, fov=30, loc=(0, -1, 0), to=(0, 0, 0), up=(0, 0, 1)):
    self.fov = fov
    self.loc = npvector(loc)
    self.to = npvector(to)
    self.up = npvector(up)


class AreaLight(object):
  def __init__(self, color=(1, 1, 1), power=1000.0):
    self.color = npvector(color)
    self.power = power
    

class Object(object):
  def __init__(self, light=None):
    self.light = light


class Sphere(Object):
  def __init__(self, center=(0, 0, 0), radius=1, **kwargs):
    super().__init__(**kwargs)
    self.center = npvector(center)
    self.radius = radius


class Scene(object):
  def __init__(self):
    self.camera = Camera()
    self.objects = []
