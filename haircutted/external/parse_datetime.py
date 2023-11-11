class SimpleLazyObject:
	def parse_datetime(value='2023-11-08 23:52:21.573273'):
		try:
		return datetime.datetime.fromisoformat(value)

