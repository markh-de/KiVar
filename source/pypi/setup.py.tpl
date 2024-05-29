from setuptools import setup
import os

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'README.md'), 'r') as f:
    long_descr = f.read()

setup(
    name='kivar',
    description='PCB Assembly Variants for KiCad',
    long_description=long_descr,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/markh-de/KiVar',
    author='Mark Hämmerling',
    author_email='dev@markh.de',
    version="<<VERSION>>",
    packages=["kivar"],
    install_requires=[],
    entry_points={
        "console_scripts": [
            "kivar = kivar:main"
        ]
    }
)
