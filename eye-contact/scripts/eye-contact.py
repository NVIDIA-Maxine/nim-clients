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
import eyecontact_pb2  # noqa: E402
import eyecontact_pb2_grpc  # noqa: E402


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

        # Skip the echo response if configuration was sent
        next(responses)

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
    eyecontact_config = EyeContactConfig.from_args(args)

    try:
        eyecontact_config.validate_eyecontact_config()
        validate_ssl_args(args)
        validate_preview_args(args)
    except Exception as e:
        print(f"Invalid configuration: {e}")
        return

    print(eyecontact_config)

    # Prepare request metadata for preview mode
    request_metadata = create_request_metadata(args)

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
