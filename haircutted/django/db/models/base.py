class ModelBase:
	def from_db(cls=<django.db.models.base.ModelBase object at 0x1070929d0>, db='default', field_names=['id', 'question_text', 'pub_date'], values=[1, 'are you gay?', datetime(2023, 11, 8, 23, 52, 21, 573273, tzinfo=<datetime.timezone object at 0x1055000d0>, fold=0)]):
		new = cls(*values)
		new._state.adding = False
		new._state.db = db
		return new

