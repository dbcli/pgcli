from setuptools import setup

setup(
        name='pgcli',
        author='Amjith Ramanujam',
        version='0.1',
        license='LICENSE.txt',
        url='https://github.com/amjith/pgcli',
        py_modules=['pgcli'],
        description='CLI for Postgres. With auto-completion and '
                    'syntax highlighting',
        install_requires=[
            'Click',
            'prompt_toolkit',
            'psycopg2',
            ],
        entry_points='''
            [console_scripts]
            pgcli=pgcli:pgcli
        ''',
        classifiers=[
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3'
            ],
        )
