class DatabaseWrapper:
	def cursor(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		return self._cursor()


	def _cursor(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>, name=None):
		self.close_if_health_check_failed()
		self.ensure_connection()


	def close_if_health_check_failed(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		self.connection is None
		or not self.health_check_enabled
		return


	def ensure_connection(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):


	def create_cursor(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>, name=None):
		return self.connection.cursor(factory=SQLiteCursorWrapper)


	def _prepare_cursor(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>, cursor=<django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x107d0b920>):
		self.validate_thread_sharing()


	def validate_thread_sharing(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		wrapped_cursor = self.make_debug_cursor(cursor)
		return wrapped_cursor


	def allow_thread_sharing(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		with self._thread_sharing_lock:
			return self._thread_sharing_count > 0


	def queries_logged(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		return self.force_debug_cursor or settings.DEBUG


	def make_debug_cursor(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>, cursor=<django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x107d0b920>):
		return utils.CursorDebugWrapper(cursor, self)


	def validate_no_broken_transaction(self=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		return self.cursor.execute(sql, params)

class SQLiteCursorWrapper:
	def execute(self=<django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x107d0b920>, query='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', params=()):
		param_names = list(params) if isinstance(params, Mapping) else None
		query = self.convert_query(query, param_names=param_names)
		return super().execute(query, params)


	def convert_query(self=<django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x107d0b920>, query='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', param_names=None):
		return FORMAT_QMARK_REGEX.sub("?", query).replace("%%", "%")

