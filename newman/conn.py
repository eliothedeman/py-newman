import io
import struct
import message
import inspect

def ll(msg):
	n = inspect.currentframe().f_back.f_lineno
	print(n, msg)

class IncorrectIOInterface(Exception):

	def __init__(self, msg):
		self._msg = msg

	def __str__(self):
		return "Incorrect Interface: {}".format(self._msg)

class Conn(object):
	"""A wrapper around an io buffer"""

	def __init__(self, rw, wait_func=None):
		self.rw = self._mk_file(rw)
		self._test_rw(rw)
		self.wait_func = wait_func
		self.buff = bytearray(1024 * 256)
		self.seekable = self._seekable(rw)
		self.r_pointer = 0
		self.w_pointer = 0

	def _mk_file(self, rw):
		# convert a socket into a file like object
		mf = getattr(rw, "makefile", None)
		if mf is not None:
			return rw.makefile(mode="rw")

		return rw

	def _seekable(self, rw):
		seek = getattr(rw, "seek", None)
		return seek is not None

	def _test_rw(self, rw):
		read = getattr(rw,  "read", None)
		write = getattr(rw, "write", None)

		# test that the these are methods
		if read is None:
			raise IncorrectIOInterface("Missing read method")

		if write is None:
			raise IncorrectIOInterface("Missing write method")

	def size_of(self, buff):
		l = len(buff)
		d = struct.pack("<Q", l)
		return d

	def next_size(self):
		buff = self.read_next_buffer(8)
		i = struct.unpack("<Q", buff)
		return i[0]

	def next(self, message):
		buff = self.read_next_buffer(self.next_size())
		message.unmarshal_binary(buff)
		return len(buff)

	def write(self, message):
		buff = message.marshal_binary()

		# write out the size of the buffer
		self.write_next_buffer(self.size_of(buff))

		# write the message
		self.write_next_buffer(buff)
		return len(buff)


	def read_next_buffer(self, n):
		"""Read the next n bytes off the buffer"""
		x = 0
		d = 0
		if self.seekable:
			self.rw.seek(self.r_pointer)
		while n > x:

			buff = self.rw.read(n)
			d = len(buff)
			if d == 0:
				if self.wait_func is not None:
					self.wait_func()
			else:
				self.buff[x:x+d] = buff
				x += d

		self.r_pointer += n
		if self.r_pointer == self.w_pointer:
			ll("Resetting pointers")
			self.r_pointer = 0
			self.w_pointer = 0

		return self.buff[:n]

	def write_next_buffer(self, buff):
		x = len(buff)
		n = 0
		d = 0
		if self.seekable:
			self.rw.seek(self.w_pointer)
		while n < x:
			d = self.rw.write(buff[n:])
			if d == 0:
				if self.wait_func is not None:
					self.wait_func()

			n += d

		self.w_pointer += x
