class is_aware:
	def is_aware(value=datetime(2023, 11, 8, 23, 52, 21, 573273, tzinfo=None, fold=0)):
		return value.utcoffset() is not None

