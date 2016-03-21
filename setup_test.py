import setuptools
import numpy.distutils.core
import os
import sys

#from sys import platform
from setuptools import setup
#from setuptools.command.install import install
from distutils.command.build import build
from numpy.distutils.command.build_ext import build_ext
from subprocess import call



# path to base CDF directory if CDF library already installed and you want to use it
# otherwise, CDF library is installed
base_cdf = None
# leave items below to None unless base_cdf set to something other than None
# name of library, mac os x, libcdf.a
lib_name = None
# shared library name, needed for some systems
shared_lib_name = None

# CDF compile options
# note that the shared library name will be appended to extra_link_args automatically
extra_link_args = None
os_name = None
env_name = None

# manual f2py command for Mac OS X
# f2py -c --include-paths $CDF_INC -I$CDF_INC $CDF_LIB/libcdf.a -m fortran_cdf fortran_cdf.f -lm -lc

# some solutions in creating this file come from
# https://github.com/Turbo87/py-xcsoar/blob/master/setup.py

# get system parameters
platform = sys.platform
if platform == 'darwin':
    os_name = 'macosx'
    env_name = 'x86_64'
    lib_name = 'libcdf.a'
    # including shared lib in mac breaks things
    shared_lib_name = None #'libcdf.dylib' #
    extra_link_args = ['-lm', '-lc']
elif (platform == 'linux') | (platform == 'linux2'):
    os_name = 'linux'
    env_name = 'gnu'
    lib_name = 'libcdf.a'
    shared_lib_name = 'libcdf.so'
    extra_link_args = ['-lm', '-lc']
elif (platform == 'win32'):
    lib_name = 'libcdf.lib'
    shared_lib_name = 'dllcdf.lib'
    extra_link_args = ['/nodefaultlib:libcd']
else:
    if (lib_name is None) or ((base_cdf is None) and ((os_name is None) 
                                or (env_name is None) or (extra_link_args is None)) ):
        raise ValueError('Unknown platform, please set setup.py parameters manually.')


if base_cdf is None:
    build_cdf_flag = True
    # library not provided, build library included with pysatCDF
else:
    build_cdf_flag = False
    raise NotImplementedError
    if (lib_name is None):
        raise ValueError('Attempting to use pre-installed CDF library as directed. Please set setup.py parameters manually.')    
        

BASEPATH = os.path.dirname(os.path.abspath(__file__))
CDF_PATH = os.path.join(BASEPATH, 'cdf36_1-dist')

class CDFBuild(build):
    def run(self):
        # build CDF Library
        build_path = os.path.abspath(self.build_temp)
        cmd0 = ['make', 'clean']
        cmd = ['make',
            'OS=' + os_name,
            'ENV=' + env_name,
            'CURSES=no',
            'UCOPTIONS=-Dsingle_underscore',
            'all',]
        cmd2 = ['make',
            'INSTALLDIR='+build_path,
            'install',]

        # clean any previous attempts
        def compile0():
            call(cmd0, cwd=CDF_PATH)
        # set compile options via makefile
        def compile1():
            call(cmd, cwd=CDF_PATH)
        # do the installation
        def compile2():
            call(cmd2, cwd=CDF_PATH)

        self.execute(compile0, [], 'Cleaning CDF')
        self.execute(compile1, [], 'Configuring CDF')
        self.execute(compile2, [], 'Compiling CDF')

        # copy resulting tool to library build folder
        self.mkpath(self.build_lib)

        if not self.dry_run:
            self.copy_tree(os.path.join(self.build_temp, 'include'), 
                           os.path.join(self.build_lib, 'include'))
            self.mkpath(os.path.join(self.build_lib, 'lib'))
            self.copy_file(os.path.join(self.build_temp, 'lib', lib_name), 
                           os.path.join(self.build_lib, 'lib', lib_name))

            if shared_lib_name is not None:
                self.copy_file(os.path.join(self.build_temp, 'lib', shared_lib_name), 
                               os.path.join(self.build_lib, 'lib', shared_lib_name))

        # run original build code
        build.run(self)
        return


class ExtensionBuild(build_ext):
    def run(self):

        #build_path = os.path.abspath(self.build_temp)
        lib_path = os.path.abspath(self.build_lib)
        # set directories for the CDF library installed with pysatCDF
        self.extensions[0].include_dirs = [os.path.join(lib_path, 'include')]
        self.extensions[0].f2py_options = ['--include-paths', os.path.join(lib_path, 'include')]
        self.extensions[0].extra_objects = [os.path.join(lib_path, 'lib', lib_name)]
        if shared_lib_name is not None:
            self.extensions[0].extra_link_args.append(os.path.join(lib_path, 'lib', shared_lib_name))

        build_ext.run(self)
        return


if not build_cdf_flag:
    f2py_cdf_include_path = os.path.join(base_cdf, 'include')
    f2py_cdf_lib_path = os.path.join(base_cdf, 'lib', lib_name)
    cmdclass = {}
else:
    cmdclass={
        'build': CDFBuild,
        'build_ext': ExtensionBuild,
        #'install': CDFInstall
          }

    f2py_cdf_include_path = ''
    f2py_cdf_lib_path = ''

# setup fortran extension
#---------------------------------------------------------------------------  

ext1 = numpy.distutils.core.Extension(
        name = 'fortran_cdf',
        sources = [os.path.join('pysatCDF', 'fortran_cdf.f')], 
        include_dirs = [f2py_cdf_include_path],
        f2py_options = ['--include-paths', f2py_cdf_include_path],
        extra_objects = [f2py_cdf_lib_path],
        extra_link_args = extra_link_args,  
        )


# call setup
#--------------------------------------------------------------------------
numpy.distutils.core.setup( 

    name = 'pysatCDF',
    version = '0.1.2',        
    packages = ['pysatCDF'],
    cmdclass = cmdclass,
    ext_modules = [ext1, ],
    description= 'Simple NASA Common Data Format (CDF) File reader.',
    url='http://github.com/rstoneback/pysatCDF',    
    # Author details
    author='Russell Stoneback',
    author_email='rstoneba@utdallas.edu',

    # Choose your license
    license='BSD',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        
        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],
    #install_requires = ['numpy'],
)  




