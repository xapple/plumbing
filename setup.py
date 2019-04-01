from setuptools import setup, find_packages

setup(
    name             = 'plumbing',
    version          = '2.2.7',
    description      = 'Helps with plumbing-type programing in python.',
    license          = 'MIT',
    url              = 'http://github.com/xapple/plumbing/',
    author           = 'Lucas Sinclair',
    author_email     = 'lucas.sinclair@me.com',
    packages         = find_packages(),
    install_requires = ['six', 'autopaths', 'sh', 'biopython', 'matplotlib', 'brewer2mpl', 'decorator',
                        'shell_command', 'pandas', 'pyodbc', 'tqdm', 'brewer2mpl'],
    long_description = open('README.md').read(),
)
