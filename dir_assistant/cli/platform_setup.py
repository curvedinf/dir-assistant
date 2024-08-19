import os

from dir_assistant.cli.config import save_config


def platform(args, config_dict):
    is_cpu = False
    is_cuda = False
    cmake_args = ""
    if args.selection.lower() == "cpu":
        is_cpu = True
    elif args.selection.lower() == "cuda":
        cmake_args = "-DGGML_CUDA=on"
        is_cuda = True
    elif args.selection.lower() == "rocm":
        cmake_args = "-DGGML_HIPBLAS=ON"
    elif args.selection.lower() == "metal":
        cmake_args = "-DGGML_METAL=on"
    elif args.selection.lower() == "vulkan":
        cmake_args = "-DGGML_VULKAN=on"
    elif args.selection.lower() == "sycl":
        cmake_args = "-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx"
    else:
        raise ValueError("Invalid platform selection.")

    # Install llama-cpp-python with the selected platform cmake_args
    if args.pipx:
        # pip3 has been replaced with pipx on Ubuntu 24.04
        os.system(
            f"CMAKE_ARGS='{cmake_args}' pipx runpip dir-assistant install --upgrade --force-reinstall --no-cache-dir llama-cpp-python faiss-cpu"
        )
    else:
        os.system(
            f"CMAKE_ARGS='{cmake_args}' pip install --upgrade --force-reinstall --no-cache-dir llama-cpp-python faiss-cpu"
        )

    if is_cpu:
        if "n_gpu_layers" in config_dict["LLAMA_CPP_OPTIONS"]:
            del config_dict["LLAMA_CPP_OPTIONS"]["n_gpu_layers"]
        if "n_gpu_layers" in config_dict["LLAMA_CPP_EMBED_OPTIONS"]:
            del config_dict["LLAMA_CPP_EMBED_OPTIONS"]["n_gpu_layers"]
    else:
        config_dict["LLAMA_CPP_OPTIONS"]["n_gpu_layers"] = -1
        config_dict["LLAMA_CPP_EMBED_OPTIONS"]["n_gpu_layers"] = -1
        if is_cuda:
            config_dict["LLAMA_CPP_OPTIONS"]["flash_attn"] = True
            config_dict["LLAMA_CPP_EMBED_OPTIONS"]["flash_attn"] = True

    save_config({"DIR_ASSISTANT": config_dict})
