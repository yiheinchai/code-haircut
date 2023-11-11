class Local:
	def get_current_task():
		try:
		return asyncio.current_task()
		! get_current_task: (<class 'RuntimeError'>, RuntimeError('no running event loop'), <traceback object at 0x107d1e680>)
		except RuntimeError:
		return None

