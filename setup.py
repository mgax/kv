import os
import distutils.core


summary = "KV provides a dictionary-like interface on top of SQLite."
with open(os.path.join(os.path.dirname(__file__), 'README.rst'), 'rb') as f:
    readme_rst = f.read()


distutils.core.setup(
    name='kv',
    url='https://github.com/mgax/kv',
    description=summary,
    long_description=readme_rst,
    license="BSD License",
    version='0.1',
    author='Alex Morega',
    py_modules=['kv'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database :: Front-Ends',
    ],
)
