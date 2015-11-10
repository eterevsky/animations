import unittest

from lux import LuxRenderer
from scene import Sphere, Scene, AreaLight, Camera


class TestLuxRenderer(unittest.TestCase):

  def test_render(self):
    renderer = LuxRenderer(samples_per_pixel=1000)
    scene = Scene()
    scene.camera = Camera(loc=(0, -10, 0), to=(0, 0, 0))
    scene.objects.append(Sphere())
    scene.objects.append(Sphere(center=(1, -1, 0.5), radius=0.5,
                                light=AreaLight(color=(1, 1, 1))))
    renderer.render(scene, generate_only=True)


if __name__ == '__main__':
    unittest.main()
