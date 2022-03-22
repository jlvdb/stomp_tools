import setuptools
import os


with open("README.md", "r") as f:
    long_description = f.read()
with open("requirements.txt") as f:
    install_requires = [pkg.strip() for pkg in f.readlines() if pkg.strip()]
scripts = [
    os.path.join("bin", fname) for fname in os.listdir("bin")]

setuptools.setup(
    name="stomp_tools",
    version="1.0",
    author="Jan Luca van den Busch",
    description="Tools to create and handle STOMP pixel maps.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jlvdb/stomp_tools",
    packages=setuptools.find_packages(),
    scripts=scripts,
    install_requires=install_requires)
