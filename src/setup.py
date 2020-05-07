from setuptools import setup, find_packages
import os
import sys

def read_requirements(fname):
    with open('requirements.txt') as file:
        lines=file.readlines()
        requirements = [line.strip() for line in lines]
    return requirements

extras_3_6 = ['dataclasses']
extras_3_7 = []
additional = []

setup(
    name='tequila',
    version="Orquestra-Test",
    author='Jakob S. Kottmann, Sumner Alperin-Lea, Teresa Tamayo-Mendoza, Cyrille Lavigne, Abhinav Anand, Maha Kesebi ...',
    author_email='jakob.kottmann@gmail.com',
    install_requires=[ # also requires jax+jaxlib or autograd
        'numpy',
        'cmake',
        'scipy',
        'jax',
        'jaxlib',
        'sympy',
        'setuptools',
        'pytest',
        'openfermion',
        'qulacs',
        'cirq',
        'sphinx',
        'm2r',
        'z-quantum-core', # no idea if needed
        'qe-openfermion', # needed for qe-psi4 anyways
        'qe-psi4'
    ] + additional,
    extras_require={
        ':python_version < "3.7"': extras_3_6,
        ':python_version == "3.7"': extras_3_7
    },
    packages=find_packages(include=['tequila', 'tequila.']),
    #package_dir={'': ''},
    include_package_data=True,
    package_data={
        '': [os.path.join('src')]
    }
)

setuptools.setup(
    name                            = "mycode",
    packages                        = setuptools.find_packages(where = "mycode"),
    package_dir                     = {
        "" : "mycode"
    },
    classifiers                     = (
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ),
    install_requires=[
        'tequila'
        ],
    include_package_data=True
)
