class ModelIterable:
	def __init__(self=<django.db.models.query.ModelIterable object at 0x1073ae450>, queryset=<django.db.models.query.QuerySet object at 0x107d1edd0>, chunked_fetch=False, chunk_size=100):
		self.queryset = queryset
		self.chunked_fetch = chunked_fetch
		self.chunk_size = chunk_size


	def __iter__(self=<django.db.models.query.ModelIterable object at 0x1073ae450>):
		for row in compiler.results_iter(results):

