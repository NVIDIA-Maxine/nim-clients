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

# Argument parsing utilities for the Synthetic Video Detector client

import argparse
import os
import pathlib
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlsplit

# Setup paths for local imports (align with other clients)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))  # noqa: E402
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(os.path.join(SCRIPT_PATH, "../../interfaces"))

# Local imports
from utils.utils import (  # noqa: E402
    add_presigned_arguments,
    add_ssl_arguments,
    is_file_available,
    redact_url,
)

# Default input video used when neither --video-input nor --presigned-url is
# provided
DEFAULT_VIDEO_INPUT = "../../assets/fake_sample_video.mp4"

# Container extensions the NIM can decode (MP4/QuickTime, Matroska, WebM).
# This is only a fast client-side sanity check on the filename -- the NIM
# identifies the actual container from the file header and rejects anything
# its NVDEC decoder cannot handle, so this list stays deliberately permissive.
SUPPORTED_VIDEO_EXTENSIONS = ["mp4", "mov", "m4v", "mkv", "webm"]


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for Synthetic Video Detector.

    Returns:
        argparse.ArgumentParser: Configured argument parser with SSL
            arguments. Script-specific arguments can be added by the caller.
    """
    parser = argparse.ArgumentParser(
        description="Detect AI-generated videos using NVIDIA Maxine Synthetic Video Detector NIM",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Add SSL arguments from utils for consistency
    add_ssl_arguments(parser)

    # Script-specific arguments
    parser.add_argument(
        "--video-input",
        type=str,
        default=None,
        help="Path to the input video file to analyze (supports MP4/MOV/M4V, MKV, and WebM). "
        f"Defaults to {DEFAULT_VIDEO_INPUT} when neither --video-input nor "
        "--presigned-url is provided. Mutually exclusive with --presigned-url.",
    )
    parser.add_argument(
        "--save-csv",
        nargs="?",
        const=True,
        default=False,
        metavar="FILENAME",
        help="Save results to CSV. Optionally specify a custom filename, "
        "otherwise uses the input video's (or URL's) base name (e.g., "
        "video.csv)",
    )

    # Pre-signed URL (S3 ingest) arguments (shared group, mirrors SSL args).
    add_presigned_arguments(parser)

    return parser


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments using the configured argument parser."""
    parser = create_argument_parser()
    return parser.parse_args()


@dataclass
class PresignedUrlConfig:
    """Configuration for the pre-signed URL (S3 ingest) request."""

    url: str
    url_provider: str = "unspecified"
    checksum_type: str = "sha256"
    checksum: Optional[str] = None
    no_verify_checksum: bool = False
    expected_size: Optional[int] = None
    content_type: Optional[str] = None
    expires_at_unix_ms: Optional[int] = None


@dataclass
class SyntheticDetectorConfig:
    """Configuration for Synthetic Video Detector."""

    video_filepath: Optional[os.PathLike]
    csv_output: Optional[str]  # None if not saving, otherwise the CSV filename
    presigned: Optional[PresignedUrlConfig] = None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "SyntheticDetectorConfig":
        """Create config from command line arguments.

        Selects the input mode:
        - --presigned-url provided: pre-signed URL (S3 ingest) mode
        - otherwise: byte-streaming mode using --video-input (falling back to
          the default sample video when --video-input is not provided)

        Handles --save-csv argument:
        - Not provided: csv_output = None (don't save)
        - Provided without value: csv_output = <video_or_url_name>.csv
        - Provided with value: csv_output = <custom_filename>

        Raises:
            RuntimeError: If both --video-input and --presigned-url are provided.
        """
        url = getattr(args, "presigned_url", None)
        if url and args.video_input:
            raise RuntimeError(
                "--video-input and --presigned-url are mutually exclusive; "
                "provide only one input mode."
            )

        presigned = None
        if url:
            presigned = PresignedUrlConfig(
                url=url,
                url_provider=args.presigned_url_provider,
                checksum_type=args.presigned_checksum_type,
                checksum=args.presigned_checksum,
                no_verify_checksum=args.presigned_no_verify_checksum,
                expected_size=args.presigned_expected_size,
                content_type=args.presigned_content_type,
                expires_at_unix_ms=args.presigned_expires_at_unix_ms,
            )

        video_filepath = args.video_input
        if presigned is None and not video_filepath:
            video_filepath = DEFAULT_VIDEO_INPUT

        csv_output = None
        if args.save_csv:
            if args.save_csv is True:
                # --save-csv provided without custom filename, derive a name
                csv_output = f"{cls._default_csv_basename(presigned, video_filepath)}.csv"
            else:
                # --save-csv provided with custom filename
                csv_output = args.save_csv
                # Ensure .csv extension
                if not csv_output.lower().endswith(".csv"):
                    csv_output = f"{csv_output}.csv"

        return cls(
            video_filepath=video_filepath,
            csv_output=csv_output,
            presigned=presigned,
        )

    @staticmethod
    def _default_csv_basename(
        presigned: Optional[PresignedUrlConfig], video_filepath: Optional[str]
    ) -> str:
        """Derive the default CSV base name from the URL or video path."""
        if presigned is not None:
            name = os.path.basename(urlsplit(presigned.url).path)
            stem = os.path.splitext(name)[0]
            return stem or "detection_results"
        return os.path.splitext(os.path.basename(video_filepath))[0]

    @property
    def use_presigned(self) -> bool:
        """Return True if the pre-signed URL (S3 ingest) mode is selected."""
        return self.presigned is not None

    @property
    def save_csv(self) -> bool:
        """Return True if CSV output is enabled."""
        return self.csv_output is not None

    def __str__(self) -> str:
        lines = [
            "=" * 60,
            "Synthetic Video Detector Configuration",
            "=" * 60,
        ]
        if self.use_presigned:
            lines.append(f"URL input   : {redact_url(self.presigned.url)}")
            lines.append(f"URL provider: {self.presigned.url_provider}")
            if self.presigned.no_verify_checksum:
                lines.append("Checksum    : verification disabled")
            elif self.presigned.checksum:
                lines.append(
                    f"Checksum    : {self.presigned.checksum_type}={self.presigned.checksum}"
                )
        else:
            lines.append(f"Video input : {self.video_filepath}")
        if self.csv_output:
            lines.append(f"CSV output  : {self.csv_output}")
        return "\n".join(lines)

    def validate_synthetic_config(self) -> bool:
        """Validate the client configuration.

        Pre-signed URL requests are validated entirely by the NIM (HTTPS, host
        allowlist, expiry, SSRF, checksum, size, content-type, etc.), so the
        client performs no pre-signed validation and stays lean. For the local
        byte-streaming path this only checks that the file exists and carries a
        supported container extension; the NIM identifies the real container
        from the file header and rejects anything it cannot decode.
        """
        if self.use_presigned:
            return True
        is_video_available = is_file_available(self.video_filepath, SUPPORTED_VIDEO_EXTENSIONS)
        if not is_video_available:
            raise RuntimeError(
                "Video file must be one of: "
                + ", ".join(f".{ext}" for ext in SUPPORTED_VIDEO_EXTENSIONS)
            )
        return True
