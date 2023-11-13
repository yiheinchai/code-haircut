class DatabaseOperations:
	def compiler(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, compiler_name='SQLCompiler'):
		return getattr(self._cache, compiler_name)


	def quote_name(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, name='pub_date'):
		return '"%s"' % name


	def limit_offset_sql(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, low_mark=0, high_mark=1):
		limit, offset = self._get_limit_offset_params(low_mark, high_mark)
		return " ".join(
		for sql in (
		("LIMIT %d" % limit) if limit else None,
		("OFFSET %d" % offset) if offset else None,


	def _get_limit_offset_params(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, low_mark=0, high_mark=1):
		offset = low_mark or 0
		if high_mark is not None:
			return (high_mark - offset), offset


	def last_executed_query(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, cursor=<django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x107d0b920>, sql='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', params=()):
		return sql


	def get_db_converters(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, expression=<django.db.models.expressions.Col object at 0x107660a50>):
		converters = super().get_db_converters(expression)
		internal_type = expression.output_field.get_internal_type()
		if internal_type == "DateTimeField":
			converters.append(self.convert_datetimefield_value)
		return converters
		def get_db_converters(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, expression=<django.db.models.expressions.Col object at 0x107660a50>):
		return []


	def convert_datetimefield_value(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, value=datetime(2023, 11, 8, 23, 52, 21, 573273, tzinfo=None, fold=0), expression=<django.db.models.expressions.Col object at 0x107660a50>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		if settings.USE_TZ and not timezone.is_aware(value):
			value = timezone.make_aware(value, self.connection.timezone)
			return value

