import os
import sys
import shutil
import subprocess
from packaging.tags import sys_tags

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):

    here = os.path.abspath(os.path.dirname(__file__))
    package_path = os.path.join(here, 'src', 'mseedlib')
    libmseed_path = os.path.join(package_path, 'libmseed')

    def initialize(self, version, build_data):
        # Set wheel tag, e.g. py3-none-macosx_14_0_x86_64
        python_tag = f'py{sys.version_info.major}'
        abi_tag = 'none'
        platform_tag = next(sys_tags()).platform
        build_data['tag'] = f'{python_tag}-{abi_tag}-{platform_tag}'
        build_data['pure_python'] = False

        print(f"Building libmseed via Makefile in {self.libmseed_path}")

        if sys.platform.lower().startswith("windows"):
            cmd = f"nmake /f Makefile.win dll"
        else:
            cmd = f"CFLAGS='-O3' make -j shared"

        subprocess.check_call(cmd, cwd=self.libmseed_path, shell=True)

        # Copy shared library to root package location
        if os.path.exists(os.path.join(self.libmseed_path, 'libmseed.so')):
            shutil.copy(os.path.join(self.libmseed_path, 'libmseed.so'),
                        os.path.join(self.package_path))
        elif os.path.exists(os.path.join(self.libmseed_path, 'libmseed.dylib')):
            shutil.copy(os.path.join(self.libmseed_path, 'libmseed.dylib'),
                        os.path.join(self.package_path))
        elif os.path.exists(os.path.join(self.libmseed_path, 'libmseed.dll')):
            shutil.copy(os.path.join(self.libmseed_path, 'libmseed.dll'),
                        os.path.join(self.package_path))

        # Copy libmseed.h to root package location
        shutil.copy(os.path.join(self.libmseed_path, 'libmseed.h'),
                    os.path.join(self.package_path))

    def clean(self, versions):
        if sys.platform.lower().startswith("windows"):
            cmd = f"pushd {self.libmseed_path} && nmake /f Makefile.win clean & popd"
        else:
            cmd = f"make -C {self.libmseed_path} clean"

        subprocess.check_call(cmd, shell=True)

        if os.path.exists(os.path.join(self.package_path, 'libmseed.so')):
            os.remove(os.path.join(self.package_path, 'libmseed.so'))
        if os.path.exists(os.path.join(self.package_path, 'libmseed.dylib')):
            os.remove(os.path.join(self.package_path, 'libmseed.dylib'))
        if os.path.exists(os.path.join(self.package_path, 'libmseed.dll')):
            os.remove(os.path.join(self.package_path, 'libmseed.dll'))
        if os.path.exists(os.path.join(self.package_path, 'libmseed.h')):
            os.remove(os.path.join(self.package_path, 'libmseed.h'))

    def finalize(self, version, build_data, artifact_path):
        pass
