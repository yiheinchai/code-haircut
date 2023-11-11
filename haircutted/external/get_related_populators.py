class SimpleLazyObject:
	def get_related_populators(klass_info={'model': <django.db.models.base.ModelBase object at 0x1070929d0>, 'select_fields': [0, 1, 2]}, select=[(<django.db.models.expressions.Col object at 0x107660910>, ('"polls_question"."id"', []), None), (<django.db.models.expressions.Col object at 0x107660990>, ('"polls_question"."question_text"', []), None), (<django.db.models.expressions.Col object at 0x107660a50>, ('"polls_question"."pub_date"', []), None)], db='default'):
		iterators = []
		related_klass_infos = klass_info.get("related_klass_infos", [])
		for rel_klass_info in related_klass_infos:
		return iterators

