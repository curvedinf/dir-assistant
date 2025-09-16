# Project Information

This document contains general information about the `dir-assistant` project, including new features, upgrade instructions, limitations, and acknowledgements.

## Table of Contents
1. [New Features](#new-features)
2. [Upgrading](#upgrading)
3. [Limitations](#limitations)
4. [Additional Help](#additional-help)
5. [Acknowledgements](#acknowledgements)

---

## New Features
* File artifact context optimization for maximal utilization of LLM context caching.
This can drastically reduce API LLM expenses and processing time if context prefix
caching is supported by your LLM provider.
* Separate configuration options for the CGRAG API model so you can now use a quicker and less expensive
model for the CGRAG guidance step.

---

## Upgrading
Some version upgrades may have incompatibility issues in the embedding index cache. Use this command to delete the
index cache so it may be regenerated:
```shell
dir-assistant clear
```

---

## Limitations
- Dir-assistant only detects and reads text files at this time.

---

## Additional Help
Use the `-h` argument with any command or subcommand to view more information. If your problem is beyond the scope of
the helptext, please report a Github issue.

---

## Acknowledgements
- Local LLMs are run via the fantastic [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) package
- API LLMS are run using the also fantastic [LiteLLM](https://github.com/BerriAI/litellm) package
- Special thanks to [Blazed.deals](https://blazed.deals) for sponsoring this project.
