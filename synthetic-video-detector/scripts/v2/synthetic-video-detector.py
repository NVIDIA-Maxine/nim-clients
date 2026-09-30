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
- Send video data to the service, either as streamed byte chunks or via a
  single pre-signed URL (S3 ingest) request
- Process responses and display detection results

The script supports different SSL modes for secure communication with a
self-hosted server. Video input can be a local MP4 file (byte streaming) or a
pre-signed HTTPS URL (S3 ingest).
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
from config import (  # noqa: E402
    PresignedUrlConfig,
    SyntheticDetectorConfig,
    parse_args,
)
from constants import DATA_CHUNK_SIZE, CLASSIFICATION_THRESHOLD  # noqa: E402

# Setup paths for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.insert(0, os.path.join(SCRIPT_PATH, "../../interfaces"))

# Import utils functions
from utils.utils import (  # noqa: E402
    create_channel_credentials,
    redact_url,
    validate_ssl_args,
)

from nvidia.ai4m.ingest.v1 import presigned_url_pb2 as ingest_pb2  # noqa: E402
from nvidia.ai4m.syntheticvideodetector.v1 import (  # noqa: E402
    syntheticvideodetector_pb2,
    syntheticvideodetector_pb2_grpc,
)

# Maps between the CLI string choices and the generated protobuf enum values
_CHECKSUM_TYPE = {
    "md5": ingest_pb2.CHECKSUM_TYPE_MD5,
    "sha256": ingest_pb2.CHECKSUM_TYPE_SHA256,
    "sha512": ingest_pb2.CHECKSUM_TYPE_SHA512,
}
_CHECKSUM_HEX_FIELD = {"md5": "md5_hex", "sha256": "sha256_hex", "sha512": "sha512_hex"}
_PROVIDER = {
    "unspecified": ingest_pb2.URL_PROVIDER_UNSPECIFIED,
    "s3": ingest_pb2.URL_PROVIDER_S3,
}


def is_streamable_mp4(video_filepath: str) -> Optional[bool]:
    """Best-effort check whether an MP4 is "streamable" (faststart).

    A streamable MP4 has its ``moov`` metadata atom immediately after the
    ``ftyp`` atom, so the NIM can begin decoding and running inference while the
    upload is still in flight (streaming mode). Otherwise the NIM must receive
    the whole file first (transactional mode). The NIM selects the mode
    automatically; this is only used to inform the user.

    Args:
        video_filepath: Path to the input MP4 file.

    Returns:
        True if streamable, False if not, or None if it cannot be determined.
    """
    try:
        with open(video_filepath, "rb") as f:
            header = f.read(8)
            if len(header) < 8 or header[4:8] != b"ftyp":
                return None
            ftyp_size = int.from_bytes(header[0:4], byteorder="big")
            if ftyp_size <= 0:
                return None
            f.seek(ftyp_size)
            next_atom = f.read(8)
        if len(next_atom) < 8:
            return None
        return next_atom[4:8] == b"moov"
    except Exception:
        return None


def _print_processing_mode(video_filepath: str) -> None:
    """Print which NIM processing mode (streaming vs transactional) will apply."""
    streamable = is_streamable_mp4(video_filepath)
    if streamable is True:
        print(
            "Input MP4 is streamable (faststart): the NIM will use streaming mode "
            "(inference overlaps upload for lowest latency)."
        )
    elif streamable is False:
        print(
            "Input MP4 is not streamable: the NIM will use transactional mode "
            "(full upload, then inference). For streaming mode, convert with "
            "'ffmpeg -i in.mp4 -movflags +faststart out.mp4'."
        )


def _build_presigned_url(cfg: PresignedUrlConfig) -> ingest_pb2.PresignedUrl:
    """Build a PresignedUrl message from the pre-signed URL configuration.

    This is a thin pass-through of user-provided fields. All validation
    (HTTPS, host allowlist, expiry, SSRF, checksum, size, content-type) is
    performed by the NIM, so the client stays lean.

    Args:
        cfg: The pre-signed URL configuration.

    Returns:
        A populated PresignedUrl protobuf message.
    """
    obj = ingest_pb2.PresignedUrl(url=cfg.url)
    obj.url_provider = _PROVIDER[cfg.url_provider]

    if cfg.no_verify_checksum:
        obj.verify_checksum = False
    elif cfg.checksum:
        obj.verify_checksum = True
        checksum = ingest_pb2.FileChecksum(type=_CHECKSUM_TYPE[cfg.checksum_type])
        setattr(checksum, _CHECKSUM_HEX_FIELD[cfg.checksum_type], cfg.checksum.lower())
        obj.checksum.CopyFrom(checksum)

    if cfg.expected_size is not None:
        obj.expected_content_length_bytes = cfg.expected_size
    if cfg.content_type:
        obj.content_type = cfg.content_type
    if cfg.expires_at_unix_ms is not None:
        obj.expires_at_unix_ms = cfg.expires_at_unix_ms

    return obj


def generate_request_for_inference(
    detector_config: SyntheticDetectorConfig,
) -> Iterator[syntheticvideodetector_pb2.DetectSyntheticVideoRequest]:
    """Generate the request stream for the service (both input modes).

    - Pre-signed URL mode: yields exactly one request carrying the PresignedUrl,
      then closes the client side of the stream. The NIM downloads, validates,
      and analyzes the object.
    - Byte-streaming mode: yields the local MP4 file in chunks.

    Args:
        detector_config: Resolved client configuration selecting the input mode.

    Yields:
        DetectSyntheticVideoRequest messages.

    Raises:
        RuntimeError: If there are errors reading the input file.
    """
    print("Generating request for inference")

    # Pre-signed URL (S3 ingest) mode: a single request message.
    if detector_config.use_presigned:
        cfg = detector_config.presigned
        print(f"Object URL   : {redact_url(cfg.url)}")
        print(f"URL provider : {cfg.url_provider}")
        if cfg.no_verify_checksum:
            print("Checksum     : verification disabled")
        elif cfg.checksum:
            print(f"Checksum     : {cfg.checksum_type}={cfg.checksum}")
        print("Sending pre-signed URL request...")
        yield syntheticvideodetector_pb2.DetectSyntheticVideoRequest(
            presigned_url=_build_presigned_url(cfg)
        )
        return

    # Byte-streaming mode: send the local MP4 file in chunks.
    video_filepath = detector_config.video_filepath
    print("Sending video data...")
    video_chunk_counter = 0

    try:
        file_size = os.path.getsize(video_filepath)
        print(f"Video file size: {file_size / (1024*1024):.2f} MB")
        _print_processing_mode(video_filepath)

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
        raise RuntimeError(f"Failed to read video file: {e}") from e


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


def _logit_to_probability(logit: float) -> float:
    """Convert a raw model logit to a probability using a sigmoid transform."""
    try:
        return 1.0 / (1.0 + math.exp(-logit))
    except OverflowError:
        return 0.0 if logit < 0 else 1.0


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

    frame_result_count = 0
    final_result = None
    service_info = None
    response_count = 0
    start_time = time.time()

    # Stream per-frame rows straight to disk rather than retaining every
    # FrameResult: the CLI only needs a running count, so memory stays flat
    # regardless of how long the input video is. The CSV keeps the
    # index,probability format, deriving probability from each per-frame logit
    # using a sigmoid transform.
    csv_file = open(csv_output, "w") if csv_output else None
    if csv_file:
        csv_file.write("index,probability\n")

    try:
        for response in response_iter:
            response_count += 1

            if response.HasField("service_info"):
                service_info = response.service_info
            elif response.HasField("frame_results"):
                batch = response.frame_results.results
                frame_result_count += len(batch)
                if csv_file:
                    for fr in batch:
                        p = _logit_to_probability(fr.logit)
                        csv_file.write(f"{fr.frame_id},{p:.6f}\n")
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
        print(f"Frame results received: {frame_result_count}")
        print(f"Processing time: {fmt_elapsed(elapsed_total)}")

        if service_info is not None:
            print("\nService Info:")
            print(f"  NIM version   : {service_info.nim_version}")
            print(f"  Model version : {service_info.model_version}")
            print(f"  Request ID    : {service_info.request_id}")

        if final_result:
            print("\nFinal Statistics:")
            print(f"  Total frames processed: {final_result.total_frames}")
            print(f"  Final mean logit: {final_result.mean_logit:.6f}")
            print(f"  Final probability: {final_result.synthetic_probability:.6f}")

            # Determine if video is likely synthetic
            if final_result.synthetic_probability > CLASSIFICATION_THRESHOLD:
                verdict = "SYNTHETIC"
                confidence = final_result.synthetic_probability * 100
            else:
                verdict = "REAL"
                confidence = (1.0 - final_result.synthetic_probability) * 100

            print(f"\n{'*' * 60}")
            print(f"VERDICT: {verdict} (confidence: {confidence:.2f}%)")
            print(f"{'*' * 60}\n")

            if csv_output and frame_result_count > 0:
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
    finally:
        if csv_file:
            csv_file.close()


def process_request(
    channel: grpc.Channel,
    detector_config: SyntheticDetectorConfig,
) -> None:
    """Process gRPC request and handle responses.

    Args:
        channel: gRPC channel for communication with the Synthetic Video
            Detector service
        detector_config: Resolved client configuration selecting either the
            byte-streaming (video file) or pre-signed URL input mode and the
            optional CSV output path
    """
    try:
        stub = syntheticvideodetector_pb2_grpc.SyntheticVideoDetectorServiceStub(channel)
        start_time = time.time()

        responses = stub.DetectSyntheticVideo(
            generate_request_for_inference(detector_config),
        )

        write_output_file_from_response(
            response_iter=responses,
            csv_output=detector_config.csv_output,
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

    # Validate SSL arguments
    try:
        validate_ssl_args(args)
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

    # Print configuration and connection info
    print(detector_config)
    print(f"Server      : {args.target}")
    print(f"SSL mode    : {args.ssl_mode}")
    print("=" * 60 + "\n")

    # Run detection
    try:
        # Create channel based on SSL mode
        if args.ssl_mode != "DISABLED":
            channel_credentials = create_channel_credentials(args)
            print(f"Establishing secure channel to {args.target}")
            with grpc.secure_channel(args.target, channel_credentials) as channel:
                process_request(
                    channel=channel,
                    detector_config=detector_config,
                )
        else:
            print(f"Establishing insecure channel to {args.target}")
            with grpc.insecure_channel(args.target) as channel:
                process_request(
                    channel=channel,
                    detector_config=detector_config,
                )

        print("\nDetection completed successfully!")

    except grpc.RpcError as e:
        print(f"\nGRPC Error: {e.code()} - {e.details()}")
        if e.code() == grpc.StatusCode.UNIMPLEMENTED:
            print(
                "\nThe server did not recognize this request. This is the v2 client "
                "(API nvidia.ai4m.syntheticvideodetector.v1); the target server appears "
                "to be a v1 (nvidia.maxine) or NVCF deployment.\n"
                "Use the v1 client for a v1/NVCF server, or point --target at a v2 "
                "(self-hosted) Synthetic Video Detector deployment."
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
