from setuptools import setup

setup(
    name             = 'plumbing',
    version          = '2.1.5',
    description      = 'Helps with plumbing-type programing in python.',
    license          = 'MIT',
    url              = 'http://github.com/xapple/plumbing/',
    author           = 'Lucas Sinclair',
    author_email     = 'lucas.sinclair@me.com',
    packages         = ['plumbing', 'plumbing.trees', 'plumbing.slurm', 'plumbing.databases'],
    install_requires = ['autopaths', 'sh', 'biopython', 'matplotlib', 'brewer2mpl'],
    long_description = open('README.md').read(),
)
