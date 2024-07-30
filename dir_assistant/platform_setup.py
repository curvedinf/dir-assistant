import os

from dir_assistant.config import save_config


def platform(args, config_dict):
    is_cpu = False
    cmake_args = ''
    if args.selection == 'cpu':
        is_cpu = True
    elif args.selection == 'cuda':
        cmake_args = '-DGGML_CUDA=on'
    elif args.selection == 'rocm':
        cmake_args = '-DGGML_HIPBLAS=ON'
    elif args.selection == 'metal':
        cmake_args = '-DGGML_METAL=on'
    elif args.selection == 'vulkan':
        cmake_args = '-DGGML_VULKAN=on'
    elif args.selection == 'sycl':
        cmake_args = '-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx'
    else:
        raise ValueError("Invalid platform selection.")

    # Install llama-cpp-python with the selected platform cmake_args
    os.system(f"CMAKE_ARGS='{cmake_args}' pip install --upgrade --force-reinstall --no-cache-dir llama-cpp-python faiss-cpu")

    if is_cpu:
        if 'n_gpu_layers' in config_dict['LLAMA_CPP_OPTIONS']:
            del config_dict['LLAMA_CPP_OPTIONS']['n_gpu_layers']
        if 'n_gpu_layers' in config_dict['LLAMA_CPP_EMBED_OPTIONS']:
            del config_dict['LLAMA_CPP_EMBED_OPTIONS']['n_gpu_layers']
    else:
        config_dict['LLAMA_CPP_OPTIONS']['n_gpu_layers'] = -1
        config_dict['LLAMA_CPP_EMBED_OPTIONS']['n_gpu_layers'] = -1

    save_config({'DIR_ASSISTANT': config_dict})

