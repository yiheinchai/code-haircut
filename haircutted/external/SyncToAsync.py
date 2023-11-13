class Local:
	def get_current_task():
		try:
			return asyncio.current_task()
			except RuntimeError:
				return None

