@echo off
REM Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

REM This script compiles Protocol Buffer (protobuf) definitions for NVIDIA Active Speaker Detection NIM on Windows.
REM
REM Execute the script using `compile_protos.bat`
REM
REM For more details, refer to README.md

setlocal

REM Get the script directory
set "SCRIPT_DIR=%~dp0"

REM Define paths for proto files and output directory
set PROTOS_DIR=%SCRIPT_DIR%..\proto
set OUT_DIR=%SCRIPT_DIR%..\..\interfaces

REM Check if required directories and files exist
if not exist "%PROTOS_DIR%" (
    echo [Error] Protos directory does not exist: %PROTOS_DIR%
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [Error] Python is not installed or not in the PATH.
    exit /b 1
)

REM Log the paths for debugging
echo Using PROTOS_DIR: %PROTOS_DIR%
echo Using OUT_DIR: %OUT_DIR%

REM Run grpc_tools.protoc
python -m grpc_tools.protoc -I="%PROTOS_DIR%" --python_out="%OUT_DIR%" --pyi_out="%OUT_DIR%" --grpc_python_out="%OUT_DIR%" ^
    "%PROTOS_DIR%\nvidia\ai4m\audio\v1\audio.proto" ^
    "%PROTOS_DIR%\nvidia\ai4m\common\v1\common.proto" ^
    "%PROTOS_DIR%\nvidia\ai4m\common\v1\service_info.proto" ^
    "%PROTOS_DIR%\nvidia\ai4m\video\v1\video.proto" ^
    "%PROTOS_DIR%\nvidia\ai4m\activespeakerdetection\v1\activespeakerdetection.proto"
if %ERRORLEVEL% neq 0 (
    echo [Error] Failed to execute grpc_tools.protoc.
    exit /b 1
)

echo gRPC files generated successfully.

endlocal
