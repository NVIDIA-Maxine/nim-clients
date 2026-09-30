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


# This script compiles Protocol Buffer (protobuf) definitions for NVIDIA Maxine Eye-Contact NIM on a Linux Client.
#
# Execute the script using `./compile_protos.sh`
#
# For more details, refer to README.md


# Get the script directory's parent directory
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
echo $SCRIPT_DIR
# Define paths for proto files and output directory
PROTOS_DIR=$(realpath "$SCRIPT_DIR/../proto/")
OUT_DIR=$(realpath "$SCRIPT_DIR/../../interfaces/")

EYECONTACT_PROTO="$PROTOS_DIR/nvidia/maxine/eyecontact/v1/eyecontact.proto"
SERVICE_INFO_PROTO="$PROTOS_DIR/nvidia/ai4m/common/v1/service_info.proto"

# Check if required directories and files exist
if [ ! -d "$PROTOS_DIR" ]; then
    echo "[Error] Protos directory does not exist: $PROTOS_DIR"
    exit 1
fi

for proto_file in "$EYECONTACT_PROTO" "$SERVICE_INFO_PROTO"; do
    if [ ! -f "$proto_file" ]; then
        echo "[Error] Protobuf file not found: $proto_file"
        exit 1
    fi
done

# Check if Python is installed
if ! command -v python3 > /dev/null; then
    echo "[Error] Python3 is not installed or not in the PATH."
    exit 1
fi

# Log the paths for debugging
echo "Using PROTOS_DIR: $PROTOS_DIR"
echo "Using OUT_DIR: $OUT_DIR"

# Run grpc_tools.protoc
python3 -m grpc_tools.protoc -I="$PROTOS_DIR" \
                             --python_out="$OUT_DIR" \
                             --pyi_out="$OUT_DIR" \
                             --grpc_python_out="$OUT_DIR" \
                             "$SERVICE_INFO_PROTO" \
                             "$EYECONTACT_PROTO"

# Check if the command succeeded
if [ $? -ne 0 ]; then
    echo "[Error] Failed to execute grpc_tools.protoc."
    exit 1
fi

echo "gRPC files generated successfully."

