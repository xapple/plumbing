from setuptools import setup, find_packages

setup(
    name             = 'plumbing',
    version          = '2.6.1',
    description      = 'Helps with plumbing-type programing in python.',
    long_description = open('README.md').read(),
    long_description_content_type = 'text/markdown',
    license          = 'MIT',
    url              = 'http://github.com/xapple/plumbing/',
    author           = 'Lucas Sinclair',
    author_email     = 'lucas.sinclair@me.com',
    packages         = find_packages(),
    install_requires = ['six', 'autopaths', 'sh', 'matplotlib', 'brewer2mpl', 'decorator',
                        'shell_command', 'pandas', 'tqdm', 'boto3', 'sshconf', 'retry',
                        'selenium'],
)
