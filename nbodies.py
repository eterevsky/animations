import logging
import math
import numpy as np

import pyrene


LUX_PATH = '../lux-v1.5-x86_64-sse2-OpenCL/luxconsole'


class Particle(object):
  def __init__(self, point, radius):
    self.location = point
    self.radius = radius


G = 1.0


class World(object):
  def __init__(self, nparticles=1000):
    self.points = np.random.multivariate_normal(
        (0, 0, 0), np.identity(3) * 25, size=nparticles)
    self.velocities = np.random.multivariate_normal(
        (0, 0, 0), np.identity(3) * 4, size=nparticles)
    self.radii = 0.5 * np.random.random(nparticles) + 0.5
    self.masses = 8 * self.radii ** 3
    self.name_to_id = {}
    self.visible = np.ones(nparticles, dtype=bool)
    self.t = 0
    self.n = nparticles

  def add_particle(self, name, point, velocity, radius, mass, visible):
    self.name_to_id[name] = len(self.masses)
    self.points = np.append(self.points, [point], axis=0)
    self.velocities = np.append(self.velocities, [velocity], axis=0)
    self.radii = np.append(self.radii, [radius])
    self.masses = np.append(self.masses, [mass])
    self.visible = np.append(self.visible, [visible])
    self.n += 1

  def get_particle(self, name):
    i = self.name_to_id[name]
    return Particle(self.points[i], self.radii[i])

  def iter_visible(self):
    for i in range(len(self.masses)):
      if self.visible[i]:
        yield Particle(self.points[i], self.radii[i])

  @staticmethod
  def acceleration(points):
    logging.info('Calculating acceleration for points:\n%s', points)
    r = points[np.newaxis] - points[:,np.newaxis]
    logging.info('Radial vectors:\n%s', r)
    dist = np.linalg.norm(r, axis=2)
    logging.info('Distances:\n%s', dist)

  def simulate(self, t1):
    # logging.debug('Points at time %f:\n%s', self.t, self.points)
    # logging.debug('Masses: %s', self.masses)
    # World.acceleration(self.points)
    # return
    dt = 0.001
    while self.t < t1:
      a = np.zeros((self.n, 3))
      for i in range(self.n):
        d = self.points - self.points[i]
        d[i][0] = 1  # to avoid division by zero
        numer = G * d * self.masses[:,np.newaxis]
        denom = (np.linalg.norm(d, axis=1)**3)[:,np.newaxis]
        a_per_point = numer / denom
        a_per_point[i] = [0, 0, 0]
        a[i] = np.sum(a_per_point, 0)
      self.velocities += dt / 2 * a
      self.points += dt * self.velocities
      self.velocities += dt / 2 * a
      self.t += dt

    e = np.sum(self.masses * np.linalg.norm(self.velocities, axis=1)**2 / 2)
    for i in range(self.n):
      d = self.points - self.points[i]
      d[i] = (1, 0, 0)
      e -= G * self.masses[i] * np.sum(self.masses / np.linalg.norm(d, axis=1))
    logging.info('Total energy: %f', e)


def gen_frame(world, t):
  logging.info('Generating frame for time %f', t)
  world.simulate(t)
  scene = pyrene.Scene()
  camera = world.get_particle('camera')
  scene.camera = pyrene.Camera(loc=camera.location, to=(0, 0, 0))
  sun = world.get_particle('sun')
  scene.objects.append(pyrene.Sphere(
      center=sun.location, radius=sun.radius,
      light=pyrene.AreaLight(color=(1, 1, 1), power=1000)))
  for particle in world.iter_visible():
    scene.objects.append(
        pyrene.Sphere(center=particle.location, radius=particle.radius))
  return scene


def main():
  world = World(100)
  world.add_particle('sun', (0, 0, 0), (0, 0, 0), 1, 10, False)
  world.add_particle('camera', (0, -50, 0), (2, 0, 0), 0, 1, False)

  logging.info(world.points)
  renderer = pyrene.LuxRenderer(
      luxconsole=LUX_PATH, samples_per_pixel=200, width=1280, height=720)
  scene = gen_frame(world, 0.0)

  movie = pyrene.Movie(renderer=renderer, fps=60)
  movie.render_clip(0.0, 30.0, lambda t: gen_frame(world, t))
  movie.write('out/nbodies1.mp4')


if __name__ == '__main__':
  logging.basicConfig(level=logging.INFO)
  main()
