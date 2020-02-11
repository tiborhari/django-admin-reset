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
    install_requires=['django>=2.2,<3.1'],
    extras_require={
        'testing': [
            'pytest-cov==2.8.1',
            'pytest-django==3.8.0',
            'tox==3.14.3'],
        'docs': [
            'sphinx==2.4.0',
            'sphinx_rtd_theme==0.4.3'],
        'babel': [
            'babel==2.8.0']
    },
)
