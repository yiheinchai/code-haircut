class Query:
	def __init__(self=<django.db.models.sql.query.Query object at 0x10766d8d0>, model=<django.db.models.base.ModelBase object at 0x1070929d0>, alias_cols=True):
		self.model = model
		self.alias_refcount = {}
		self.alias_map = {}
		self.alias_cols = alias_cols
		self.external_aliases = {}
		self.table_map = {}  # Maps table names to list of aliases.
		self.used_aliases = set()
		self.where = WhereNode()
		self.annotations = {}
		self.extra = {}  # Maps col_alias -> (col_sql, params).
		self._filtered_relations = {}


	def chain(self=<django.db.models.sql.query.Query object at 0x10766d8d0>, klass=None):
		obj = self.clone()
		if not obj.filter_is_sticky:
			obj.used_aliases = set()
			obj.filter_is_sticky = False
		return obj


	def clone(self=<django.db.models.sql.query.Query object at 0x10766d8d0>):
		obj = Empty()
		obj.__class__ = self.__class__
		obj.__dict__ = self.__dict__.copy()
		obj.alias_refcount = self.alias_refcount.copy()
		obj.alias_map = self.alias_map.copy()
		obj.external_aliases = self.external_aliases.copy()
		obj.table_map = self.table_map.copy()
		obj.where = self.where.clone()
		obj.annotations = self.annotations.copy()
		obj._annotation_select_cache = None
		obj.extra = self.extra.copy()
		obj.used_aliases = self.used_aliases.copy()
		obj._filtered_relations = self._filtered_relations.copy()
		obj.__dict__.pop("base_table", None)
		return obj


	def set_limits(self=<django.db.models.sql.query.Query object at 0x107704590>, low=0, high=1):
		self.high_mark = self.low_mark + high
		if low is not None:
			if self.high_mark is not None:
				self.low_mark = min(self.high_mark, self.low_mark + low)


	def get_compiler(self=<django.db.models.sql.query.Query object at 0x107704590>, using='default', connection=None, elide_empty=True):
		if using:
			connection = connections[using]
		return connection.ops.compiler(self.compiler)(
		self, connection, using, elide_empty


	def get_initial_alias(self=<django.db.models.sql.query.Query object at 0x107704590>):
		elif self.model:
			alias = self.join(self.base_table_class(self.get_meta().db_table, None))
		return alias
		if self.alias_map:
			alias = self.base_table
		self.ref_alias(alias)


	def get_meta(self=<django.db.models.sql.query.Query object at 0x107704590>):
		if self.model:
			return self.model._meta


	def join(self=<django.db.models.sql.query.Query object at 0x107704590>, join=<django.db.models.sql.datastructures.BaseTable object at 0x10766ded0>, reuse=None):
		reuse_aliases = [
		for a, j in self.alias_map.items()
		alias, _ = self.table_alias(
		join.table_name, create=True, filtered_relation=join.filtered_relation
		join.table_alias = alias
		self.alias_map[alias] = join
		return alias


	def table_alias(self=<django.db.models.sql.query.Query object at 0x107704590>, table_name='polls_question', create=True, filtered_relation=None):
		alias_list = self.table_map.get(table_name)
		filtered_relation.alias if filtered_relation is not None else table_name
		alias = (
		self.table_map[table_name] = [alias]
		self.alias_refcount[alias] = 1
		return alias, True


	def extra_select(self=<django.db.models.sql.query.Query object at 0x107704590>):
		if not self.extra:
			return {}


	def get_select_mask(self=<django.db.models.sql.query.Query object at 0x107704590>):
		field_names, defer = self.deferred_loading
		if not field_names:
			return {}


	def base_table(self=<django.db.models.sql.query.Query object at 0x107704590>):
		for alias in self.alias_map:
			return alias


	def ref_alias(self=<django.db.models.sql.query.Query object at 0x107704590>, alias='polls_question'):
		self.alias_refcount[alias] += 1


	def join_parent_model(self=<django.db.models.sql.query.Query object at 0x107704590>, opts=<django.db.models.options.Options object at 0x107275390>, model=None, alias='polls_question', seen={None: 'polls_question'}):
		if model in seen:
			return seen[model]


	def annotation_select(self=<django.db.models.sql.query.Query object at 0x107704590>):
		elif not self.annotations:
			return {}


	def is_sliced(self=<django.db.models.sql.query.Query object at 0x107704590>):
		return self.low_mark != 0 or self.high_mark is not None


	def reset_refcounts(self=<django.db.models.sql.query.Query object at 0x107704590>, to_counts={}):
		for alias, cur_refcount in self.alias_refcount.copy().items():
			unref_amount = cur_refcount - to_counts.get(alias, 0)
			self.unref_alias(alias, unref_amount)


	def unref_alias(self=<django.db.models.sql.query.Query object at 0x107704590>, alias='polls_question', amount=2):
		self.alias_refcount[alias] -= amount

