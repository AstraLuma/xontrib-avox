from setuptools import setup

setup(
    name='xontrib-avox',
    version='0.8',
    url='https://github.com/astronouth7303/xontrib-avox',
    license='GPLv3',
    author='Jamie Bliss',
    author_email='astronouth7303@gmail.com',
    description="Automatic voxes for projects",
    packages=['xontrib'],
    package_dir={'xontrib': 'xontrib'},
    package_data={'xontrib': ['*.xsh']},
    platforms='any',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Desktop Environment',
        'Topic :: System :: Shells',
        'Topic :: System :: System Shells',
    ]
)
