class SimpleLazyObject:
	def cursor_iter(cursor=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, sentinel=[], col_count=None, itersize=100):
		try:
			for rows in iter((lambda: cursor.fetchmany(itersize)), sentinel):
		def cursor_iter(cursor=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, sentinel=[], col_count=None, itersize=100):
		cursor.close()

