from setuptools import setup

setup(
    name             = 'plumbing',
    version          = '2.1.1',
    description      = 'Helps with plumbing-type programing in python.',
    license          = 'MIT',
    url              = 'http://github.com/xapple/plumbing/',
    author           = 'Lucas Sinclair',
    author_email     = 'lucas.sinclair@me.com',
    classifiers      = ['Topic :: Scientific/Engineering :: Bio-Informatics'],
    packages         = ['plumbing', 'plumbing.trees', 'plumbing.slurm'],
    install_requires = ['autopaths', 'sh', 'biopython', 'matplotlib', 'brewer2mpl'],
    long_description = open('README.md').read(),
)
