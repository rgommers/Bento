"""
Cache version 1

db["version"] : version number
db["magic"]   : "BENTOMAGIC"
db["bento_checkums"] : pickled dictionary {filename: checksum(filename)} for
                       each bento.info (including subentos)
db["package_description"] : pickled PackageDescription instance
db["user_flags"] : pickled user_flags dict
db["parsed_dict"]: raw parsed dictionary (as returned by raw_parse,
                   before having been seen by the visitor)
"""
import os
import tempfile
import cPickle
try:
    from hashlib import md5
except ImportError:
    import md5

from bento._config \
    import \
        DB_FILE
from bento.core.parser.api \
    import \
        raw_parse
from bento.core.package \
    import \
        raw_to_pkg_kw, PackageDescription
from bento.core.options \
    import \
        raw_to_options_kw, PackageOptions
from bento.core.utils \
    import \
        ensure_dir, rename

class CachedPackage(object):
    __version__ = "1"
    __magic__ = "BENTOMAGIC"

    def __init__(self, db_location=DB_FILE):
        self._location = db_location
        self._first_time = False
        if not os.path.exists(db_location):
            ensure_dir(db_location)
            self.db = {}
            self.db["magic"] = CachedPackage.__magic__
            self.db["version"] = CachedPackage.__version__
            self._first_time = True
        else:
            self.db = cPickle.load(open(db_location))
            try:
                magic = self.db["magic"]
                if not magic == self.__magic__:
                    raise ValueError("Db is not a cached package db !")
            except KeyError:
                raise ValueError("Db is not a cached package db !")

            version = self.db["version"]
            if version != self.__version__:
                raise ValueError("Invalid db version")

    def has_changed(self):
        if self.db.has_key("bentos_checksums"):
            r_checksums = cPickle.loads(self.db["bentos_checksums"])
            for f in r_checksums:
                checksum = md5(open(f).read()).hexdigest()
                if checksum != r_checksums[f]:
                    return True
            return False
        else:
            return True

    def get_package(self, filename, user_flags=None):
        if self._first_time:
            self._first_time = False
            return _create_package_nocached(filename, user_flags, self.db)
        else:
            if self.has_changed():
                return _create_package_nocached(filename, user_flags, self.db)
            else:
                r_user_flags = cPickle.loads(self.db["user_flags"])
                if user_flags is None:
                    # FIXME: this case is wrong
                    return cPickle.loads(self.db["package_description"])
                elif r_user_flags != user_flags:
                    return _create_package_nocached(filename, user_flags, self.db)
                else:
                    raw = cPickle.loads(self.db["parsed_data"])
                    return _raw_to_pkg(raw, user_flags, filename)

    def get_options(self, filename):
        if self._first_time:
            self._first_time = False
            return _create_options_nocached(filename, {}, self.db)
        else:
            if self.has_changed():
                return _create_options_nocached(filename, {}, self.db)
            else:
                raw = cPickle.loads(self.db["parsed_dict"])
                return _raw_to_options(raw)

    def close(self):
        f = tempfile.NamedTemporaryFile(mode="wb", delete=False)
        try:
            cPickle.dump(self.db, f)
        finally:
            f.close()
            rename(f.name, self._location)

def _create_package_nocached(filename, user_flags, db):
    pkg, options = _create_objects_no_cached(filename, user_flags, db)
    return pkg

def _create_options_nocached(filename, user_flags, db):
    pkg, options = _create_objects_no_cached(filename, user_flags, db)
    return options

def _raw_to_options(raw):
    kw = raw_to_options_kw(raw)
    return PackageOptions(**kw)

def _raw_to_pkg(raw, user_flags, filename):
    kw, files = raw_to_pkg_kw(raw, user_flags, filename)
    files.append(filename)

    pkg = PackageDescription(**kw)
    # FIXME: find a better way to automatically include the
    # bento.info file
    pkg.extra_source_files.append(filename)
    return pkg, files

def _create_objects_no_cached(filename, user_flags, db):
    info_file = open(filename, 'r')
    try:
        data = info_file.read()
        raw = raw_parse(data, filename)

        pkg, files = _raw_to_pkg(raw, user_flags, filename)
        options = _raw_to_options(raw)

        checksums = [md5(open(f).read()).hexdigest() for f in files]
        db["bentos_checksums"] = cPickle.dumps(dict(zip(files, checksums)))
        db["package_description"] = cPickle.dumps(pkg)
        db["user_flags"] = cPickle.dumps(user_flags)
        db["parsed_dict"] = cPickle.dumps(raw)

        return pkg, options
    finally:
        info_file.close()
