#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import glob
import os
import sys

# Uncomment to enforce Python version check during package import.
# Also uncomment python_requires below in setup().
# Replace "packagename" in error message with your package name.
# This is the same check as packagename/__init__.py but this one has to
# happen before importing ah_bootstrap.
__minimum_python_version__ = '3.5'
#if sys.version_info < tuple((int(val) for val in __minimum_python_version__.split('.'))):
#    sys.stderr.write("ERROR: packagename requires Python {} or later\n".format(__minimum_python_version__))
#    sys.exit(1)

import ah_bootstrap
from setuptools import setup

# A dirty hack to get around some early import/configurations ambiguities
if sys.version_info[0] >= 3:
    import builtins
else:
    import __builtin__ as builtins
builtins._ASTROPY_SETUP_ = True

from astropy_helpers.setup_helpers import (register_commands, get_debug_option,
                                           get_package_info)
from astropy_helpers.git_helpers import get_git_devstr
from astropy_helpers.version_helpers import generate_version_py

try:
    from astropy_helpers.distutils_helpers import is_distutils_display_option
except:
    # For astropy-helpers v0.4.x
    from astropy_helpers.setup_helpers import is_distutils_display_option


# Get some values from the setup.cfg
try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

conf = ConfigParser()
conf.read(['setup.cfg'])
metadata = dict(conf.items('metadata'))

NAME = metadata.get('name', 'packagename')
PACKAGENAME = metadata.get('package_name', 'packagename')
DESCRIPTION = metadata.get('description', 'packagename')
AUTHOR = metadata.get('author', 'Astropy Developers')
AUTHOR_EMAIL = metadata.get('author_email', '')
LICENSE = metadata.get('license', 'unknown')
URL = metadata.get('url', 'http://astropy.org')

# order of priority for long_description:
#   (1) set in setup.cfg,
#   (2) load LONG_DESCRIPTION.rst,
#   (3) load README.rst,
#   (4) package docstring
readme_glob = 'README*'
_cfg_long_description = metadata.get('long_description', '')
if _cfg_long_description:
    LONG_DESCRIPTION = _cfg_long_description

elif os.path.exists('LONG_DESCRIPTION.rst'):
    with open('LONG_DESCRIPTION.rst') as f:
        LONG_DESCRIPTION = f.read()

elif len(glob.glob(readme_glob)) > 0:
    with open(glob.glob(readme_glob)[0]) as f:
        LONG_DESCRIPTION = f.read()

else:
    # Get the long description from the package's docstring
    __import__(PACKAGENAME)
    package = sys.modules[PACKAGENAME]
    LONG_DESCRIPTION = package.__doc__

# Store the package name in a built-in variable so it's easy
# to get from other parts of the setup infrastructure
builtins._ASTROPY_PACKAGE_NAME_ = PACKAGENAME

# VERSION should be PEP440 compatible (http://www.python.org/dev/peps/pep-0440)
VERSION = metadata.get('version', '0.0.dev0')

# Indicates if this version is a release version
RELEASE = 'dev' not in VERSION

if not RELEASE:
    VERSION += get_git_devstr(False)

# Populate the dict of setup command overrides; this should be done before
# invoking any other functionality from distutils since it can potentially
# modify distutils' behavior.
cmdclassd = register_commands(PACKAGENAME, VERSION, RELEASE)

# Freeze build information in version.py
generate_version_py(PACKAGENAME, VERSION, RELEASE,
                    get_debug_option(PACKAGENAME))

# Treat everything in scripts except README* as a script to be installed
scripts = [fname for fname in glob.glob(os.path.join('scripts', '*'))
           if not os.path.basename(fname).startswith('README')]


# Get configuration information from all of the various subpackages.
# See the docstring for setup_helpers.update_package_files for more
# details.
package_info = get_package_info()

# Add the project-global data
package_info['package_data'].setdefault(PACKAGENAME, [])
package_info['package_data'][PACKAGENAME].append('data/*')

# Define entry points for command-line scripts
entry_points = {'console_scripts': []}

if conf.has_section('entry_points'):
    entry_point_list = conf.items('entry_points')
    for entry_point in entry_point_list:
        entry_points['console_scripts'].append('{0} = {1}'.format(
            entry_point[0], entry_point[1]))

# Include all .c files, recursively, including those generated by
# Cython, since we can not do this in MANIFEST.in with a "dynamic"
# directory name.
c_files = []
for root, dirs, files in os.walk(PACKAGENAME):
    for filename in files:
        if filename.endswith('.c'):
            c_files.append(
                os.path.join(
                    os.path.relpath(root, PACKAGENAME), filename))
package_info['package_data'][PACKAGENAME].extend(c_files)
install_requires = metadata.get('requires-dist')

if install_requires is None:
    install_requires = ['numpy', 'cython', 'astropy']
else:
    # Convert the config setup_requires string into a list
    install_requires = install_requires.strip().split()


def split_requirements_into_list(metadata, keyword):
    """
    Split a requirements keyword from the setup.cfg file into a list that setup() will accept.

    Parameters
    ----------
    metadata: dict
        Dictionary of metadata values
    keyword : string
        Name of requirements keyword (e.g. install_requires)

    Returns
    -------
    requirements_list : list of strings
        List of distutils requirements that can be passed to setup().
    """
    requirements = metadata.get(keyword)
    if requirements is None:
        requirement_list = []
    else:
        # Convert the config setup_requires string into a list
        requirement_list = requirements.strip().split()
    return requirement_list


# Avoid installing setup_requires dependencies if the user just
# queries for information
if is_distutils_display_option():
    setup_requires = []
    tests_require = []
    install_requires = []
else:
    setup_requires = split_requirements_into_list(metadata, 'setup_requires')
    install_requires = split_requirements_into_list(metadata, 'install_requires')
    tests_require = split_requirements_into_list(metadata, 'tests_require')


# Note that requires and provides should not be included in the call to
# ``setup``, since these are now deprecated. See this link for more details:
# https://groups.google.com/forum/#!topic/astropy-dev/urYO8ckB2uM

setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      scripts=scripts,
      setup_requires=setup_requires,
      install_requires=install_requires,
      tests_require=tests_require,
      provides=[PACKAGENAME],
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      url=URL,
      long_description=LONG_DESCRIPTION,
      cmdclass=cmdclassd,
      zip_safe=False,
      use_2to3=False,
      entry_points=entry_points,
      python_requires='>=' + __minimum_python_version__,
      **package_info
)
