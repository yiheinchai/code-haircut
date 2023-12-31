class QuerySet:
	def __init__(self=<django.db.models.query.QuerySet object at 0x107d1edd0>, model=<django.db.models.base.ModelBase object at 0x1070929d0>, query=<django.db.models.sql.query.Query object at 0x107704590>, using=None, hints={}):
		self.model = model
		self._db = using
		self._hints = hints or {}
		self._query = query or sql.Query(self.model)
		self._result_cache = None
		self._sticky_filter = False
		self._for_write = False
		self._prefetch_related_lookups = ()
		self._prefetch_done = False
		self._known_related_objects = {}  # {rel_field: {pk: rel_obj}}
		self._iterable_class = ModelIterable
		self._fields = None
		self._defer_next_filter = False
		self._deferred_filter = None


	def __getitem__(self=<django.db.models.query.QuerySet object at 0x107c7a350>, k=0):
		if (isinstance(k, int) and k < 0) or (
		isinstance(k, slice)
		qs = self._chain()
		qs.query.set_limits(k, k + 1)
		qs._fetch_all()


	def _chain(self=<django.db.models.query.QuerySet object at 0x107c7a350>):
		obj = self._clone()
		return obj


	def _clone(self=<django.db.models.query.QuerySet object at 0x107c7a350>):
		c = self.__class__(
		model=self.model,
		query=self.query.chain(),
		using=self._db,
		hints=self._hints,
		c._sticky_filter = self._sticky_filter
		c._for_write = self._for_write
		c._prefetch_related_lookups = self._prefetch_related_lookups[:]
		c._known_related_objects = self._known_related_objects
		c._iterable_class = self._iterable_class
		c._fields = self._fields
		return c


	def query(self=<django.db.models.query.QuerySet object at 0x107d1edd0>):
		return self._query


	def _fetch_all(self=<django.db.models.query.QuerySet object at 0x107d1edd0>):


	def db(self=<django.db.models.query.QuerySet object at 0x107d1edd0>):
		return self._db or router.db_for_read(self.model, **self._hints)

class ModelIterable:
	def __init__(self=<django.db.models.query.ModelIterable object at 0x1073ae450>, queryset=<django.db.models.query.QuerySet object at 0x107d1edd0>, chunked_fetch=False, chunk_size=100):
		self.queryset = queryset
		self.chunked_fetch = chunked_fetch
		self.chunk_size = chunk_size


	def __iter__(self=<django.db.models.query.ModelIterable object at 0x1073ae450>):
		queryset = self.queryset
		db = queryset.db
		compiler = queryset.query.get_compiler(using=db)
		results = compiler.execute_sql(
		chunked_fetch=self.chunked_fetch, chunk_size=self.chunk_size
		select, klass_info, annotation_col_map = (
		compiler.select,
		compiler.klass_info,
		compiler.annotation_col_map,
		model_cls = klass_info["model"]
		select_fields = klass_info["select_fields"]
		model_fields_start, model_fields_end = select_fields[0], select_fields[-1] + 1
		init_list = [
		f[0].target.attname for f in select[model_fields_start:model_fields_end]
		related_populators = get_related_populators(klass_info, select, db)
		known_related_objects = [
		for field, related_objs in queryset._known_related_objects.items()
		for row in compiler.results_iter(results):
			obj = model_cls.from_db(
			db, init_list, row[model_fields_start:model_fields_end]
		def __iter__(self=<django.db.models.query.ModelIterable object at 0x1073ae450>):

