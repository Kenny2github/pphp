from setuptools import setup, find_packages

f = open('README.rst', 'r')
long_description = f.read()
f.close()

setup(
	name='pphp',
	version='2.0.0a3',
	description='A spinoff of PHP in Python',
	long_description=long_description,
	url='https://kenny2github.github.io/pphp',
	author='Ken Hilton',
	author_email='kenny2minecraft@gmail.com',
        py_modules=['pphp'],
	license='GNU GPLv3',
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
		'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
		'Programming Language :: Python :: 2.7',
	],
	keywords='http php server',
	python_requires='<3'
)
