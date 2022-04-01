import pathlib
import secrets


class _MockAccessor:
    pass


class _MockFlavour:
    sep = '‖'
    altsep = '/'
    has_drv = False
    is_supported = True

    def parse_parts(self, parts):
        drv = root = ''
        parsed = []
        for part in reversed(parts):
            parsed.extend(part.replace(altsep, sep).split(sep))
        parsed.reverse()
        return '', '', parsed


class MockPath(pathlib.Path):
    _accessor = _MockAccessor()
    _flavour = _MockFlavour()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MockFile:
    def __new__(cls, path, *args, **kwargs):
        if isinstance(path, MockFile):
            return path
        return super().__new__(cls)

    def __init__(self, path, contents=None):
        if isinstance(path, MockFile):
            # Already initialised in __new__
            return
        self.path = path
        self.contents = contents

    def __repr__(self):
        content = repr(self.contents)
        r = f"<{self.path}:{content}>"
        if len(r) > 80:
            r = f"{r[:75]}{content[-1:]}...>"
        return r

    def __hash__(self):
        return hash((self.path, self.contents))

    def __eq__(self, other):
        return self.path == other.path and self.contents == other.contents

    def __ne__(self, other):
        return self.path != other.path or self.contents != other.contents


class MockFilesystem:
    def __init__(
        self,
        files,
        *,
        scratch_dir = None,
        rmtree_scratch_dir = None,
        prefix = None,
    ):
        self._prefix = MockPath(prefix or secrets.token_hex(8))
        self._scratch = pathlib.Path(scratch_dir or tempfile.mkdtemp())
        if rmtree_scratch_dir is None:
            self._rmtree_scratch = not scratch_dir
        else:
            self._rmtree_scratch = rmtree_scratch_dir
        self._scratch_map = {}

        self.warnings = []

        self._files = _files = {}
        for file in files:
            if isinstance(file, tuple):
                file = MockFile(*file)
            elif isinstance(file, str):
                file = MockFile(file)
            _files[pathlib.PurePath(file.path).parts] = file

    def __enter__(self):
        self.warnings.clear()
        self._scratch_map.clear()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        # TODO: somehow elevate warnings
        any_fail = False
        if any_fail and not exc_type:
            raise RuntimeError("pick a better error")

    def __bool__(self):
        return bool(self._files)

    def __len__(self):
        return len(self._files)

    def __iter__(self):
        p = self._prefix
        for f in self._files:
            yield p / f

    def __getitem__(self, key):
        # Unmodified path coming back in
        try:
            f = key.relative_to(self._prefix)
        except ValueError:
            pass
        else:
            return self._files[f.parts]

        # Path that was resolved to actual scratch space
        try:
            f = key.relative_to(self._scratch)
        except ValueError:
            pass
        else:
            f = self._scratch_map[f.parts]
            self.warnings.append(f"{f} passed through scratch space but came back via __getitem__")
            return f

        # Not one of ours!
        self.warnings.append(f"Attempted to acess {f} through MockFilesystem")
        raise LookupError(key)
