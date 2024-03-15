import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bpy_helper",
    version="0.0.0",
    author="NCJ",
    author_email="me@ncj.wiki",
    description="A lightweight alternative to BlenderProc",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/iamNCJ/bpy-helper",
    packages=setuptools.find_packages(),
    install_requires=[
        'bpy>=3.4.0'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Topic :: Multimedia :: Graphics :: 3D Rendering"
    ],
    python_requires='>=3.10',
)