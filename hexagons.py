import math

SQ3 = math.sqrt(3)

verts = [(1/2, 1/(2*SQ3)), (0, 1/SQ3), (-1/2, 1/(2*SQ3)),
         (-1/2, -1/(2*SQ3)), (0, -1/SQ3), (1/2, -1/(2*SQ3))]

TEMPLATE = """
AttributeBegin
  Material "matte" "color Kd" [{color}]
  Shape "trianglemesh" "integer indices" [0 1 2  0 2 3  0 3 4  0 4 5]
    "point P" [{points}]
AttributeEnd
"""

out = open('out/hexagons-geom.lxo', 'w')

for x in range(-5, 6):
  for y in range(-5, 6):
    cx, cy = (x + y / 2, y * SQ3 / 2)
    h = 0.4 * ((x + 2*y) % 3)
    for dh in range(4):
      points = []
      for i in range(6):
        dx, dy = verts[i]
        points.append((cx + dx, h + dh * 1.2, cy + dy))

      points_str = '  '.join('{:.4f} {:.4f} {:.4f}'.format(x, y, z)
                             for x, y, z in points)
      colors = [(0.902, 0.29, 0.098), (0.38, 0.38, 0.38), (0.271, 0.353, 0.392)]
      c = colors[(x + 2*y) % 3]

      out.write(TEMPLATE.format(points=points_str, color=' '.join(map(str, c))))
