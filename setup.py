import os
from setuptools import setup


summary = "KV provides a dictionary-like interface on top of SQLite."
with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    readme_rst = f.read()


setup(
    name='kv',
    url='https://github.com/mgax/kv',
    description=summary,
    long_description=readme_rst,
    license="BSD License",
    version='0.3',
    author='Alex Morega',
    py_modules=['kv'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Database :: Front-Ends',
    ],
    entry_points={
        'console_scripts': [
            'kv-cli = kv:main',
        ],
    },
)
