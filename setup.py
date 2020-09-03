from setuptools import setup, find_packages

setup(
    name             = 'plumbing',
    version          = '2.9.2',
    description      = 'Helps with plumbing-type programing in python.',
    license          = 'MIT',
    url              = 'http://github.com/xapple/plumbing/',
    author           = 'Lucas Sinclair',
    author_email     = 'lucas.sinclair@me.com',
    packages         = find_packages(),
    install_requires = ['autopaths>=1.4.2', 'six', 'pandas', 'numpy', 'matplotlib',
                        'retry', 'tzlocal'],
    long_description = open('README.md').read(),
    long_description_content_type = 'text/markdown',
    include_package_data = True,
)
