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
		try:
			sql, params = self.as_sql()
		cursor = self.connection.cursor()
		try:
			cursor.execute(sql, params)
		result = cursor_iter(
		cursor,
		self.connection.features.empty_fetchmany_value,
		self.col_count if self.has_extra_select else None,
		chunk_size,
		return list(result)


	def as_sql(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, with_limits=True, with_col_aliases=False):
		refcounts_before = self.query.alias_refcount.copy()
		try:
			combinator = self.query.combinator
			extra_select, order_by, group_by = self.pre_sql_setup(
			with_col_aliases=with_col_aliases or bool(combinator),
		for_update_part = None
		with_limit_offset = with_limits and self.query.is_sliced
		combinator = self.query.combinator
		features = self.connection.features
		distinct_fields, distinct_params = self.get_distinct()
		from_, f_params = self.get_from_clause()
		self.compile(self.where) if self.where is not None else ("", [])
		except FullResultSet:
			where, w_params = "", []
		having, h_params = (
		if self.having is not None
		else ("", [])
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
		if with_limit_offset:
			result.append(
			self.connection.ops.limit_offset_sql(
			self.query.low_mark, self.query.high_mark
		return " ".join(result), tuple(params)
		self.query.reset_refcounts(refcounts_before)


	def pre_sql_setup(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, with_col_aliases=False):
		self.setup_query(with_col_aliases=with_col_aliases)
		order_by = self.get_order_by()
		self.where, self.having, self.qualify = self.query.where.split_having_qualify(
		must_group_by=self.query.group_by is not None
		extra_select = self.get_extra_select(order_by, self.select)
		self.has_extra_select = bool(extra_select)
		group_by = self.get_group_by(self.select + extra_select, order_by)
		return extra_select, order_by, group_by


	def setup_query(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, with_col_aliases=False):
		if all(self.query.alias_refcount[a] == 0 for a in self.query.alias_map):
			self.query.get_initial_alias()
			self.select, self.klass_info, self.annotation_col_map = self.get_select(
			with_col_aliases=with_col_aliases,
		self.col_count = len(self.select)


	def get_select(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, with_col_aliases=False):
		select = []
		klass_info = None
		annotations = {}
		select_idx = 0
		assert not (self.query.select and self.query.default_cols)
		select_mask = self.query.get_select_mask()
		if self.query.default_cols:
			cols = self.get_default_columns(select_mask)
		if cols:
			select_list = []
			for col in cols:
				select_list.append(select_idx)
				select.append((col, None))
				select_idx += 1
		klass_info = {
		"model": self.query.model,
		"select_fields": select_list,
		ret = []
		col_idx = 1
		for col, alias in select:
		try:
		sql, params = self.compile(col)
		sql, params = col.select_format(self, sql, params)
		ret.append((col, (sql, params), alias))
		return ret, klass_info, annotations


	def get_default_columns(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, select_mask={}, start_alias=None, opts=None, from_parent=None):
		result = []
		start_alias = start_alias or self.query.get_initial_alias()
		seen_models = {None: start_alias}
		for field in opts.concrete_fields:
		model = field.model._meta.concrete_model
		if model == opts.model:
		model = None
		if (
		from_parent
		alias = self.query.join_parent_model(opts, model, start_alias, seen_models)
		column = field.get_col(alias)
		result.append(column)
		return result


	def compile(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, node=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>):
		vendor_impl = getattr(node, "as_" + self.connection.vendor, None)
		sql, params = node.as_sql(self, self.connection)
		return sql, params


	def quote_name_unless_alias(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, name='polls_question'):
		if name in self.quote_cache:
			return self.quote_cache[name]
		(name in self.query.alias_map and name not in self.query.table_map)
		or name in self.query.extra_select
		self.query.external_aliases.get(name)
		r = self.connection.ops.quote_name(name)
		self.quote_cache[name] = r
		return r


	def get_order_by(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>):
		result = []
		seen = set()
		return result


	def _order_by_pairs(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>):
		ordering = []
		if self.query.standard_ordering:
			default_order, _ = ORDER_DIR["ASC"]
		selected_exprs = {}


	def get_extra_select(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, order_by=[], select=[(<django.db.models.expressions.Col object at 0x107660910>, ('"polls_question"."id"', []), None), (<django.db.models.expressions.Col object at 0x107660990>, ('"polls_question"."question_text"', []), None), (<django.db.models.expressions.Col object at 0x107660a50>, ('"polls_question"."pub_date"', []), None)]):
		extra_select = []
		return extra_select


	def get_group_by(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, select=[(<django.db.models.expressions.Col object at 0x107660910>, ('"polls_question"."id"', []), None), (<django.db.models.expressions.Col object at 0x107660990>, ('"polls_question"."question_text"', []), None), (<django.db.models.expressions.Col object at 0x107660a50>, ('"polls_question"."pub_date"', []), None)], order_by=[]):
		if self.query.group_by is None:
			return []


	def get_distinct(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>):
		result = []
		params = []
		opts = self.query.get_meta()
		return result, params


	def get_from_clause(self=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>):
		result = []
		params = []
		try:
			from_clause = self.query.alias_map[alias]
		clause_sql, clause_params = self.compile(from_clause)
		result.append(clause_sql)
		params.extend(clause_params)
		return result, params


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

