import os
import sys
import shutil
import subprocess

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        here = os.path.abspath(os.path.dirname(__file__))
        package_path = os.path.join(here, 'src', 'mseedlib')
        libmseed_path = os.path.join(package_path, 'libmseed')

        print(f"Building libmseed via Makefile in {libmseed_path}")

        if sys.platform.lower().startswith("windows"):
            cmd = f"nmake /f Makefile.win -C {libmseed_path} dll"
        else:
            cmd = f"make -C {libmseed_path} -j shared"
            env = {'CFLAGS': '-O3'}

        subprocess.check_call(cmd, env=env, shell=True)

        # Copy shared library to root package location
        if os.path.exists(os.path.join(libmseed_path, 'libmseed.so')):
            shutil.copy(os.path.join(libmseed_path, 'libmseed.so'),
                        os.path.join(package_path))
        elif os.path.exists(os.path.join(libmseed_path, 'libmseed.dylib')):
            shutil.copy(os.path.join(libmseed_path, 'libmseed.dylib'),
                        os.path.join(package_path))
        elif os.path.exists(os.path.join(libmseed_path, 'libmseed.dll')):
            shutil.copy(os.path.join(libmseed_path, 'libmseed.dll'),
                        os.path.join(package_path))

        # Copy libmseed.h to root package location
        shutil.copy(os.path.join(libmseed_path, 'libmseed.h'),
                    os.path.join(package_path))
