from __future__ import division  # confidence high

CONTACT = "Michael Droettboom"
EMAIL = "mdroe@stsci.edu"

from distutils.core import Extension
import glob
from os.path import join
import os.path
import sys

from astropy import setup_helpers

WCSROOT = os.path.relpath(os.path.dirname(__file__))
WCSVERSION = "4.10"


def b(s):
    return s.encode('ascii')

if sys.version_info[0] >= 3:

    def string_escape(s):
        s = s.decode('ascii').encode('ascii', 'backslashreplace')
        s = s.replace(b('\n'), b('\\n'))
        s = s.replace(b('\0'), b('\\0'))
        return s.decode('ascii')

    from io import StringIO
    string_types = (str, bytes)
else:

    def string_escape(s):
        return s.encode('string_escape')

    from cStringIO import StringIO
    string_types = (str, unicode)


def determine_64_bit_int():
    """
    The only configuration parameter needed at compile-time is how to
    specify a 64-bit signed integer.  Python's ctypes module can get us
    that information, but it is only available in Python 2.5 or later.
    If we can't be absolutely certain, we default to "long long int",
    which is correct on most platforms (x86, x86_64).  If we find
    platforms where this heuristic doesn't work, we may need to
    hardcode for them.
    """
    try:
        try:
            import ctypes
        except ImportError:
            raise ValueError()

        if ctypes.sizeof(ctypes.c_longlong) == 8:
            return "long long int"
        elif ctypes.sizeof(ctypes.c_long) == 8:
            return "long int"
        elif ctypes.sizeof(ctypes.c_int) == 8:
            return "int"
        else:
            raise ValueError()

    except ValueError:
        return "long long int"


def write_wcsconfig_h():
    """
    Writes out the wcsconfig.h header with local configuration.
    """
    h_file = StringIO()
    h_file.write("""
    /* WCSLIB library version number. */
    #define WCSLIB_VERSION {0}

    /* 64-bit integer data type. */
    #define WCSLIB_INT64 {1}

    /* Windows needs some other defines to prevent inclusion of wcsset()
       which conflicts with wcslib's wcsset().  These need to be set
       on code that *uses* astropy.wcs, in addition to astropy.wcs itself.
       */
    #if defined(_WIN32) || defined(_MSC_VER) || defined(__MINGW32__) || defined (__MINGW64__)

    #ifndef YY_NO_UNISTD_H
    #define YY_NO_UNISTD_H
    #endif

    #ifndef _CRT_SECURE_NO_WARNINGS
    #define _CRT_SECURE_NO_WARNINGS
    #endif

    #ifndef _NO_OLDNAMES
    #define _NO_OLDNAMES
    #endif

    #ifndef NO_OLDNAMES
    #define NO_OLDNAMES
    #endif

    #ifndef __STDC__
    #define __STDC__ 1
    #endif

    #endif
    """.format(WCSVERSION, determine_64_bit_int()))
    setup_helpers.write_if_different(
        join(WCSROOT, 'include', 'wcsconfig.h'),
        h_file.getvalue().encode('ascii'))

######################################################################
# GENERATE DOCSTRINGS IN C


def generate_c_docstrings():
    from astropy.wcs import docstrings
    docstrings = docstrings.__dict__
    keys = [
        key for key in docstrings.keys()
        if not key.startswith('__') and type(key) in string_types]
    keys.sort()
    docs = {}
    for key in keys:
        docs[key] = docstrings[key].encode('utf8').lstrip() + b'\0'

    h_file = StringIO()
    h_file.write("""/*
DO NOT EDIT!

This file is autogenerated by astropy/wcs/setup_package.py.  To edit
its contents, edit astropy/wcs/docstrings.py
*/

#ifndef __DOCSTRINGS_H__
#define __DOCSTRINGS_H__

#if defined(_MSC_VER)
void fill_docstrings(void);
#endif

""")
    for key in keys:
        val = docs[key]
        h_file.write('extern char doc_{0}[{1}];\n'.format(key, len(val)))
    h_file.write("\n#endif\n\n")

    setup_helpers.write_if_different(
        join(WCSROOT, 'include', 'docstrings.h'),
        h_file.getvalue().encode('utf-8'))

    c_file = StringIO()
    c_file.write("""/*
DO NOT EDIT!

This file is autogenerated by astropy/wcs/setup_package.py.  To edit
its contents, edit astropy/wcs/docstrings.py

The weirdness here with strncpy is because some C compilers, notably
MSVC, do not support string literals greater than 256 characters.
*/

#include <string.h>
#include "docstrings.h"

#if defined(_MSC_VER)
""")
    for key in keys:
        val = docs[key]
        c_file.write('char doc_{0}[{1}];\n'.format(key, len(val)))

    c_file.write("\nvoid fill_docstrings(void)\n{\n")
    for key in keys:
        val = docs[key]
        # For portability across various compilers, we need to fill the
        # docstrings in 256-character chunks
        for i in range(0, len(val), 256):
            chunk = string_escape(val[i:i + 256]).replace('"', '\\"')
            c_file.write('   strncpy(doc_{0} + {1}, "{2}", {3});\n'.format(
                key, i, chunk, min(len(val) - i, 256)))
        c_file.write("\n")
    c_file.write("\n}\n\n")

    c_file.write("#else /* UNIX */\n")

    for key in keys:
        val = docs[key]
        c_file.write('char doc_{0}[{1}] = "{2}";\n\n'.format(
            key, len(val), string_escape(val).replace('"', '\\"')))

    c_file.write("#endif\n")

    setup_helpers.write_if_different(
        join(WCSROOT, 'src', 'docstrings.c'),
        c_file.getvalue().encode('utf-8'))


def get_extensions():
    from astropy.version import debug

    write_wcsconfig_h()
    generate_c_docstrings()

    ######################################################################
    # WCSLIB
    wcslib_path = join(WCSROOT, "src", "wcslib")  # Path to wcslib
    wcslib_cpath = join(wcslib_path, "C")  # Path to wcslib source files
    wcslib_files = [  # List of wcslib files to compile
        'flexed/wcsbth.c',
        'flexed/wcspih.c',
        'flexed/wcsulex.c',
        'flexed/wcsutrn.c',
        'cel.c',
        'lin.c',
        'log.c',
        'prj.c',
        'spc.c',
        'sph.c',
        'spx.c',
        'tab.c',
        'wcs.c',
        'wcserr.c',
        'wcsfix.c',
        'wcshdr.c',
        'wcsprintf.c',
        'wcsunits.c',
        'wcsutil.c']
    wcslib_files = [join(wcslib_cpath, x) for x in wcslib_files]

    ######################################################################
    # ASTROPY.WCS-SPECIFIC AND WRAPPER SOURCE FILES
    astropy_wcs_files = [  # List of astropy.wcs files to compile
        'distortion.c',
        'distortion_wrap.c',
        'docstrings.c',
        'pipeline.c',
        'pyutil.c',
        'astropy_wcs.c',
        'astropy_wcs_api.c',
        'sip.c',
        'sip_wrap.c',
        'str_list_proxy.c',
        'util.c',
        'wcslib_wrap.c',
        'wcslib_tabprm_wrap.c',
        'wcslib_units_wrap.c',
        'wcslib_wtbarr_wrap.c']
    astropy_wcs_files = [join(WCSROOT, 'src', x) for x in astropy_wcs_files]

    ######################################################################
    # DISTUTILS SETUP
    libraries = []
    define_macros = [
        ('ECHO', None),
        ('WCSTRIG_MACRO', None),
        ('ASTROPY_WCS_BUILD', None),
        ('_GNU_SOURCE', None),
        ('WCSVERSION', WCSVERSION)]
    undef_macros = []
    extra_compile_args = []
    extra_link_args = []

    if debug:
        define_macros.append(('DEBUG', None))
        undef_macros.append('NDEBUG')
        if not sys.platform.startswith('sun') and \
           not sys.platform == 'win32':
            extra_compile_args.extend(["-fno-inline", "-O0", "-g"])
    else:
        # Define ECHO as nothing to prevent spurious newlines from
        # printing within the libwcs parser
        define_macros.append(('NDEBUG', None))
        undef_macros.append('DEBUG')

    if sys.platform == 'win32':
        define_macros.extend([
            ('YY_NO_UNISTD_H', None),
            ('_CRT_SECURE_NO_WARNINGS', None),
            ('_NO_OLDNAMES', None),  # for mingw32
            ('NO_OLDNAMES', None),  # for mingw64
            ('__STDC__', None)  # for MSVC
            ])

    if sys.platform.startswith('linux'):
        define_macros.append(('HAVE_SINCOS', None))

    return [
        Extension('astropy.wcs._wcs',
                  wcslib_files + astropy_wcs_files,
                  include_dirs=[
                      setup_helpers.get_numpy_include_path(),
                      wcslib_cpath,
                      join(WCSROOT, "include")],
                  define_macros=define_macros,
                  undef_macros=undef_macros,
                  extra_compile_args=extra_compile_args,
                  extra_link_args=extra_link_args,
                  libraries=libraries)]


def get_package_data():
    # Installs the testing data files
    return {
        'astropy.wcs.tests': ['data/*.hdr', 'data/*.fits',
                              'maps/*.hdr', 'spectra/*.hdr'],
        'astropy.wcs': ['include/*.h']}


def get_legacy_alias():
    return setup_helpers.add_legacy_alias('pywcs', 'astropy.wcs')
