from setuptools import setup

# TODO add longer description
# TODO add short readme, read it, add as markdown, see
#      https://www.youtube.com/watch?v=tEFkHEKypLI

setup(
    name='kivar',
    description='PCB Assembly Variants for KiCad',
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
