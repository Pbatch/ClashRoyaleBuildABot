import os
from setuptools import setup, find_packages

# Define long description with readme text
with open("README.md", "r", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

# Get tag name for versioning for CI or dev for otherwise
try:
    version = (os.environ["GIT_TAG_NAME"]).replace("v", "")
except KeyError:
    print("Defaulting to dev")
    version = "dev"

setup(
    name="ClashRoyaleBuildABot",
    version=version,
    description="A platform for creating bots to play Clash Royale",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    keywords="machine-learning ai computer-vision adb clashroyale bluestacks yolov5",
    author="pbatch",
    url="https://github.com/Pbatch/ClashRoyaleBuildABot",
    download_url="https://github.com/Pbatch/ClashRoyaleBuildABot/releases",
    install_requires=[
        "flatbuffers==2.0",
        "numpy==1.23.0",
        "onnxruntime==1.12.1",
        "Pillow==10.1.0",
        "protobuf==4.21.1",
        "scipy==1.8.1",
        "rich==13.7.1",
        "loguru==0.7.2",
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "clashroyalebuildabot.data": ["images/*/*.jpg", "*.csv", "*.onnx"]
    },
    python_requires=">=3.6",
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
