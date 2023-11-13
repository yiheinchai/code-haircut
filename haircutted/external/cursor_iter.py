class SimpleLazyObject:
	def cursor_iter(cursor=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, sentinel=[], col_count=None, itersize=100):
		def cursor_iter(cursor=<django.db.backends.utils.CursorDebugWrapper object at 0x107d1f090>, sentinel=[], col_count=None, itersize=100):
		compiler.select,
		compiler.klass_info,
		compiler.annotation_col_map,
		select, klass_info, annotation_col_map = (
		model_cls = klass_info["model"]
		select_fields = klass_info["select_fields"]
		model_fields_start, model_fields_end = select_fields[0], select_fields[-1] + 1
		init_list = [
		f[0].target.attname for f in select[model_fields_start:model_fields_end]
		init_list = [
		related_populators = get_related_populators(klass_info, select, db)
		known_related_objects = [
		for field, related_objs in queryset._known_related_objects.items()
		known_related_objects = [
		obj = model_cls.from_db(
		db, init_list, row[model_fields_start:model_fields_end]
		obj = model_cls.from_db(
		yield obj

