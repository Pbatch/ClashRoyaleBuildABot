import os
from setuptools import setup, find_packages

# define long description with readme text
with open("README.md", "r", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

# get tag name for versioning for CI or dev for otherwise
try:
    version = (os.environ['GIT_TAG_NAME']).replace('v', '')
except KeyError:
    print('Defaulting to dev')
    version = 'dev'

setup(
    name='ClashRoyaleBuildABot',
    version=version,
    description='A platform for creating bots to play Clash Royale',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords='machine-learning ai computer-vision adb clashroyale bluestacks yolov5',
    author='pbatch',
    url='https://github.com/Pbatch/ClashRoyaleBuildABot',
    download_url='https://github.com/Pbatch/ClashRoyaleBuildABot/releases',
    install_requires=[
        "pure-python-adb",
        "Pillow", "numpy", "scipy",
        "onnxruntime",
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={'clashroyalebuildabot.data': ["images/*/*.png", "*.csv", "*.onnx"]},
    python_requires='>=3.6',
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
