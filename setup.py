from setuptools import setup, find_packages

setup(
    name="phone-mcp",
    version="0.1.9",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.6.0",
        "aiohttp>=3.8.0",
        "asyncio>=3.4.3",
    ],
    author="hao",
    author_email="hao@hao.com",
    description="A phone control plugin for MCP that allows you to control your Android phone through ADB commands to connect any human",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hao-cyber/phone-mcp",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "mcp.plugins": [
            "phone=phone_mcp:mcp"
        ],
        "console_scripts": [
            "phone-mcp=phone_mcp.__main__:main",
            "phone-cli=phone_mcp.cli:main"
        ]
    },
    keywords=["mcp", "phone", "android", "adb"],
    include_package_data=True,
) 