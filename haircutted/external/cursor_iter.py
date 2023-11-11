class SimpleLazyObject:
	def cursor_iter(cursor=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, sentinel=[], col_count=None, itersize=100):
		for rows in iter((lambda: cursor.fetchmany(itersize)), sentinel):
		cursor.close()

