import abc

class Message(object):


	def marshal_binary(self):
		"""Must return a string"""
		raise NotImplementedError

	def unmarshal_binary(self, data):
		"""Given a string, decode it into this class"""
		raise NotImplementedError


class MockMessage(Message):

	def __init__(self, msg):
		self.msg = str(msg)

	def marshal_binary(self):
		return bytearray(self.msg,"utf8")

	def unmarshal_binary(self, buff):
		self.msg = str(buff)

	def __str__(self):
		return self.msg
