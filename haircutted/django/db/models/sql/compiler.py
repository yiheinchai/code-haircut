class SQLCompiler:
	def __init__(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, query=<django.db.models.sql.query.Query object at 0x107704590>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>, using='default', elide_empty=True):
		self.query = query
		self.connection = connection
		self.using = using
		self.elide_empty = elide_empty
		self.quote_cache = {"*": "*"}
		self.select = None
		self.annotation_col_map = None
		self.klass_info = None
		self._meta_ordering = None


	def execute_sql(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, result_type='multi', chunked_fetch=False, chunk_size=100):
		result_type = result_type or NO_RESULTS


	def as_sql(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, with_limits=True, with_col_aliases=False):
		refcounts_before = self.query.alias_refcount.copy()


	def pre_sql_setup(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, with_col_aliases=False):
		self.setup_query(with_col_aliases=with_col_aliases)


	def setup_query(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, with_col_aliases=False):
		if all(self.query.alias_refcount[a] == 0 for a in self.query.alias_map):
			self.query.get_initial_alias()


	def get_select(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, with_col_aliases=False):
		select = []
		klass_info = None
		annotations = {}
		select_idx = 0


	def get_default_columns(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, select_mask={}, start_alias=None, opts=None, from_parent=None):
		result = []


	def compile(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, node=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>):
		vendor_impl = getattr(node, "as_" + self.connection.vendor, None)
		sql, params = node.as_sql(self, self.connection)
		self.col_count = len(self.select)
		result.append(clause_sql)
		params.extend(clause_params)
		return result, params
		! as_sql: (<class 'django.core.exceptions.FullResultSet'>, FullResultSet(), <traceback object at 0x107d1f300>)
		except FullResultSet:
			where, w_params = "", []
		if self.having is not None
		else ("", [])
		having, h_params = (
		result = ["SELECT"]
		params = []
		out_cols = []
		params.extend(s_params)
		out_cols.append(s_sql)
		result += [", ".join(out_cols)]
		if from_:
			result += ["FROM", *from_]
		params.extend(f_params)
		grouping = []


	def quote_name_unless_alias(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, name='polls_question'):
		(name in self.query.alias_map and name not in self.query.table_map)
		or name in self.query.extra_select
		return sql, []
		return sql, params
		return base_sql + alias_str, []


	def get_order_by(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>):
		result = []
		seen = set()


	def _order_by_pairs(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>):
		self.where, self.having, self.qualify = self.query.where.split_having_qualify(
		must_group_by=self.query.group_by is not None


	def get_extra_select(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, order_by=[], select=[(<django.db.models.expressions.Col object at 0x107660910>, ('"polls_question"."id"', []), None), (<django.db.models.expressions.Col object at 0x107660990>, ('"polls_question"."question_text"', []), None), (<django.db.models.expressions.Col object at 0x107660a50>, ('"polls_question"."pub_date"', []), None)]):
		extra_select = []
		return extra_select


	def get_group_by(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, select=[(<django.db.models.expressions.Col object at 0x107660910>, ('"polls_question"."id"', []), None), (<django.db.models.expressions.Col object at 0x107660990>, ('"polls_question"."question_text"', []), None), (<django.db.models.expressions.Col object at 0x107660a50>, ('"polls_question"."pub_date"', []), None)], order_by=[]):
		return extra_select, order_by, group_by


	def get_distinct(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>):
		result = []
		params = []
		opts = self.query.get_meta()
		from_, f_params = self.get_from_clause()


	def get_from_clause(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>):
		result = []
		params = []
		try:
			from_clause = self.query.alias_map[alias]
		clause_sql, clause_params = self.compile(from_clause)
		self.compile(self.where) if self.where is not None else ("", [])


	def results_iter(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, results=[[(1, 'are you gay?', datetime(2023, 11, 8, 23, 52, 21, 573273, tzinfo=None, fold=0))]], tuple_expected=False, chunked_fetch=False, chunk_size=100):
		fields = [s[0] for s in self.select[0 : self.col_count]]
		converters = self.get_converters(fields)
		rows = chain.from_iterable(results)
		if converters:
			rows = self.apply_converters(rows, converters)
		return rows


	def get_converters(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, expressions=[<django.db.models.expressions.Col object at 0x107660910>, <django.db.models.expressions.Col object at 0x107660990>, <django.db.models.expressions.Col object at 0x107660a50>]):
		converters = {}
			for i, expression in enumerate(expressions):
				if expression:
					backend_converters = self.connection.ops.get_db_converters(expression)
		field_converters = expression.get_db_converters(self.connection)
		if backend_converters or field_converters:
			converters[i] = (backend_converters + field_converters, expression)
		return converters


	def apply_converters(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, rows=<itertools.chain object at 0x1076596c0>, converters={2: ([<bound method DatabaseOperations.convert_datetimefield_value of <django.db.backends.sqlite3.operations.DatabaseOperations object at 0x107277850>>], <django.db.models.expressions.Col object at 0x107660a50>)}):
		connection = self.connection
		converters = list(converters.items())
		for row in map(list, rows):
			for pos, (convs, expression) in converters:
				value = row[pos]
				for converter in convs:
					value = converter(value, expression, connection)
		row[pos] = value
		def apply_converters(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, rows=<itertools.chain object at 0x1076596c0>, converters=[(2, ([<bound method DatabaseOperations.convert_datetimefield_value of ...>], <django.db.models.expressions.Col object at 0x107660a50>))]):

