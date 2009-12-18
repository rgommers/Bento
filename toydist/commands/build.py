import os
import sys

from toydist.utils import \
        pprint, expand_glob, find_package
from toydist.package import \
        PackageDescription
from toydist.conv import \
        to_distutils_meta, write_pkg_info
from toydist.installed_package_description import \
        InstalledPkgDescription

from toydist.commands.core import \
        Command
from toydist.commands.configure import \
        ConfigureState

USE_NUMPY_DISTUTILS = True

def build_extensions(extensions):
    # FIXME: import done here to avoid clashing with monkey-patch as done by
    # the convert subcommand.
    if USE_NUMPY_DISTUTILS:
        from numpy.distutils.extension import Extension
        from numpy.distutils.numpy_distribution import NumpyDistribution as Distribution
        from numpy.distutils.command.build_ext import build_ext
        from numpy.distutils.command.build_src import build_src
        from numpy.distutils.command.scons import scons
        from numpy.distutils import log
        import distutils.core
    else:
        from distutils.extension import Extension
        from distutils.dist import Distribution
        from distutils.command.build_ext import build_ext
        from distutils import log

    log.set_verbosity(1)

    dist = Distribution()
    if USE_NUMPY_DISTUTILS:
        dist.cmdclass['build_src'] = build_src
        dist.cmdclass['scons'] = scons
        distutils.core._setup_distribution = dist

    dist.ext_modules = []
    for name, value in extensions.items():
        e = Extension(name, sources=value["sources"])
        dist.ext_modules.append(e)

    bld_cmd = build_ext(dist)
    bld_cmd.initialize_options()
    bld_cmd.finalize_options()
    bld_cmd.run()

    outputs = {}
    for ext in bld_cmd.extensions:
        # FIXME: do package -> location translation correctly
        pkg_dir = os.path.dirname(ext.name.replace('.', os.path.sep))
        target = os.path.join('$sitedir', pkg_dir)
        fullname = bld_cmd.get_ext_fullname(ext.name)
        ext_target = os.path.join(bld_cmd.build_lib,
                                 bld_cmd.get_ext_filename(fullname))
        srcdir = os.path.dirname(ext_target)
        ext_descr = {'files': [os.path.basename(ext_target)],
                     'srcdir': srcdir,
                     'target': target}
        outputs[fullname] = ext_descr
    return outputs

class BuildCommand(Command):
    long_descr = """\
Purpose: build the project
Usage:   toymaker build [OPTIONS]."""
    short_descr = "build the project."

    def run(self, opts):
        self.set_option_parser()
        o, a = self.parser.parse_args(opts)
        if o.help:
            self.parser.print_help()
            return

        if not os.path.exists('.config.bin'):
            pprint('RED', 
                   "You need to run %s configure before building" % SCRIPT_NAME)
        s = ConfigureState.from_dump('.config.bin')

        filename = s.package_description
        scheme = dict([(k, s.paths[k]) for k in s.paths])

        pkg = PackageDescription.from_file(filename)

        # FIXME: root_src
        root_src = ""
        python_files = []
        for p in pkg.packages:
            python_files.extend(find_package(p, root_src))
        for m in pkg.py_modules:
            python_files.append(os.path.join(root_src, '%s.py' % m))

        sections = {"pythonfiles": {"files": python_files,
                                    "target": "$sitedir"}}

        # Get data files
        datafiles = pkg.data_files
        for s, v in datafiles.items():
            srcdir = v["srcdir"]
            files = []
            for f in v["files"]:
                files.extend(expand_glob(f, srcdir))
            v["files"] = files
        sections["datafiles"] = datafiles

        # handle extensions
        if pkg.extensions:
            extensions = build_extensions(pkg.extensions)
            sections["extensions"] = extensions

        if pkg.executables:
            executables = build_executables(pkg.executables)
            sections["executables"] = executables

        meta = {}
        for m in ["name", "version", "summary", "url", "author", "author_email",
                  "license", "download_url", "description", "platforms", "classifiers",
                  "install_requires"]:
            meta[m] = getattr(pkg, m)

        meta["top_levels"] = pkg.top_levels

        p = InstalledPkgDescription(sections, meta, scheme, pkg.executables)
        p.write('installed-pkg-info')

def create_script(name, module, function=None):
    sys_executable = os.path.normpath(sys.executable)
    if function is None:
        raise NotImplementedError("Generating build scripts without function not yet implemented")
    script_text = """\
#!%(python_exec)s
# TOYDIST AUTOGENERATED-CONSOLE SCRIPT
import sys
from %(module)s import %(function)s
%(function)s(sys.argv)
""" % {"python_exec": sys_executable, "module": module, "function": function}
    return script_text

def build_dir():
    # FIXME: handle build directory differently, wo depending on distutils
    from distutils.command.build_scripts import build_scripts
    from distutils.dist import Distribution

    dist = Distribution()

    bld_scripts = build_scripts(dist)
    bld_scripts.initialize_options()
    bld_scripts.finalize_options()
    return bld_scripts.build_dir

def build_executables(executables):
    bdir = build_dir()
    ret = {}

    for name, prop in executables.items():
        cnt = create_script(name, **prop)
        target = os.path.join(bdir, name)
        # FIXME: deal with win32 stuff here
        mode = "b"
        d = os.path.dirname(target)
        if d and not os.path.exists(d):
            os.makedirs(d)
        f = open(target, "w" + mode)
        try:
            f.write(cnt)
        finally:
            f.close()

        name = "executable:%s" % name
        ret[name] = {"files": [os.path.basename(target)],
                     "srcdir": d,
                     "target": "$bindir"}
    return ret