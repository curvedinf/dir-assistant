#!/bin/sh

# Requires pyenv to be installed: https://github.com/pyenv/pyenv-installer
if command -v pyenv 1>/dev/null 2>&1; then
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi
pyenv install 3.11.9 -s
pyenv virtualenv 3.11.9 dir-assistant
pyenv activate dir-assistant
pip install --upgrade pip

echo "Select platform to use:"
echo "1) CPU (OpenBLAS, most compatible)"
echo "2) Cuda"
echo "3) ROCm"
echo "4) Metal"
echo "5) Vulkan"
echo "6) SYCL"
echo "Enter number: "
read platform

case $platform in
    1)
        pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    2)
        CMAKE_ARGS="-DGGML_CUDA=on" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    3)
        CMAKE_ARGS="-DGGML_HIPBLAS=ON" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    4)
        CMAKE_ARGS="-DGGML_METAL=on" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    5)
        CMAKE_ARGS="-DGGML_VULKAN=on" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    6)
		source /opt/intel/oneapi/setvars.sh
        CMAKE_ARGS="-DGGML_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac
