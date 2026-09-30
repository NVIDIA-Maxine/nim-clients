# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: MIT
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

"""Main script for running Eye Contact inference with video files.

This script provides functionality to:
- Parse command line arguments for configuring Eye Contact
- Set up gRPC communication with the Eye Contact service
- Send video data to the service with streaming support
- Process responses and write output video files

The script supports different SSL modes for secure communication and handles
various input/output formats and configurations.
"""

# Standard library imports
import os
import sys
import time
from typing import Iterator
import pathlib

# Third-party imports
import grpc
from tqdm import tqdm

# Setup paths for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(os.path.join(SCRIPT_PATH, "../interfaces"))

# Local imports
from config import EyeContactConfig, parse_args  # noqa: E402
from constants import DATA_CHUNK_SIZE  # noqa: E402
from utils.utils import (  # noqa: E402
    create_channel_credentials,
    validate_ssl_args,
    validate_preview_args,
    create_request_metadata,
)
from nvidia.maxine.eyecontact.v1 import eyecontact_pb2  # noqa: E402
from nvidia.maxine.eyecontact.v1 import eyecontact_pb2_grpc  # noqa: E402

# gRPC metadata key the server inspects to recover the client-assigned session
# id (see NV_AI4M_SESSION_ID_METADATA_KEY on the server; defaults to this).
CLIENT_SESSION_ID_METADATA_KEY = "client-session-id"


def build_request_metadata(args) -> tuple | None:
    """Build the gRPC request metadata, including the client session id.

    Combines the preview-mode metadata (authorization / function-id) with the
    optional client-session-id header so the server can echo it back in
    ServiceInfo and correlate logs.

    Args:
        args: Parsed command line arguments.

    Returns:
        A tuple of ``(key, value)`` metadata pairs, or ``None`` if empty.
    """
    metadata = list(create_request_metadata(args) or ())
    client_session_id = getattr(args, "client_session_id", None)
    if client_session_id:
        metadata.append((CLIENT_SESSION_ID_METADATA_KEY, client_session_id))
    return tuple(metadata) if metadata else None


def print_service_info(service_info) -> None:
    """Print the one-shot ServiceInfo provenance banner from the server.

    Identifies the NIM producing the stream and the request being served
    (feature name/version, model identity, and request/session IDs).

    Args:
        service_info: nvidia.ai4m.common.v1.ServiceInfo message from the response.
    """
    print("\n" + "-" * 60)
    print("Service info (from server)")
    print("-" * 60)
    print(f"Feature name      : {service_info.feature_name}")
    print(f"Feature version   : {service_info.feature_version}")
    print(f"Model info        : {service_info.model_info}")
    print(f"Server request ID : {service_info.server_request_id}")
    print(f"Client session ID : {service_info.client_session_id}")
    print("-" * 60)
    sys.stdout.flush()


def generate_request_for_inference(
    eyecontact_config: EyeContactConfig,
) -> Iterator[eyecontact_pb2.RedirectGazeRequest]:
    """Generate a stream of RedirectGazeRequest messages for the Eye Contact service.

    Args:
        eyecontact_config: Configuration object containing all Eye Contact
            parameters

    Yields:
        RedirectGazeRequest messages containing either configuration or chunks
        of input data

    Raises:
        RuntimeError: If there are errors reading input files
    """
    print("Generating request for inference")

    # Get configuration parameters
    params = eyecontact_config.get_config_params()

    print("Sending data for inference")

    # Send config first
    yield eyecontact_pb2.RedirectGazeRequest(config=eyecontact_pb2.RedirectGazeConfig(**params))

    # Send video data in chunks
    video_chunk_counter = 0

    try:
        with open(eyecontact_config.video_filepath, "rb") as video_file:
            while True:
                video_buffer = video_file.read(DATA_CHUNK_SIZE)
                if video_buffer == b"":
                    break
                video_chunk_counter += 1
                yield eyecontact_pb2.RedirectGazeRequest(video_file_data=video_buffer)
    except IOError as e:
        print(f"Error reading video chunk {video_chunk_counter}: {e}")
        raise RuntimeError(f"Failed to read video file: {e}")

    print("Data sending completed\n")


def write_output_file_from_response(
    response_iter: Iterator[eyecontact_pb2.RedirectGazeResponse],
    output_filepath: os.PathLike = "output.mp4",
) -> None:
    """Function to write the output file from the incoming gRPC data stream.

    Args:
        response_iter: Responses from the server to write into output file
        output_filepath: Path to output file
    """
    print(f"Writing output in {output_filepath}")
    sys.stdout.flush()  # Ensure output is flushed before starting progress bar

    # Initialize progress bar for streaming data reception
    chunk_count = 0
    total_bytes = 0
    service_info_received = False

    with open(output_filepath, "wb") as fd:
        # Create progress bar that shows streaming progress
        # Use leave=False to clean up the progress bar when done
        pbar = tqdm(
            desc="Receiving video chunks",
            unit="chunks",
            unit_scale=False,
            dynamic_ncols=True,
            leave=False,
            bar_format="{desc}: {n} chunks | {rate_fmt} | {postfix}",
        )

        try:
            for response in response_iter:
                if response.HasField("service_info"):
                    if not service_info_received:
                        print_service_info(response.service_info)
                        service_info_received = True
                    continue

                if response.HasField("video_file_data"):
                    chunk_data = response.video_file_data
                    fd.write(chunk_data)

                    # Update progress tracking
                    chunk_count += 1
                    total_bytes += len(chunk_data)

                    # Update progress bar
                    pbar.update(1)
                    pbar.set_postfix_str(f"{total_bytes / (1024*1024):.1f} MB received")
        finally:
            pbar.close()

    print(
        f"Completed: Received {chunk_count} chunks " f"({total_bytes / (1024*1024):.1f} MB total)"
    )


def process_request(
    channel: grpc.Channel,
    eyecontact_config: EyeContactConfig,
    request_metadata: tuple = None,
) -> None:
    """Process gRPC request and handle responses.

    Args:
        channel: gRPC channel for server client communication
        eyecontact_config: Configuration for the Eye Contact service
        request_metadata: Credentials to process preview request

    Raises:
        Exception: If any errors occur during processing
    """
    try:
        stub = eyecontact_pb2_grpc.MaxineEyeContactServiceStub(channel)
        start_time = time.time()

        responses = stub.RedirectGaze(
            generate_request_for_inference(eyecontact_config=eyecontact_config),
            metadata=request_metadata,
        )

        write_output_file_from_response(
            response_iter=responses, output_filepath=eyecontact_config.output_filepath
        )
        end_time = time.time()
        print(f"Function invocation completed in {end_time-start_time:.2f}s")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    """Main entry point for the Eye Contact client.

    Handles:
    1. Argument parsing
    2. Configuration validation
    3. Channel setup (secure/insecure)
    4. Request processing
    """
    args = parse_args()

    try:
        eyecontact_config = EyeContactConfig.from_args(args)
        eyecontact_config.validate_eyecontact_config()
        validate_ssl_args(args)
        validate_preview_args(args)
    except Exception as e:
        print(f"Invalid configuration: {e}")
        return

    print(eyecontact_config)

    # Prepare request metadata for preview mode and log correlation
    request_metadata = build_request_metadata(args)

    # Check ssl-mode and create channel_credentials for that mode
    if args.ssl_mode != "DISABLED":
        channel_credentials = create_channel_credentials(args)
        # Establish secure channel when ssl-mode is MTLS/TLS
        with grpc.secure_channel(target=args.target, credentials=channel_credentials) as channel:
            process_request(
                channel=channel,
                eyecontact_config=eyecontact_config,
                request_metadata=request_metadata,
            )
    elif args.preview_mode:
        # Establish secure channel when sending request to NVCF server
        with grpc.secure_channel(
            target=args.target, credentials=grpc.ssl_channel_credentials()
        ) as channel:
            process_request(
                channel=channel,
                eyecontact_config=eyecontact_config,
                request_metadata=request_metadata,
            )
    else:
        # Establish insecure channel when ssl-mode is DISABLED
        print(f"Establishing insecure channel to {args.target}")
        with grpc.insecure_channel(target=args.target) as channel:
            process_request(
                channel=channel,
                eyecontact_config=eyecontact_config,
                request_metadata=request_metadata,
            )


if __name__ == "__main__":
    main()
