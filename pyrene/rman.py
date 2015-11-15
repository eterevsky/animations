import logging


class Identifier(object):
  def __init__(self, name, positional=None, named=None):
    self._name = name
    self._positional = positional or []
    self._named = named or {}

  def __call__(self, *args, **kwargs):
    s = self._name
    logging.debug('Creating identifier %s %s %s',
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
        s += ' [{:d}]'.format(v)
      elif t == 'float':
        s += ' [{:f}]'.format(v)
      elif t in ('point', 'vector', 'normal', 'color', 'rgb'):
        s += ' [' + ' '.join('{:f}'.format(a) for a in v) + ']'
      elif t == 'bool':
        s += ' ["true"]' if v else '  ["false"]'
      elif t == 'string':
        s += ' "{}"'.format(v)
      else:
        assert False, 'Unexpected type name'

    return s


class FileWriter(object):
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
