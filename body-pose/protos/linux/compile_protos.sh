#!/bin/bash

# Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


# This script compiles Protocol Buffer (protobuf) definitions for NVIDIA 3D Body Pose NIM on a Linux Client.
#
# Execute the script using `./compile_protos.sh`
#
# For more details, refer to README.md


# Get the script directory's parent directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# Define paths for proto files and output directory
PROTO_ROOT=$(realpath "$SCRIPT_DIR/../proto")
OUT_DIR=$(realpath "$SCRIPT_DIR/../../interfaces/")

# Check if required directories exist
if [ ! -d "$PROTO_ROOT" ]; then
    echo "[Error] Proto root directory does not exist: $PROTO_ROOT"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 > /dev/null; then
    echo "[Error] Python3 is not installed or not in the PATH."
    exit 1
fi

# Log the paths for debugging
echo "Using PROTO_ROOT: $PROTO_ROOT"
echo "Using OUT_DIR: $OUT_DIR"

# Proto files to compile
PROTO_FILES=(
    "$PROTO_ROOT/nvidia/ai4m/common/v1/service_info.proto"
    "$PROTO_ROOT/nvidia/ai4m/body_pose/v1/body_pose.proto"
)

# Verify all proto files exist
for proto in "${PROTO_FILES[@]}"; do
    if [ ! -f "$proto" ]; then
        echo "[Error] Protobuf file not found: $proto"
        exit 1
    fi
done

# Run grpc_tools.protoc for all protos
python3 -m grpc_tools.protoc -I="$PROTO_ROOT" \
                             --python_out="$OUT_DIR" \
                             --pyi_out="$OUT_DIR" \
                             --grpc_python_out="$OUT_DIR" \
                             "${PROTO_FILES[@]}"

# Check if the command succeeded
if [ $? -ne 0 ]; then
    echo "[Error] Failed to execute grpc_tools.protoc."
    exit 1
fi

# Create __init__.py files for the package hierarchy
for dir in \
    "$OUT_DIR/nvidia" \
    "$OUT_DIR/nvidia/ai4m" \
    "$OUT_DIR/nvidia/ai4m/body_pose" \
    "$OUT_DIR/nvidia/ai4m/body_pose/v1" \
    "$OUT_DIR/nvidia/ai4m/common" \
    "$OUT_DIR/nvidia/ai4m/common/v1"; do
    if [ -d "$dir" ] && [ ! -f "$dir/__init__.py" ]; then
        touch "$dir/__init__.py"
    fi
done

echo "gRPC files generated successfully."
