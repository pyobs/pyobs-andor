from distutils.core import setup, Extension
import os
from Cython.Build import cythonize

# setup
setup(name='pytel_andor',
      version='0.1',
      description='pytel component for Andor cameras',
      packages=['pytel_andor'],
      ext_modules=cythonize(Extension(
          "pytel_andor.libandor", 
          ["pytel_andor/libandor.pyx"],
          libraries=["andor"]
      )),
      requires=['pytel', 'astropy', 'numpy'])
