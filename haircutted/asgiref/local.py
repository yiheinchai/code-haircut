class Local:
	def __getattr__(self=<asgiref.local.Local object at 0x105eb8ed0>, key='default'):
		with self._thread_lock:
			storage = self._get_storage()
			if key in storage:
				return storage[key]


	def _get_storage(self=<asgiref.local.Local object at 0x105eb8ed0>):
		context_obj = self._get_context_id()
		return getattr(context_obj, self._attr_name)


	def _get_context_id(self=<asgiref.local.Local object at 0x105eb8ed0>):
		from .sync import AsyncToSync, SyncToAsync
		context_id = SyncToAsync.get_current_task()
		context_is_async = True
		if context_id is None:
			context_id = threading.current_thread()
			context_is_async = False
		if self._thread_critical:
			return context_id

