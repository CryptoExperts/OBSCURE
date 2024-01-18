#!/usr/bin/env python
from distutils.core import setup, Extension

schwaemm_ext = Extension(
    'schwaemm._schwaemm',
    sources=[
        'schwaemm/schwaemm.i',
        'schwaemm/schwaemm.c',
        'schwaemm/sparkle.c',
        'schwaemm/wrapper.c',
    ],
    depends=[
        'schwaemm/*.h'
        'schwaemm/*.c'
    ],
    swig_opts=["-DSWIGWORDSIZE64"],  # https://github.com/swig/swig/issues/568
    # linking by path later would not include path
    # https://stackoverflow.com/questions/1305266/how-to-link-to-a-shared-library-without-lib-prefix-in-a-different-directory
    # extra_link_args=["-Wl,-soname,_example.so"],
)

setup(
    packages=["schwaemm"],
    name='schwaemm',
    version='0.1',
    author="Aleksei Udovenko",
    description="""Simple wrapper for Schwaemm AEAD""",
    ext_modules=[schwaemm_ext],
    package_data={'schwaemm': ['*.h', '*.so']},
)
