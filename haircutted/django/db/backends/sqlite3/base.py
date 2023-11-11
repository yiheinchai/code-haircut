class SQLiteCursorWrapper:
	def execute(self=<django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x107d0b920>, query='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', params=()):
		param_names = list(params) if isinstance(params, Mapping) else None
		query = self.convert_query(query, param_names=param_names)
		return super().execute(query, params)


	def convert_query(self=<django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x107d0b920>, query='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', param_names=None):
		return FORMAT_QMARK_REGEX.sub("?", query).replace("%%", "%")

