:: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
::
:: Permission is hereby granted, free of charge, to any person obtaining a
:: copy of this software and associated documentation files (the "Software"),
:: to deal in the Software without restriction, including without limitation
:: the rights to use, copy, modify, merge, publish, distribute, sublicense,
:: and/or sell copies of the Software, and to permit persons to whom the
:: Software is furnished to do so, subject to the following conditions:
::
:: The above copyright notice and this permission notice shall be included in
:: all copies or substantial portions of the Software.
::
:: THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
:: IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
:: FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
:: THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
:: LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
:: FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
:: DEALINGS IN THE SOFTWARE.


:: This script compiles Protocol Buffer (protobuf) definitions for NVIDIA Maxine Eye-Contact NIM on a Windows Client.
::
:: Execute the script using `compile_protos.bat`.
::
:: For more details, refer to README.txt.


@echo off
setlocal

:: Define the script directory
set "SCRIPT_DIR=%~dp0"

:: Define the protobufs and output directories
set "PROTOS_DIR=%SCRIPT_DIR%..\proto"
set "OUT_DIR=%SCRIPT_DIR%..\..\interfaces\"

:: Log the paths for debugging
echo "Using PROTOS_DIR: %PROTOS_DIR%"
echo "Using OUT_DIR: %OUT_DIR%"

:: Check if Python is installed
where python >nul 2>&1
if errorlevel 1 (
    echo [Error] Python is not installed or not in the PATH.
    exit /b 1
)

:: Run grpc_tools.protoc to generate Python gRPC code
python -m grpc_tools.protoc -I=%PROTOS_DIR% ^
                            --python_out=%OUT_DIR% ^
                            --pyi_out=%OUT_DIR% ^
                            --grpc_python_out=%OUT_DIR% ^
                            %PROTOS_DIR%\nvidia\ai4m\common\v1\service_info.proto ^
                            %PROTOS_DIR%\nvidia\maxine\eyecontact\v1\eyecontact.proto
if errorlevel 1 (
    echo [Error] Failed to execute grpc_tools.protoc. Please check the paths and dependencies.
    exit /b 1
)

echo "gRPC files generated successfully."
endlocal

