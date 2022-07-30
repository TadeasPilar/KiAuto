#!/usr/bin/python3
from setuptools import setup, find_packages
from kiauto.misc import __version__, __author__, __email__, __url__

# Use the README.md as a long description.
# Note this is also included in the MANIFEST.in
with open('README.md', encoding='utf-8') as f:
    long_description = '\n' + f.read()

setup(name='kiauto',
      version=__version__,
      description='KiCad Automation Scripts',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author=__author__,
      author_email=__email__,
      url=__url__,
      # Packages are marked using __init__.py
      packages=find_packages(),
      scripts=['src/eeschema_do', 'src/pcbnew_do', 'src/kicad2step_do'],
      install_requires=['xvfbwrapper', 'psutil'],
      include_package_data=True,
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Apache Software License',
                   'Natural Language :: English',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python :: 3',
                   'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
                   ],
      platforms='POSIX',
      license='Apache License 2.0',
      python_requires='>=3.4',
      )
