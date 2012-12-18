from setuptools import setup

version = '1.10.dev0'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('TODO.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'Django',
    'django-extensions',
    'django-nose',
    'lizard-fewsjdbc',
    'lizard-map >= 4.0, < 5.0',
    'lizard-ui >= 4.0, < 5.0',
    'lizard-shape',
    'nens-graph',
    'pkginfo',
    'pytz',
    'GDAL',
    ],

tests_require = [
    ]

setup(name='lizard-rainapp',
      version=version,
      description=("RainApp - visualizing rain statistics " +
                   "based on measurements"),
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Programming Language :: Python',
                   'Framework :: Django',
                   ],
      keywords=[],
      author='Jack Ha',
      author_email='jack.ha@nelen-schuurmans.nl',
      url='',
      license='GPL',
      packages=['lizard_rainapp'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      entry_points={
          'console_scripts': [
            ],
          'lizard_map.adapter_class': [
            'adapter_rainapp = lizard_rainapp.layers:RainAppAdapter'
            ],
          },
      )
