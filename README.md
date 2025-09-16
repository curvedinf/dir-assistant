# dir-assistant
[![PyPI](https://img.shields.io/pypi/v/dir-assistant)](https://pypi.org/project/dir-assistant/)
[![GitHub license](https://img.shields.io/github/license/curvedinf/dir-assistant)](LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/curvedinf/dir-assistant)](https://github.com/curvedinf/dir-assistant/commits/main)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/dir-assistant)](https://pypi.org/project/dir-assistant/)
[![GitHub stars](https://img.shields.io/github/stars/curvedinf/dir-assistant)](https://github.com/curvedinf/dir-assistant/stargazers)
[![Ko-fi Link](kofi.webp)](https://ko-fi.com/A0A31B6VB6)

Chat with your current directory's files using a local or API LLM.

![(Demo GIF of dir-assistant being run)](demo.gif)
## Summary
`dir-assistant` is a CLI python application available through `pip` that recursively indexes all text 
files in the current working directory so you can chat with them using a local or API LLM. By 
"chat with them", it is meant that their contents will automatically be included in the prompts sent 
to the LLM, with the most contextually relevant files included first. `dir-assistant` is designed 
primarily for use as a coding aid and automation tool.
### Features
- Includes an interactive chat mode and a single prompt non-interactive mode.
- When enabled, it will automatically make file updates and commit to git.
- Local platform support for CPU (OpenBLAS), Cuda, ROCm, Metal, Vulkan, and SYCL. 
- API support for all major LLM APIs. More info in the 
[LiteLLM Docs](https://docs.litellm.ai/docs/providers).
- Uses a unique method for finding the most important files to include when submitting your
prompt to an LLM called CGRAG (Contextually Guided Retrieval-Augmented Generation). You can read 
[this blog post](https://medium.com/@djangoist/how-to-create-accurate-llm-responses-on-large-code-repositories-presenting-cgrag-a-new-feature-of-e77c0ffe432d) for more information about how it works.
- Context optimization for utilizing LLM context caching to reduce cost and latency.
- Optionally configure a separate, faster LLM for the CGRAG guidance step to reduce cost and latency.
## Table of Contents
1. [Install](docs/install.md)
2. [Usage](docs/usage.md)
3. [Configuration](docs/configuration.md)
4. [Project Information](docs/project_info.md)
5. [Contributors](CONTRIBUTORS.md)
