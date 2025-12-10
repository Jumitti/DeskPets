from setuptools import setup, find_packages

setup(
    name="deskpets",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
        "Pillow",
        "PyQt6-WebEngine"
    ],
    entry_points={
        "console_scripts": [
            "deskpets=deskpets.main:main"
        ],
    },
    include_package_data=True,
)
