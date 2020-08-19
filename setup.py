# -*- coding: utf-8 -*-
from os.path import dirname, join
from setuptools import setup

from django_admin_reset import __version__

with open(join(dirname(__file__), 'README.rst')) as readme_file:
    long_description = readme_file.read()

setup(
    name='django-admin-reset',
    version=__version__,
    description='Django admin password reset',
    long_description=long_description,
    author='Tibor Hári',
    author_email='hartib@gmail.com',
    url='https://github.com/tiborhari/django-admin-reset/',
    packages=['django_admin_reset'],
    package_data={'django_admin_reset': ['templates/admin/*.html',
                                         'locale/*/LC_MESSAGES/*.[mp]o']},
    python_requires='>=3.5, <4',
    install_requires=['django>=2.2,<3.2'],
    extras_require={
        'testing': [
            'pytest>=6.0.1,<6.1',
            'pytest-cov>=2.10.1,<2.11',
            'pytest-django>=3.9.0,<3.10',
            'tox>=3.19.0,<3.20'],
        'docs': [
            'sphinx>=3.2.1,<3.3',
            'sphinx_rtd_theme>=0.5.0,<0.6'],
        'babel': [
            'babel>=2.8.0,<2.9']
    },
)
