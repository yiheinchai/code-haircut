class Node:
	def __init__(self=<django.utils.tree.Node object at 0x107d1ecd0>, children=None, connector='AND', negated=False):
		self.children = children[:] if children else []
		self.connector = connector or self.default
		self.negated = negated

