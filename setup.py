from distutils.core import setup, Extension
import os
from Cython.Build import cythonize

# setup
setup(name='pobs_andor',
      version='0.2',
      description='pobs component for Andor cameras',
      packages=['pobs_andor'],
      ext_modules=cythonize(Extension(
          "pobs_andor.libandor", 
          ["pobs_andor/libandor.pyx"],
          libraries=["andor"]
      )),
      requires=['pobs', 'astropy', 'numpy'])
