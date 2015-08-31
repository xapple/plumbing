from setuptools import setup

setup(
        name             = 'plumbing',
        version          = '2.0.3',
        description      = 'Helps with plumbing-type programing in python',
        long_description = open('README.md').read(),
        license          = 'MIT',
        url              = 'http://github.com/xapple/plumbing/',
        author           = 'Lucas Sinclair',
        author_email     = 'lucas.sinclair@me.com',
        classifiers      = ['Topic :: Scientific/Engineering :: Bio-Informatics'],
        packages         = ['plumbing'],
        install_requires = ['sh', 'biopython'],

        # Install extra dependencies:
        # $ pip install =e.[dev]
        extras_require={
            'dev': [
                'setuptools',
                'sphinx',
                'sphinx_rtd_theme',
            ],
        },
    )
