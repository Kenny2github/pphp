from setuptools import setup

f = open('README.rst', 'r')
long_description = f.read()
f.close()

setup(
	name='pphp',
	version='3.3.1',
	description='A spinoff of PHP in Python',
	long_description=long_description,
	url='https://kenny2github.github.io/pphp',
	author='Ken Hilton',
	author_email='kenny2minecraft@gmail.com',
        py_modules=['pphp'],
	license='GNU GPLv3',
	classifiers=[
		'Development Status :: 4 - Beta',
		'Intended Audience :: Developers',
		'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
		'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
		'Programming Language :: Python :: 2.7',
                'Programming Language :: Python :: 3',
	],
	keywords='http php server',
	python_requires='>=2.7'
)
