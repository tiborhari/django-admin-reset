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
    python_requires='>=3.6, <4',
    install_requires=['django>=3.2,<4.1'],
    extras_require={
        'testing': [
            'flake8~=3.9.2',
            'pytest~=6.2.5',
            'pytest-cov~=3.0.0',
            'pytest-django~=3.10.0',
            'tox~=3.25.0'],
        'docs': [
            'sphinx~=4.5.0',
            'sphinx_rtd_theme~=1.0.0'],
        'babel': [
            'babel~=2.10.1']
    },
)
