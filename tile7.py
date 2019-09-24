import math
from pyx import canvas, path

def p(rad, total, i):
    t = 2 * math.pi * i / total
    return rad * math.cos(t), rad * math.sin(t)

c = canvas.canvas()

for r in range(1, 6):
    total = 7 * 4**(r-1)
    for i in range(total):
        x, y = p(r, total, i)
        xn, yn = p(r, total, i+1)
        c.stroke(path.line(x, y, xn, yn))

        if r > 1 and i % 4 == 0:
            xl, yl = p(r - 1, total / 4, i / 4)
            c.stroke(path.line(x, y, xl, yl))

c.writePDFfile("path")
