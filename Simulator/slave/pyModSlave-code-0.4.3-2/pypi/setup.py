import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyModSlave",
    version="0.4.2.1",
    author="ElBar",
    author_email="eleftherios.barbas@gmail.com",
    description="A modbus RTU/TCP slave application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://sourceforge.net/projects/pymodslave/",
    packages=setuptools.find_packages(),
	include_package_data=False,
	package_data={
		'pyModSlave': ['ManModbus/*.*', 'ManModbus/style/*.*', 'ManModbus/READ_ME/*.*', 'ui/*.*', 'ui/icons/*.*'],
		},
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)