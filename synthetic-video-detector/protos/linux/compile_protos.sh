#!/bin/bash

# Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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


# This script compiles Protocol Buffer (protobuf) definitions for NVIDIA Synthetic Video Detector NIM on a Linux Client.
#
# Both gRPC API generations are compiled: the v1 API (nvidia.maxine) and the
# v2 API (nvidia.ai4m). Stubs are emitted under interfaces/ mirroring each
# proto package, so the two generations never collide.
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

mkdir -p "$OUT_DIR"

# Check if Python is installed
if ! command -v python3 > /dev/null; then
    echo "[Error] Python3 is not installed or not in the PATH."
    exit 1
fi

# Log the paths for debugging
echo "Using PROTO_ROOT: $PROTO_ROOT"
echo "Using OUT_DIR: $OUT_DIR"

# Proto files to compile. The v1 service lives in the nvidia.maxine package;
# the v2 service lives in nvidia.ai4m alongside the shared, media-agnostic
# pre-signed URL (ingest) proto it imports.
PROTO_FILES=(
    "$PROTO_ROOT/nvidia/maxine/syntheticvideodetector/v1/syntheticvideodetector.proto"
    "$PROTO_ROOT/nvidia/ai4m/ingest/v1/presigned_url.proto"
    "$PROTO_ROOT/nvidia/ai4m/syntheticvideodetector/v1/syntheticvideodetector.proto"
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
    "$OUT_DIR/nvidia/maxine" \
    "$OUT_DIR/nvidia/maxine/syntheticvideodetector" \
    "$OUT_DIR/nvidia/maxine/syntheticvideodetector/v1" \
    "$OUT_DIR/nvidia/ai4m" \
    "$OUT_DIR/nvidia/ai4m/ingest" \
    "$OUT_DIR/nvidia/ai4m/ingest/v1" \
    "$OUT_DIR/nvidia/ai4m/syntheticvideodetector" \
    "$OUT_DIR/nvidia/ai4m/syntheticvideodetector/v1"; do
    if [ -d "$dir" ] && [ ! -f "$dir/__init__.py" ]; then
        touch "$dir/__init__.py"
    fi
done

echo "gRPC files generated successfully."
