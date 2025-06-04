from setuptools import find_packages, setup

install_requires = [
    "bleak",
    "matplotlib",
    "numpy",
    "pycycling",
    "fastapi",
    "uvicorn",
    "dearpygui",
    "pandas",
    "requests",
    "lxml",
    "garmin-fit-sdk"
]

tests_require = [
    "pytest",
]


setup(
    name="ble_sequencer",
    version="0.1.0",
    description="",
    author="François GAUTRAIS",
    author_email="francois@gautrais.eu",
    install_requires=install_requires,
    packages=find_packages("src"),
    include_package_data=True,
    zip_safe=False,
    data_files=[],
    test_suite="tests",
    tests_require=tests_require,
    extras_require={
        "test": tests_require,
        "sphinx": ["sphinx >= 1.5", "sphinx-rtd-theme", "rdcore_doc"],
        "pylint": ["pylint"],
    },

    entry_points={"console_scripts": []},
    package_dir={"": "src"},
)
