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

# Setup paths for local imports (align with other clients)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))  # noqa: E402
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(os.path.join(SCRIPT_PATH, "../../interfaces"))

# Local imports
from utils.utils import (  # noqa: E402
    add_ssl_arguments,
    add_preview_arguments,
    is_file_available,
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for Synthetic Video Detector.

    Returns:
        argparse.ArgumentParser: Configured argument parser with SSL and
            preview mode arguments. Script-specific arguments can be added
            by the caller.
    """
    parser = argparse.ArgumentParser(
        description="Detect AI-generated videos using NVIDIA Maxine Synthetic Video Detector NIM",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Add SSL and preview mode arguments from utils for consistency
    add_ssl_arguments(parser)
    add_preview_arguments(parser)

    # Script-specific arguments
    parser.add_argument(
        "--video-input",
        type=str,
        default="../../assets/fake_sample_video.mp4",
        help="Path to the input video file to analyze (supports MP4 only)",
    )
    parser.add_argument(
        "--save-csv",
        nargs="?",
        const=True,
        default=False,
        metavar="FILENAME",
        help="Save results to CSV. Optionally specify a custom filename, "
        "otherwise uses the input video's base name (e.g., video.csv)",
    )

    return parser


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments using the configured argument parser."""
    parser = create_argument_parser()
    return parser.parse_args()


@dataclass
class SyntheticDetectorConfig:
    """Configuration for Synthetic Video Detector."""

    video_filepath: os.PathLike
    csv_output: str  # None if not saving, otherwise the CSV filename

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "SyntheticDetectorConfig":
        """Create config from command line arguments.

        Handles --save-csv argument:
        - Not provided: csv_output = None (don't save)
        - Provided without value: csv_output = <video_name>.csv
        - Provided with value: csv_output = <custom_filename>
        """
        csv_output = None
        if args.save_csv:
            if args.save_csv is True:
                # --save-csv provided without custom filename, use video name
                video_name = os.path.splitext(os.path.basename(args.video_input))[0]
                csv_output = f"{video_name}.csv"
            else:
                # --save-csv provided with custom filename
                csv_output = args.save_csv
                # Ensure .csv extension
                if not csv_output.lower().endswith(".csv"):
                    csv_output = f"{csv_output}.csv"

        return cls(
            video_filepath=args.video_input,
            csv_output=csv_output,
        )

    @property
    def save_csv(self) -> bool:
        """Return True if CSV output is enabled."""
        return self.csv_output is not None

    def __str__(self) -> str:
        lines = [
            "=" * 60,
            "Synthetic Video Detector Configuration",
            "=" * 60,
            f"Video input : {self.video_filepath}",
        ]
        if self.csv_output:
            lines.append(f"CSV output  : {self.csv_output}")
        return "\n".join(lines)

    def validate_synthetic_config(self) -> bool:
        """Validate the synthetic detector configuration."""
        # Validate video file exists and has correct format
        is_video_available = is_file_available(self.video_filepath, ["mp4"])
        if not is_video_available:
            raise RuntimeError("Video file must be MP4 format")
        return True
