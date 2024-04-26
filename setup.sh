#!/bin/sh

# Requires pyenv to be installed: https://github.com/pyenv/pyenv-installer
if command -v pyenv 1>/dev/null 2>&1; then
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
fi
pyenv install 3.11 -s
pyenv virtualenv 3.11 dir-assistant
pyenv activate dir-assistant
pip install --upgrade pip

echo "Select platform to use:"
echo "1) CPU (OpenBLAS, most compatible)"
echo "2) Cuda"
echo "3) ROCm"
echo "4) Metal"
echo "5) OpenCL"
echo "6) Vulkan"
echo "7) Kompute"
echo "8) SYCL"
echo "Enter number: "
read platform

case $platform in
    1)
        pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    2)
        CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    3)
        CMAKE_ARGS="-DLLAMA_HIPBLAS=ON" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    4)
        CMAKE_ARGS="-DLLAMA_METAL=on" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    5)
        CMAKE_ARGS="-DLLAMA_CLBLAST=on" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    6)
        CMAKE_ARGS="-DLLAMA_VULKAN=on" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    7)
        CMAKE_ARGS="-DLLAMA_KOMPUTE=on" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    8)
        CMAKE_ARGS="-DLLAMA_SYCL=on -DCMAKE_C_COMPILER=icx -DCMAKE_CXX_COMPILER=icpx" pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac
