class DatabaseOperations:
	def compiler(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, compiler_name='SQLCompiler'):
		return getattr(self._cache, compiler_name)


	def quote_name(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, name='polls_question'):
		return '"%s"' % name
		def quote_name(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, name='id'):
		return '"%s"' % name
		def quote_name(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, name='question_text'):
		return '"%s"' % name
		def quote_name(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, name='pub_date'):
		return '"%s"' % name


	def limit_offset_sql(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, low_mark=0, high_mark=1):
		limit, offset = self._get_limit_offset_params(low_mark, high_mark)
		result.append(
		return " ".join(result), tuple(params)
		self.query.reset_refcounts(refcounts_before)
		cursor = self.connection.cursor()


	def _get_limit_offset_params(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, low_mark=0, high_mark=1):
		offset = low_mark or 0
		return " ".join(
		("LIMIT %d" % limit) if limit else None,
		("OFFSET %d" % offset) if offset else None,
		for sql in (
		return " ".join(


	def last_executed_query(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, cursor=<django.db.backends.sqlite3.base.SQLiteCursorWrapper object at 0x107d0b920>, sql='SELECT "polls_question"."id", "polls_question"."question_text", "polls_question"."pub_date" FROM "polls_question" LIMIT 1', params=()):
		return sql


	def get_db_converters(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, expression=<django.db.models.expressions.Col object at 0x107660910>):
		converters = super().get_db_converters(expression)
		def get_db_converters(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, expression=<django.db.models.expressions.Col object at 0x107660910>):
		return []
		internal_type = expression.output_field.get_internal_type()
		return converters
		def get_db_converters(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, expression=<django.db.models.expressions.Col object at 0x107660990>):
		converters = super().get_db_converters(expression)
		def get_db_converters(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, expression=<django.db.models.expressions.Col object at 0x107660990>):
		return []
		internal_type = expression.output_field.get_internal_type()
		return converters
		def get_db_converters(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, expression=<django.db.models.expressions.Col object at 0x107660a50>):
		converters = super().get_db_converters(expression)
		def get_db_converters(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, expression=<django.db.models.expressions.Col object at 0x107660a50>):
		return []
		internal_type = expression.output_field.get_internal_type()
		if internal_type == "DateTimeField":
			converters.append(self.convert_datetimefield_value)
		return converters


	def convert_datetimefield_value(self=<django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>, value=datetime(2023, 11, 8, 23, 52, 21, 573273, tzinfo=None, fold=0), expression=<django.db.models.expressions.Col object at 0x107660a50>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		value = timezone.make_aware(value, self.connection.timezone)
		return value

