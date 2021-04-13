#coding: utf - 8
import os
import fnmatch
import subprocess
import sysconfig

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py as _build_py
from setuptools.extension import Extension

from Cython.Build import cythonize
from Cython.Distutils import build_ext
from pathlib import Path
import shutil
import sys

# TODO: replace Microsoft Visual Studio with Mingw_x64
if sys.platform == 'win32':
    # patch env with vcvarsall.bat from vs2015 (vc14)
    try:
        # C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build
        # cmd = '"{}..\\VC\\Auxiliary\\Build\\vcvarsall.bat" x86_amd64 >nul 2>&1 && set'.format(os.environ['VS140COMNTOOLS'])
        cmd = '"C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\BuildTools\\VC\\Auxiliary\\Build\\vcvarsall.bat" x86_amd64 >nul 2>&1 && set'
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
    except:
        print("Error executing {}".format(cmd))
        raise

    for key, _, value in (line.partition('=') for line in out.splitlines()):
        if key and value:
            os.environ[key] = value

    # inform setuptools that the env is already set
    os.environ['DISTUTILS_USE_SDK'] = '1'

EXCLUDE_FILES = [
    # 'app/main.py'
]

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# noinspection PyPep8Naming
class build_py(_build_py):
    
    def find_package_modules(self, package, package_dir):
        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        modules = super().find_package_modules(package, package_dir)
        filtered_modules = []
        for (pkg, mod, filepath) in modules:
            if os.path.exists(filepath.replace('.py', ext_suffix)):
                continue
            filtered_modules.append((pkg, mod, filepath,))
        return filtered_modules


def get_ext_paths(root_dir, exclude_files):
    """get filepaths for compilation"""
    paths = []
    
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            if os.path.splitext(filename)[1] != '.py':
                continue
            
            file_path = os.path.join(root, filename)
            if file_path in exclude_files:
                continue
            
            paths.append(file_path)
    return paths


def get_export_symbols_fixed(self, ext):
    names = ext.name.split('.')
    if names[-1] != "__init__":
        initfunc_name = "PyInit_" + names[-1]
    else:
        # take name of the package if it is an __init__-file
        initfunc_name = "PyInit_" + names[-2]
    if initfunc_name not in ext.export_symbols:
        ext.export_symbols.append(initfunc_name)
    return ext.export_symbols


class MyBuildExt(build_ext):
    def run(self):
        build_ext.get_export_symbols = get_export_symbols_fixed
        build_ext.run(self)
        
        build_dir = Path(self.build_lib)
        root_dir = Path(__file__).parent
        
        target_dir = build_dir if not self.inplace else root_dir

        self.copy_file(Path('pyrplidar') / '__init__.py', root_dir, target_dir)
    
    def copy_file(self, path, source_dir, destination_dir):
        if not (source_dir / path).exists():
            return
        shutil.copyfile(str(source_dir / path), str(destination_dir / path))


setup(
    name="pyrplidar",
    version="0.1.2-0.0.2",
    author=["Hyun-je", "Toan Truong Viet"],
    author_email=["bigae2@gmail.com", "viettoan151"],
    license="MIT",
    description="Full-featured python library for Slamtec RPLIDAR series",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Hyun-je/pyrplidar",
    packages=[],
    ext_modules=cythonize(
        # get_ext_paths('app', EXCLUDE_FILES),
        [
            Extension("pyrplidar.*", ["pyrplidar/*.py"]),
        ],
        build_dir="build",
        compiler_directives={'language_level': 3,
                             'always_allow_keywords': True,
                             }
    ),
    cmdclass={
        # 'build_py': build_py,
        'build_ext': MyBuildExt,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: DMP License",
        "Operating System :: OS Independent",
    ],
    python_requires='==3.8.8',
    install_requires = ["pyserial"],
)


# build command
# python setup_cython.py bdist_wheel
# python setup_cython.py install
# rm -rf pyrplidar.egg-info dist build
