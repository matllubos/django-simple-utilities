from setuptools import setup, find_packages

version = '0.8'

setup(
    name='django-simple-utilities',
    version=version,
    description="Simple utilities which help create django application.",
    keywords='django, admin, utilities',
    author='Lubos Matl',
    author_email='matllubos@gmail.com',
    url='https://www.assembla.com/code/django-simple-utilities/git/nodes',
    license='GPL',
    package_dir={'utilities': 'utilities'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: Czech',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    zip_safe=False
)