class Local:
	def __getattr__(self=<asgiref.local.Local object at 0x105eb8ed0>, key='default'):


	def _get_storage(self=<asgiref.local.Local object at 0x105eb8ed0>):
		context_obj = self._get_context_id()
		results = compiler.execute_sql(
		chunked_fetch=self.chunked_fetch, chunk_size=self.chunk_size
		results = compiler.execute_sql(


	def _get_context_id(self=<asgiref.local.Local object at 0x105eb8ed0>):
		from .sync import AsyncToSync, SyncToAsync
		context_id = SyncToAsync.get_current_task()
		return connection.ops.compiler(self.compiler)(
		self, connection, using, elide_empty
		return connection.ops.compiler(self.compiler)(

