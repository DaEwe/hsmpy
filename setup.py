from setuptools import setup, find_packages

setup(
    name='hsmpy',
    version='0.0.1',
    packages=find_packages(exclude=["tests*"]),
    url='https://gitlab.com/ewert-daniel/hsmpy',
    license='MIT',
    author='Daniel Ewert',
    author_email='ewert.daniel@gmail.com',
    description='Behavior Engine based on Hybrid State Machines, inspired by http://www.fawkesrobotics.org',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=["pygraphviz"],
)
