import pathlib

class _MockAccessor:
    pass

class _MockFlavour:
    pass

class MockPath(pathlib.Path):
    _accessor = _MockAccessor()
    _flavour = _MockFlavour()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
