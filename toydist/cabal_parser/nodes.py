from toydist.cabal_parser.utils import \
    comma_list_split
from toydist.utils import \
    expand_glob

class DataFiles(object):
    @classmethod
    def from_parse_dict(cls, name, d):
        kw = {}
        kw["target"] = d["target"]
        kw["srcdir"] = d.get("srcdir", None)
        kw["files"] = d.get('files', None)
        if kw["files"]:
            kw["files"] = comma_list_split(kw['files'])

        return cls(name=name, **kw)

    def __init__(self, name, files=None, target=None, srcdir=None):
        self.name = name

        if files is not None:
            self.files = files
        else:
            self.files = []

        if target is not None:
            self.target = target
        else:
            self.target = "$sitedir"

        if srcdir is not None:
            self.srcdir = srcdir
        else:
            self.srcdir = "."

    # FIXME: this function should not really be here...
    def resolve_glob(self):
        """Expand any glob pattern in the files section relatively to the
        current value for source direcory."""
        files = []
        for f in self.files:
            files.extend(expand_glob(f, self.srcdir))
        return files

    def __repr__(self):
        return repr({"files": self.files, "srcdir": self.srcdir, "target": self.target})

class Executable(object):
    @classmethod
    def from_parse_dict(cls, name, d):
        return cls(name, **d)

    @classmethod
    def from_representation(cls, s):
        if not "=" in s:
            raise ValueError("s should be of the form name=module:function")
        name, value = [j.strip() for j in s.split("=")]
        if not ":" in value:
            raise ValueError(
                "string representation should be of the form module:function, not %s"
                % value)
        module, function = value.split(":", 1)
        return cls(name, module, function)

    def __init__(self, name, module, function):
        # FIXME: check that module is a module name ?
        self.name = name
        self.module = module
        self.function = function

    # FIXME: this function should not really be here...
    def representation(self):
        return ":".join([self.module, self.function])

    # FIXME: this function should not really be here...
    def full_representation(self):
        return "%s=%s" % (self.name, self.representation())

    def __repr__(self):
        return repr({"name": self.name, "module": self.module, "function": self.function})
