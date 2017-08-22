#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""A pure Python implementation of stream.pyx.

For internal use only; no backwards-compatibility guarantees.
"""

from builtins import chr
from builtins import object
import struct
import sys

class OutputStream(object):
  """For internal use only; no backwards-compatibility guarantees.

  A pure Python implementation of stream.OutputStream."""

  def __init__(self):
    self.data = []

  def write(self, b, nested=False):
    assert isinstance(b, str)
    if nested:
      self.write_var_int64(len(b))
    if sys.version_info[0] < 3:
      # We decode it from latin-1 first since if we directly attempt to encode
      # it Python may assume an ASCII encoding (which limmits range to 128).
      encoded = b.decode("latin-1").encode("latin-1")
    else:
      encoded = b
    self.data.append(encoded)

  def write_byte(self, val):
    self.data.append(chr(val).encode("latin-1"))

  def write_var_int64(self, v):
    if v < 0:
      v += 1 << 64
      if v <= 0:
        raise ValueError('Value too large (negative).')
    while True:
      bits = v & 0x7F
      v >>= 7
      if v:
        bits |= 0x80
      self.write_byte(bits)
      if not v:
        break

  def write_bigendian_int64(self, v):
    self.write(struct.pack(b'>q', v))

  def write_bigendian_uint64(self, v):
    self.write(struct.pack(b'>Q', v))

  def write_bigendian_int32(self, v):
    self.write(struct.pack(b'>i', v))

  def write_bigendian_double(self, v):
    self.write(struct.pack(b'>d', v))

  def get(self):
    return b''.join(self.data)

  def size(self):
    return len(self.data)


class ByteCountingOutputStream(OutputStream):
  """For internal use only; no backwards-compatibility guarantees.

  A pure Python implementation of stream.ByteCountingOutputStream."""

  def __init__(self):
    # Note that we don't actually use any of the data initialized by our super.
    super(ByteCountingOutputStream, self).__init__()
    self.count = 0

  def write(self, byte_array, nested=False):
    blen = len(byte_array)
    if nested:
      self.write_var_int64(blen)
    self.count += blen

  def write_byte(self, _):
    self.count += 1

  def get_count(self):
    return self.count

  def get(self):
    raise NotImplementedError

  def __str__(self):
    return '<%s %s>' % (self.__class__.__name__, self.count)


class InputStream(object):
  """For internal use only; no backwards-compatibility guarantees.

  A pure Python implementation of stream.InputStream."""

  def __init__(self, data):
    self.data = data
    self.pos = 0

  def size(self):
    return len(self.data) - self.pos

  def read(self, size):
    self.pos += size
    return self.data[self.pos - size : self.pos]

  def read_all(self, nested):
    return self.read(self.read_var_int64() if nested else self.size())

  def read_byte(self):
    self.pos += 1
    return ord(self.data[self.pos - 1])

  def read_var_int64(self):
    shift = 0
    result = 0
    while True:
      byte = self.read_byte()
      if byte < 0:
        raise RuntimeError('VarLong not terminated.')

      bits = byte & 0x7F
      if shift >= 64 or (shift >= 63 and bits > 1):
        raise RuntimeError('VarLong too long.')
      result |= bits << shift
      shift += 7
      if not byte & 0x80:
        break
    if result >= 1 << 63:
      result -= 1 << 64
    return result

  def read_bigendian_int64(self):
    return struct.unpack(b'>q', self.read(8))[0]

  def read_bigendian_uint64(self):
    return struct.unpack(b'>Q', self.read(8))[0]

  def read_bigendian_int32(self):
    return struct.unpack(b'>i', self.read(4))[0]

  def read_bigendian_double(self):
    return struct.unpack(b'>d', self.read(8))[0]


def get_varint_size(v):
  """For internal use only; no backwards-compatibility guarantees.

  Returns the size of the given integer value when encode as a VarInt."""
  if v < 0:
    v += 1 << 64
    if v <= 0:
      raise ValueError('Value too large (negative).')
  varint_size = 0
  while True:
    varint_size += 1
    v >>= 7
    if not v:
      break
  return varint_size
