from setuptools import setup

# Set the version number from the VERSION environment variable if it exists
version = os.environ.get('VERSION', '0.0.1')  # Default version if not set

# Read the contents of your README file
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='lkg-quilt',
    version=version,
    packages=['lkg_quilt'],
    entry_points={
        'console_scripts': [
            'lkg-quilt = lkg_quilt.__main__:main'
        ]
    },
    author="Brian Jackson",
    author_email="brian@jaxzin.com",
    url="https://github.com/jaxzin/lkg-quilt",
    description='Quilt Generator from Lightfield Captures',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=[
        'ffmpeg-python',
        # Add other dependencies here
    ],
    classifiers=[
        'Development Status :: 4 - Beta',  # Adjust as per your development status
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Graphics',
        'License :: OSI Approved :: MIT License',  # Adjust your license
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.12',
)
