import sys
import os
import stat

if sys.version_info >= (3, ):
    import glob
    import lib2to3
    import pickle
    from hashlib import md5
    import shutil
    import lib2to3.main
    local_path = os.path.dirname(__file__)
    src_path = os.path.join(local_path, 'build', 'py3k')

    def ensure_dir(path):
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d)

    print("Converting to Python3 via 2to3...")

    files_to_convert = []
    files_to_copy = []
    for pkg in ["bento/core", "bento/commands", "bento/compat", "bentomakerlib",
                "bento/tests"]:
        for root, dirs, files in os.walk(pkg):
            for f in files:
                if f.endswith(".py"):
                    files_to_convert.append(os.path.join(root, f))
                else:
                    files_to_copy.append(os.path.join(root, f))
    files_to_convert.extend(glob.glob("bento/*.py"))
    files_to_convert.extend(glob.glob("bento/private/*.py"))

    ensure_dir(src_path)
    cache = src_path + "/cache.db"
    if os.path.exists(cache):
        fid = open(cache, "rb")
        try:
            checksums = pickle.load(fid)
        finally:
            fid.close()
    else:
        checksums = {}

    filenames = []
    for f in files_to_convert:
        fid = open(f, "rb")
        try:
            checksum = md5(fid.read()).hexdigest()
        finally:
            fid.close()
        cached_checksum = checksums.get(f, "")
        if cached_checksum != checksum:
            checksums[f] = checksum
            target = os.path.join(src_path, f)
            ensure_dir(target)
            shutil.copy(f, target)
            filenames.append(target)

    fid = open(cache, "+wb")
    try:
        pickle.dump(checksums, fid)
    finally:
        fid.close()
    
    for f in filenames:
        lib2to3.main.main("lib2to3.fixes", ['-w'] + [f])

    for pkg in ["bento/private/_ply"]:
        for root, dirs, files in os.walk(pkg):
            for f in files:
                files_to_copy.append(os.path.join(root, f))

    for f in files_to_copy:
        target = os.path.join(src_path, f)
        ensure_dir(target)
        shutil.copy(f, target)

    sys.path.insert(0, src_path)

from bento.core \
    import \
        PackageDescription
from bento.core.utils \
    import \
        pprint

from bento.commands.script_utils \
    import \
        create_posix_script, create_win32_script

def install_inplace(pkg):
    """Install scripts of pkg in the current directory."""
    for name, executable in pkg.executables.items():
        if sys.platform == "win32":
            section = create_win32_script(name, executable, ".")
        else:
            section = create_posix_script(name, executable, ".")
            for f in section.files:
                os.chmod(f, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC | \
                            stat.S_IRGRP | stat.S_IXGRP | \
                            stat.S_IROTH | stat.S_IXOTH)
        installed = ",".join(section.files)
        pprint("GREEN", "installing %s in current directory" % installed)

def build_bootstrap():
    from setup_common import generate_version_py
    #generate_version_py("bento/__dev_version.py")

    pkg = PackageDescription.from_file("bento.info")
    if pkg.executables:
        install_inplace(pkg)

if __name__ == "__main__":
    build_bootstrap()
