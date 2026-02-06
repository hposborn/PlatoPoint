from setuptools import setup

setup(
    name='PlatoPoint',
    version='0.1.0',
    description='A tool for simulating the PLATO space telescope field of view and coverage.',
    author='Your Name',  # Update this
    author_email='your.email@example.com',  # Update this
    py_modules=['PlatoPoint'],  # This tells setuptools to include your single .py file
    install_requires=[
        'numpy',
        'astropy>=5.0',
        'pandas'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Astronomy',
    ],
    python_requires='>=3.8',
)
