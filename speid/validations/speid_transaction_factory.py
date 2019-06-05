class TransactionFactory:
    """
    from: https://realpython.com/factory-method-python/
    """
    def __init__(self):
        self._builders = dict()

    def register_builder(self, key, builder):
        self._builders[key] = builder

    def create(self, key, **kwargs):
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(key)
        return builder(**kwargs)
