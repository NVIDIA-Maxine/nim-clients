# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Main script for running Synthetic Video Detection with video files.

This script provides functionality to:
- Parse command line arguments for configuring Synthetic Video Detector
- Set up gRPC communication with the Synthetic Video Detector service
- Send video data to the service
- Process responses and display detection results

The script supports different SSL modes for secure communication and handles
video file input and CSV result output.
"""

# Standard library imports
import math
import os
import pathlib
import sys
import time
from typing import Iterator, Optional

# Third-party imports
import grpc
from tqdm import tqdm

# Local imports
from config import SyntheticDetectorConfig, parse_args  # noqa: E402
from constants import DATA_CHUNK_SIZE, CLASSIFICATION_THRESHOLD  # noqa: E402

# Setup paths for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.insert(0, os.path.join(SCRIPT_PATH, "../../interfaces"))

# Import utils functions
from utils.utils import (  # noqa: E402
    create_channel_credentials,
    create_request_metadata,
    validate_preview_args,
    validate_ssl_args,
)

from nvidia.maxine.syntheticvideodetector.v1 import (  # noqa: E402
    syntheticvideodetector_pb2,
    syntheticvideodetector_pb2_grpc,
)


def generate_request_for_inference(
    video_filepath: str,
) -> Iterator[syntheticvideodetector_pb2.DetectSyntheticVideoRequest]:
    """Generate a stream of DetectSyntheticVideoRequest messages for the service.

    Args:
        video_filepath: Path to the input video

    Yields:
        DetectSyntheticVideoRequest messages containing chunks of input video data

    Raises:
        RuntimeError: If there are errors reading input files
    """
    print("Generating request for inference")
    print("Sending video data...")

    # Send video data in chunks
    video_chunk_counter = 0

    try:
        file_size = os.path.getsize(video_filepath)
        print(f"Video file size: {file_size / (1024*1024):.2f} MB")

        with open(video_filepath, "rb") as video_file:
            # Create progress bar for sending data
            with tqdm(
                total=file_size,
                desc="Uploading video",
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                dynamic_ncols=True,
            ) as pbar:
                while True:
                    video_buffer = video_file.read(DATA_CHUNK_SIZE)
                    if video_buffer == b"":
                        break
                    video_chunk_counter += 1
                    pbar.update(len(video_buffer))
                    yield syntheticvideodetector_pb2.DetectSyntheticVideoRequest(
                        video_file_data=video_buffer
                    )

        print(f"\nData sending completed ({video_chunk_counter} chunks)\n")

    except IOError as e:
        print(f"Error reading video chunk {video_chunk_counter}: {e}")
        raise RuntimeError(f"Failed to read video file: {e}")


def fmt_elapsed(sec: float) -> str:
    """Format elapsed time in seconds as a MM:SS string.

    Args:
        sec: Time in seconds to format

    Returns:
        Formatted time string in MM:SS format (e.g., "03:45" for 225 seconds)
    """
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"


def write_output_file_from_response(
    response_iter: Iterator[syntheticvideodetector_pb2.DetectSyntheticVideoResponse],
    csv_output: Optional[str],
) -> None:
    """Write output file from incoming gRPC data stream (CSV for detector).

    Args:
        response_iter: Responses from the server to process
        csv_output: Path to save CSV file, or None to skip saving
    """
    if csv_output:
        print(f"Processing detection responses and writing CSV to {csv_output}")
    else:
        print("Processing detection responses")
    sys.stdout.flush()

    frame_results = []
    final_result = None
    response_count = 0
    start_time = time.time()

    try:
        for response in response_iter:
            response_count += 1

            if response.HasField("clip_result"):
                frame_results.append(response.clip_result)
            elif response.HasField("final_result"):
                final_result = response.final_result
            elif response.HasField("keepalive"):
                pass

        # Print results
        elapsed_total = time.time() - start_time
        print("\n" + "=" * 60)
        print("DETECTION RESULTS")
        print("=" * 60)
        print(f"Total responses received: {response_count}")
        print(f"Frame results received: {len(frame_results)}")
        print(f"Processing time: {fmt_elapsed(elapsed_total)}")

        if final_result:
            print("\nFinal Statistics:")
            # Map API field name to consistent terminology
            total_frames = final_result.total_clips
            print(f"  Total frames processed: {total_frames}")
            print(f"  Final logit: {final_result.logit:.6f}")
            print(f"  Final probability: {final_result.probability:.6f}")

            # Determine if video is likely synthetic
            if final_result.probability > CLASSIFICATION_THRESHOLD:
                verdict = "SYNTHETIC"
                confidence = final_result.probability * 100
            else:
                verdict = "REAL"
                confidence = (1.0 - final_result.probability) * 100

            print(f"\n{'*' * 60}")
            print(f"VERDICT: {verdict} (confidence: {confidence:.2f}%)")
            print(f"{'*' * 60}\n")

            # Save CSV only when csv_output is specified
            if csv_output:
                # Prefer locally accumulated frame_results to construct CSV as index,probability
                if len(frame_results) > 0:
                    with open(csv_output, "w") as f:
                        f.write("index,probability\n")
                        for fr in frame_results:
                            try:
                                p = 1.0 / (1.0 + math.exp(-fr.logit))
                            except OverflowError:
                                p = 0.0 if fr.logit < 0 else 1.0
                            f.write(f"{fr.index},{p:.6f}\n")
                    print(f"CSV data saved to: {csv_output}")
                elif len(final_result.csv_data) > 0:
                    # Fallback: transform server csv_data (index,logit) into index,probability
                    lines = [
                        ln.strip()
                        for ln in final_result.csv_data.strip().splitlines()
                        if ln.strip()
                    ]
                    rows = []
                    for ln in lines:
                        parts = [p.strip() for p in ln.split(",")]
                        if len(parts) < 2:
                            continue
                        # Skip header-like rows if present
                        try:
                            idx_val = int(parts[0])
                            logit_val = float(parts[1])
                        except ValueError:
                            continue
                        try:
                            prob_val = 1.0 / (1.0 + math.exp(-logit_val))
                        except OverflowError:
                            prob_val = 0.0 if logit_val < 0 else 1.0
                        rows.append((idx_val, prob_val))
                    if rows:
                        with open(csv_output, "w") as f:
                            f.write("index,probability\n")
                            for idx_val, prob_val in rows:
                                f.write(f"{idx_val},{prob_val:.6f}\n")
                        print(f"CSV data saved to: {csv_output}")
        else:
            print("Warning: No final result received")

        print("=" * 60)

    except grpc.RpcError as e:
        print(f"\nGRPC Error: {e.code()} - {e.details()}")
        raise
    except Exception as e:
        print(f"\nError: {e}")
        raise


def process_request(
    channel: grpc.Channel,
    video_filepath: str,
    csv_output: Optional[str],
    request_metadata: Optional[tuple] = None,
) -> None:
    """Process gRPC request and handle responses.

    Args:
        channel: gRPC channel for communication with the Synthetic Video
            Detector service
        video_filepath: Path to the input video file to be analyzed
        csv_output: Path to save CSV results, or None to skip saving
        request_metadata: Optional tuple of metadata to include in the gRPC
            request (used for preview mode authentication)
    """
    try:
        stub = syntheticvideodetector_pb2_grpc.SyntheticVideoDetectorServiceStub(channel)
        start_time = time.time()

        responses = stub.DetectSyntheticVideo(
            generate_request_for_inference(video_filepath=video_filepath),
            metadata=request_metadata,
        )

        write_output_file_from_response(
            response_iter=responses,
            csv_output=csv_output,
        )
        end_time = time.time()
        print(f"Function invocation completed in {end_time-start_time:.2f}s")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise  # Re-raise the exception to propagate to the caller


def main():
    """Main entry point for the Synthetic Video Detector client."""
    # Parse command line arguments using shared config
    args = parse_args()

    # Validate SSL and preview mode arguments
    try:
        validate_ssl_args(args)
        validate_preview_args(args)
    except RuntimeError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Build and validate config
    try:
        detector_config = SyntheticDetectorConfig.from_args(args)
        detector_config.validate_synthetic_config()
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    # Guard: If function ID or API key are provided without target, exit
    target = getattr(args, "target", None)
    function_id = getattr(args, "function_id", None)
    api_key = getattr(args, "ngc_api_key", None) or getattr(args, "api_key", None)
    if (function_id or api_key) and (target is None or str(target).strip() == ""):
        print(
            "Configuration error: '--target' must be provided when using "
            "'--function-id' or an NGC API key."
        )
        sys.exit(1)

    # Print configuration and connection info
    print(detector_config)
    print(f"Server      : {args.target}")
    print(f"SSL mode    : {args.ssl_mode}")
    if args.preview_mode:
        print("Preview mode: Enabled")
        print(f"Function ID : {args.function_id}")
    print("=" * 60 + "\n")

    # Prepare request metadata for preview mode
    request_metadata = create_request_metadata(args)

    # Run detection
    try:
        # Create channel based on SSL mode or preview mode
        if args.ssl_mode != "DISABLED":
            channel_credentials = create_channel_credentials(args)
            print(f"Establishing secure channel to {args.target}")
            with grpc.secure_channel(args.target, channel_credentials) as channel:
                process_request(
                    channel=channel,
                    video_filepath=detector_config.video_filepath,
                    csv_output=detector_config.csv_output,
                    request_metadata=request_metadata,
                )
        elif args.preview_mode:
            print(f"Connecting to NVCF preview server at {args.target}")
            with grpc.secure_channel(
                args.target, credentials=grpc.ssl_channel_credentials()
            ) as channel:
                process_request(
                    channel=channel,
                    video_filepath=detector_config.video_filepath,
                    csv_output=detector_config.csv_output,
                    request_metadata=request_metadata,
                )
        else:
            print(f"Establishing insecure channel to {args.target}")
            with grpc.insecure_channel(args.target) as channel:
                process_request(
                    channel=channel,
                    video_filepath=detector_config.video_filepath,
                    csv_output=detector_config.csv_output,
                    request_metadata=request_metadata,
                )

        print("\nDetection completed successfully!")

    except grpc.RpcError as e:
        print(f"\nGRPC Error: {e.code()} - {e.details()}")
        if e.code() == grpc.StatusCode.UNIMPLEMENTED:
            print(
                "\nThe server did not recognize this request. This is the v1 client "
                "(API nvidia.maxine.syntheticvideodetector.v1); the target server appears "
                "to be a v2 (nvidia.ai4m) deployment.\n"
                "Use the v2 client for a v2 (self-hosted) server, or point --target at a "
                "v1/NVCF Synthetic Video Detector deployment."
            )
        print("\nDetection failed!")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
