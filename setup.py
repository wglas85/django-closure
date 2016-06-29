from setuptools import setup, find_packages
import os
import re

PACKAGE="django-closure"
MYDIR = os.path.dirname(__file__)

# Utility function to read the README file from the doc folder.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read_doc(fname):
    return open(os.path.join(MYDIR,fname)).read()

def read_version():
    fn  = os.path.join(os.path.join(MYDIR,"debian-unix"),"changelog")
    with open(fn) as fd:
        line = fd.readline()   
        version,n = re.subn('^'+PACKAGE+'\\s*\\(([^-]*)-[^)]\\).*\n','\\1',line)
        if n != 1:
            raise SyntaxError("debian changelog line [%s] is malformatted"%line.substring[:-1])
        return version

setup(
    name='django-closure',
    packages=find_packages(),
    include_package_data=True,
    package_dir={'closure': 'closure'},
    version='0.1.0',
    description='A closure javascript .',
    author='Vasco Pinho',
    author_email='vascogpinho@gmail.com',
    url='https://github.com/wglas85/django-closure',
    download_url='https://github.com/wglas85/django-closure/tarball/master',
    long_description=read_doc("README.md"),
    license='Apache 2.0',
    keywords=['closure', 'javascript', 'django'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
    ],
)
