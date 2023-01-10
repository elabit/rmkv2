from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fhand:
    long_description = fhand.read()

setup(
    name="robotmk",
    version="0.0.2",
    author="Simon Meggle",
    author_email="simon.meggle@elabit.de",
    description=("Robotmk Agent library for running Robot Framework tests"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/elabit/robotmk",
    project_urls={
        "Bug Tracker": "https://github.com/elabit/robotmk/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    install_requires=["click"],
    packages=find_packages(),
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "robotmk = robotmk.cli:main",
        ]
    },
)
