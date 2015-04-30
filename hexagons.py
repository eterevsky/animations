import math

def rotate(vec, angle_deg):
  angle = angle_deg * math.pi / 180
  s = math.sin(angle)
  c = math.cos(angle)
  x, y = vec
  return c * x - s * y, s * x + c * y

OBJECT_TEMPLATE = """
ObjectBegin "hexagon"
  Shape "trianglemesh" "integer indices" [0 1 2  0 2 3  0 3 4  0 4 5]
    "point P" [{points}]
ObjectEnd
"""

def base_hexagon():
  x, y = (1 / 2, 1 / (2 * math.sqrt(3)))
  points = [x, y, 0]
  for i in range(5):
    x, y = rotate((x, y), 60)
    points.extend([x, y, 0])
  return OBJECT_TEMPLATE.format(
      points=' '.join('{:.6f}'.format(p) for p in points))

INSTANCE_TEMPLATE = """
AttributeBegin
  Translate {x:.5f} {y:.5f} {z:.5f}
  NamedMaterial "hex{idx}"
  ObjectInstance "hexagon"
AttributeEnd
"""

HSTEP = 0.4

out = open('out/hexagons-geom.lxo', 'w')
out.write(base_hexagon())

for x in range(-5, 6):
  for y in range(-5, 6):
    cx, cy = (x + y / 2, y * math.sqrt(3) / 2)
    idx = (x + 2 * y) % 3
    for h in range(2):
      out.write(INSTANCE_TEMPLATE.format(
          idx=idx, x=cx, y=cy, z=-(HSTEP * idx + 3 * HSTEP * h)))
