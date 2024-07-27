from setuptools import setup, find_packages

setup(
    name="dir-assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "llama-cpp-python",
        "faiss-cpu",
        "litellm",
        "colorama",
        "sqlitedict",
        "prompt-toolkit",
        "watchdog",
        "google-generativeai",
        "openai",
        "boto3",
    ],
    entry_points={
        "console_scripts": [
            "dir-assistant=dir_assistant.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
