# Dir Assistant Project Summary 🤖

## Overview

`dir-assistant` is a sophisticated command-line tool 💻 designed to let developers interact with their codebases using Large Language Models (LLMs). It operates directly within a project directory, recursively scanning files 📂 to build a contextual understanding. This enables a powerful chat-based interface where users can ask questions, request code modifications, and get insights about their project, all with the AI 🧠 having direct access to the relevant file contents.

The tool is highly flexible, supporting both locally-run GGUF models 🏠 via `llama-cpp-python` and a wide range of API-based models (like OpenAI, Gemini, Anthropic) ☁️ through the `LiteLLM` library.

## Core Features

-   **🔄 Hybrid LLM Support:** Seamlessly switch between local models for privacy and offline use, and powerful API models for advanced tasks.
-   **📚 Retrieval-Augmented Generation (RAG):** Intelligently finds and injects the most relevant snippets of code from the project into the LLM prompt, providing accurate, context-aware answers.
-   **⚡️ Advanced RAG Caching & Optimization:** A unique system that caches and reorders context based on historical usage patterns, significantly reducing latency and API costs.
-   **💬 Interactive & Single-Prompt Modes:** Can be used as an ongoing interactive chat assistant or for one-off questions directly from the command line.
-   **👀 Live File Watching:** A background process monitors files for changes and automatically re-indexes them, ensuring the assistant's knowledge is always up-to-date.
-   **🐙 Git Integration:** Can be configured to automatically generate and apply file changes, and then commit them to the repository with a user-provided message.
-   **🎯 Contextually-Guided RAG (CGRAG):** An optional two-step process where an initial LLM call generates a more focused search query, improving the relevance of the retrieved context for the final answer.
-   **⚙️ Extensive Configuration:** A simple `config.toml` file allows fine-tuning of nearly every aspect, from system prompts and model parameters to RAG optimizer weights.

## Technology Stack 🛠️

-   **Backend:** Python 🐍
-   **LLM Integration:**
    -   `llama-cpp-python` for local GGUF models.
    -   `litellm` for API-based models.
-   **Vector Search:** `faiss-cpu` for efficient RAG indexing and searching. 🔍
-   **CLI Interface:** `argparse` for command parsing and `prompt-toolkit` for rich, multi-line input. ⌨️
-   **Configuration:** `dynaconf` and `toml` for flexible configuration management.
-   **File System:** `watchdog` for live file monitoring.
-   **Caching:** `sqlitedict` for persistent file indexing and RAG optimization caches. 💾

## Architecture 🏗️

The project follows a modular, inheritance-based structure centered around the `BaseAssistant` class.

-   **`main.py`** 🚀: The main entry point that handles argument parsing and dispatches commands to the appropriate modules (`start`, `config`, `models`, etc.).

-   **`cli/`** 🖥️: Contains the logic for all command-line operations.
    -   `start.py`: Initializes the embedding and LLM models, creates the file index, and starts the main chat loop or single-prompt execution.
    -   `config.py`: Manages loading, saving, and defining default configurations.
    -   `models.py`: Provides helper functions to download and manage LLM/embedding models.

-   **`assistant/`** 🧠: The core logic of the AI assistant.
    -   **`base_assistant.py`**: The foundational class that implements core functionalities like RAG (`build_relevant_full_text`), history management (`cull_history_list`), and the main streaming chat loop.
    -   **`cgrag_assistant.py`**: Inherits from `BaseAssistant` and adds the two-step CGRAG logic.
    -   **`git_assistant.py`**: Inherits from `CGRAGAssistant` and adds the logic for creating diffs and committing to Git.
    -   **`llama_cpp_assistant.py` & `lite_llm_assistant.py`**: The final concrete classes inheriting from `GitAssistant`. They implement the `call_completion` and `count_tokens` methods specific to their respective LLM backends.
    -   **`index.py`**: Handles scanning for text files, chunking their content, generating embeddings, and building the `faiss` index.
    -   **`rag_optimizer.py`**: Implements the algorithm to re-rank RAG results based on historical usage, cache hits, and file stability.
    -   **`cache_manager.py`**: Manages the SQLite-based caches for prompt history and optimized prefixes.