from distutils.core import setup, Extension
import os
from Cython.Build import cythonize

# setup
setup(name='pyobs_andor',
      version='0.2',
      description='pyobs component for Andor cameras',
      packages=['pyobs_andor'],
      ext_modules=cythonize(Extension(
          "pyobs_andor.libandor", 
          ["pyobs_andor/libandor.pyx"],
          libraries=["andor"]
      )),
      requires=['astropy', 'numpy'])
