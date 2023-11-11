class CursorDebugWrapper:
	def __init__(self=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, cursor=<django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x107d0b920>, db=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		self.cursor = cursor
		self.db = db


	def execute(self=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, sql='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', params=()):
		return self._execute_with_wrappers(
		sql, params, many=False, executor=self._execute
		return self._execute_with_wrappers(
		with self.debug_sql(sql, params, use_last_executed_query=True):


	def debug_sql(self=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, sql='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', params=(), use_last_executed_query=True, many=False):
		stop = time.monotonic()
		duration = stop - start
		if use_last_executed_query:
		sql = self.db.ops.last_executed_query(self.cursor, sql, params)
		try:
		times = len(params) if many else ""
		self.db.queries_log.append(
		"sql": "%s times: %s" % (times, sql) if many else sql,
		"time": "%.3f" % duration,
		{
		self.db.queries_log.append(
		logger.debug(
		"(%.3f) %s; args=%s; alias=%s",
		duration,
		sql,
		params,
		self.db.alias,
		"duration": duration,
		"sql": sql,
		"params": params,
		"alias": self.db.alias,
		extra={
		logger.debug(


	def _execute_with_wrappers(self=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, sql='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', params=(), many=False, executor=<bound method CursorWrapper._execute of <django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>>):
		context = {"connection": self.db, "cursor": self}
		for wrapper in reversed(self.db.execute_wrappers):
		return executor(sql, params, many, context)


	def _execute(self=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, sql='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', params=(), *ignored_wrapper_args=(False, {'connection': <django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>, 'cursor': <django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>})):
		self.db.validate_no_broken_transaction()
		with self.db.wrap_database_errors:
		return self.cursor.execute(sql, params)
		with self.db.wrap_database_errors:


	def __getattr__(self=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, attr='close'):
		cursor_attr = getattr(self.cursor, attr)
		return cursor_attr

