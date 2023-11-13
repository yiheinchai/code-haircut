class Local:
	def get_current_task():
		try:
			! get_current_task: (<class 'RuntimeError'>, RuntimeError('no running event loop'), <traceback object at 0x107d1e680>)
			context_is_async = True
		if context_id is None:
			context_id = threading.current_thread()
			context_is_async = False
		return getattr(context_obj, self._attr_name)

