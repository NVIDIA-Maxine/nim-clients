@echo off
REM Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
REM
REM Permission is hereby granted, free of charge, to any person obtaining a
REM copy of this software and associated documentation files (the "Software"),
REM to deal in the Software without restriction, including without limitation
REM the rights to use, copy, modify, merge, publish, distribute, sublicense,
REM and/or sell copies of the Software, and to permit persons to whom the
REM Software is furnished to do so, subject to the following conditions:
REM
REM The above copyright notice and this permission notice shall be included in
REM all copies or substantial portions of the Software.
REM
REM THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
REM IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
REM FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
REM THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
REM LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
REM FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
REM DEALINGS IN THE SOFTWARE.

REM This script compiles Protocol Buffer (protobuf) definitions for NVIDIA Synthetic Video Detector NIM on Windows.
REM
REM Both gRPC API generations are compiled: the v1 API (nvidia.maxine) and the
REM v2 API (nvidia.ai4m). Stubs are emitted under interfaces\ mirroring each
REM proto package, so the two generations never collide.
REM
REM Execute the script using `compile_protos.bat`
REM
REM For more details, refer to README.md

setlocal

REM Get the script directory
set SCRIPT_DIR=%~dp0

REM Define paths for proto files and output directory
set PROTO_ROOT=%SCRIPT_DIR%..\proto
set OUT_DIR=%SCRIPT_DIR%..\..\interfaces

REM The v1 service lives in the nvidia.maxine package; the v2 service lives in
REM nvidia.ai4m alongside the shared pre-signed URL (ingest) proto it imports.
set MAXINE_SVD=%PROTO_ROOT%\nvidia\maxine\syntheticvideodetector\v1\syntheticvideodetector.proto
set AI4M_INGEST=%PROTO_ROOT%\nvidia\ai4m\ingest\v1\presigned_url.proto
set AI4M_SVD=%PROTO_ROOT%\nvidia\ai4m\syntheticvideodetector\v1\syntheticvideodetector.proto

REM Check if required files exist
if not exist "%MAXINE_SVD%" (
    echo [Error] Protobuf file not found: %MAXINE_SVD%
    exit /b 1
)

if not exist "%AI4M_INGEST%" (
    echo [Error] Protobuf file not found: %AI4M_INGEST%
    exit /b 1
)

if not exist "%AI4M_SVD%" (
    echo [Error] Protobuf file not found: %AI4M_SVD%
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [Error] Python is not installed or not in the PATH.
    exit /b 1
)

if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

REM Log the paths for debugging
echo Using PROTO_ROOT: %PROTO_ROOT%
echo Using OUT_DIR: %OUT_DIR%

REM Run grpc_tools.protoc
python -m grpc_tools.protoc -I="%PROTO_ROOT%" --python_out="%OUT_DIR%" --pyi_out="%OUT_DIR%" --grpc_python_out="%OUT_DIR%" "%MAXINE_SVD%" "%AI4M_INGEST%" "%AI4M_SVD%"

REM Check if the command succeeded
if %ERRORLEVEL% neq 0 (
    echo [Error] Failed to execute grpc_tools.protoc.
    exit /b 1
)

REM Create __init__.py files for the package hierarchy
for %%D in (
    "%OUT_DIR%\nvidia"
    "%OUT_DIR%\nvidia\maxine"
    "%OUT_DIR%\nvidia\maxine\syntheticvideodetector"
    "%OUT_DIR%\nvidia\maxine\syntheticvideodetector\v1"
    "%OUT_DIR%\nvidia\ai4m"
    "%OUT_DIR%\nvidia\ai4m\ingest"
    "%OUT_DIR%\nvidia\ai4m\ingest\v1"
    "%OUT_DIR%\nvidia\ai4m\syntheticvideodetector"
    "%OUT_DIR%\nvidia\ai4m\syntheticvideodetector\v1"
) do (
    if exist %%D if not exist %%D\__init__.py type nul > %%D\__init__.py
)

echo gRPC files generated successfully.

endlocal
