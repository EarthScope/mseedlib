import os
import sys
import setuptools
from setuptools.dist import Distribution
from setuptools.command.build import build
import subprocess

module_path = os.path.abspath(os.path.dirname(__file__))
package_path = os.path.join(module_path, 'src', 'mseedlib')
libmseed_path = os.path.join(package_path, 'libmseed')


class BuildWithMake(build):
    def run(self):
        # Run our build steps
        self.run_portable_make()

        # call superclass
        build.run(self)

    def run_portable_make(self):
        print("Building libmseed via Makefile")

        if sys.platform.lower().startswith("windows"):
            cmd = f"nmake /f Makefile.win -C {libmseed_path} dll"
        else:
            cmd = f"make -C {libmseed_path} -j shared"
            env = {'CFLAGS': '-O3'}

        subprocess.check_call(cmd, env=env, shell=True)


class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""

    def has_ext_modules(self):
        return True


setuptools.setup(
    cmdclass={'build': BuildWithMake},
    distclass=BinaryDistribution,
)
