# Project Summary: dir-assistant

`dir-assistant` is a versatile command-line interface (CLI) tool designed to facilitate conversational interaction with a software project's codebase. It allows users to "chat" with their files, leveraging the power of Large Language Models (LLMs) to answer questions, generate code, and perform file modifications.

## Core Purpose

The primary goal of `dir-assistant` is to provide an AI-powered assistant that is deeply integrated into a developer's local environment. By indexing the files in the current directory (and other specified directories), it builds a contextual understanding of the codebase, which it uses to provide relevant and accurate responses to user prompts.

## Key Features

- **Hybrid LLM Support:** Seamlessly integrates with both local GGUF models (via `llama-cpp-python`) and a wide range of API-based models like OpenAI, Gemini, and Anthropic (via `litellm`).
- **Retrieval-Augmented Generation (RAG):** Employs a FAISS-based vector index to perform semantic searches on file chunks, ensuring that only the most relevant code snippets are included in the LLM's context.
- **Contextually-Guided RAG (CGRAG):** An advanced feature that uses an initial LLM call to generate a list of key concepts from the user's prompt. This guidance is then used to perform a more targeted and effective RAG search.
- **RAG Caching & Optimization:** A sophisticated system (`RagOptimizer`) that analyzes prompt history to reorder and replace file chunks ("artifacts") in the context. It prioritizes historically frequent, stable, and well-positioned artifacts to improve response quality and reduce latency/cost.
- **Git Integration:** Can be configured to automatically commit LLM-generated file changes to the local Git repository, streamlining the development workflow.
- **File Watching:** Actively monitors the filesystem for changes and automatically re-indexes modified files in the background, keeping the assistant's knowledge up-to-date.
- **Interactive & Single-Prompt Modes:** Supports both a continuous, multi-turn chat session and a one-off mode for single questions via the `-s` flag.
- **Robust Configuration:** Manages settings through a `config.toml` file, with support for environment variable overrides. Includes utilities for downloading models, setting API keys, and platform-specific setup.

## Architecture Overview

The application is structured into several core components:

1.  **CLI Entrypoint (`main.py`, `cli/`):** Uses `argparse` to handle command-line arguments. It dispatches tasks to dedicated modules for starting the assistant (`start.py`), managing configuration (`config.py`), handling models (`models.py`), and setting API keys (`setkey.py`).

2.  **Assistant Abstraction (`assistant/`):**
    -   `BaseAssistant`: The foundation class that manages chat history, context size, and the main interaction loop. It orchestrates the RAG process.
    -   `CGRAGAssistant`: Inherits from `BaseAssistant` and adds the two-step CGRAG logic.
    -   `GitAssistant`: Inherits from `CGRAGAssistant` and implements the logic for prompting for file changes and committing them to Git.
    -   `LlamaCppAssistant` & `LiteLLMAssistant`: The final concrete classes that inherit from `GitAssistant`. They implement the model-specific logic for calling either a local `llama.cpp` model or an API-based `litellm` model.

3.  **Indexing & Retrieval (`assistant/`):**
    -   `index.py`: Scans directories for text files, chunks them into manageable pieces, generates embeddings, and builds a `faiss` vector index. It also handles caching of indexed files to speed up subsequent runs.
    -   `cache_manager.py`: Manages SQLite databases for prompt history and RAG prefix caching, providing the data needed for optimization.
    -   `rag_optimizer.py`: Implements the algorithm to reorder and refine the list of file chunks retrieved from the RAG search.

4.  **Embedding (`assistant/`):**
    -   `BaseEmbed`: An abstract base class for embedding models.
    -   `LlamaCppEmbed` & `LiteLlmEmbed`: Concrete implementations for generating embeddings using either a local GGUF model or an API, respectively.

## Dependencies

-   **`llama-cpp-python`**: For running local GGUF models.
-   **`litellm`**: For interfacing with various LLM APIs.
-   **`faiss-cpu`**: For efficient similarity search in the RAG vector index.
-   **`prompt-toolkit`**: For providing a rich, multi-line input experience in the interactive chat.
-   **`dynaconf` & `toml`**: For flexible configuration management.
-   **`watchdog`**: For monitoring file system events.
-   **`sqlitedict`**: For simple key-value file caching.