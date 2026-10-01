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

"""Configuration and argument parsing for the 3D Body Pose NIM client."""

import argparse
import os
import sys
from dataclasses import dataclass

from constants import (
    DEFAULT_BBOX_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TIMEOUT,
    DEFAULT_VIDEO_PATH,
    DRAW_KEYPOINTS_CONFIGS,
    VIDEO_FILE_TYPES,
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from utils.utils import (  # noqa: E402
    add_preview_arguments,
    add_ssl_arguments,
    is_file_available,
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for 3D Body Pose.

    Returns:
        argparse.ArgumentParser: Configured argument parser with all 3D Body Pose options
    """
    parser = argparse.ArgumentParser(
        description="Run 3D Body Pose inference with an input video and tracked bounding boxes",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    add_ssl_arguments(parser)
    add_preview_arguments(parser)

    parser.add_argument(
        "--video-input",
        type=str,
        default=DEFAULT_VIDEO_PATH,
        help="The path to the input video file (MP4, WebM or MKV).",
    )
    parser.add_argument(
        "--bbox-input",
        type=str,
        default=DEFAULT_BBOX_PATH,
        help="The path to the tracked bounding-box annotation file (TXT). Line 1 is the "
        "number of tracked bodies; each following line is 'frame_id tracking_id x y w h'.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help="The path for the output pose file (JSON Lines, one frame per line).",
    )
    parser.add_argument(
        "--overlay-output",
        type=str,
        default=None,
        help="If set, also render the skeleton overlay onto the input video and write it "
        "to this path (MP4).",
    )
    parser.add_argument(
        "--draw-keypoints",
        choices=list(DRAW_KEYPOINTS_CONFIGS.keys()),
        default="both",
        help="Keypoints drawn by --overlay-output: 2D keypoints (green), 3D keypoints "
        "reprojected to the image (red), or both.",
    )
    parser.add_argument(
        "--focal-length",
        type=float,
        default=0.0,
        help="Pinhole focal length in pixels. 0 requests the default derived from the "
        "image size.",
    )
    parser.add_argument(
        "--enable-contact",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Request static-camera contact correction. This setting is fixed when the "
        "server starts (BODY_POSE_ENABLE_CONTACT); requesting the other value is served "
        "with the server's value and prints a warning. Omit to accept the server's value.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="RPC deadline in seconds. 0 disables the deadline. Raise it for long videos "
        "or many tracked bodies.",
    )
    parser.add_argument(
        "--client-session-id",
        type=str,
        default=None,
        help="Session identifier of your own (printable ASCII), echoed by the server in the "
        "service info it prints before the poses.",
    )
    return parser


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments using the configured argument parser.

    Returns:
        Namespace containing all parsed arguments
    """
    parser = create_argument_parser()
    return parser.parse_args()


@dataclass
class BodyPoseClientConfig:
    """Configuration class for 3D Body Pose parameters."""

    video_filepath: os.PathLike
    bbox_filepath: os.PathLike
    output_filepath: os.PathLike
    overlay_filepath: os.PathLike | None
    draw_keypoints: str
    focal_length: float
    enable_contact: bool | None
    timeout: float
    client_session_id: str | None

    @classmethod
    def from_args(cls, args):
        """Create config from command-line arguments."""
        return cls(
            video_filepath=args.video_input,
            bbox_filepath=args.bbox_input,
            output_filepath=args.output,
            overlay_filepath=args.overlay_output,
            draw_keypoints=args.draw_keypoints,
            focal_length=args.focal_length,
            enable_contact=args.enable_contact,
            timeout=args.timeout,
            client_session_id=args.client_session_id,
        )

    def __str__(self) -> str:
        """Return string representation of config."""
        sep = "=" * 60
        contact = "server default" if self.enable_contact is None else self.enable_contact
        lines = [
            sep,
            "3D Body Pose Configuration",
            sep,
            f"Video input      : {self.video_filepath}",
            f"BBox input       : {self.bbox_filepath}",
            f"Output file      : {self.output_filepath}",
            f"Overlay file     : {self.overlay_filepath}",
            f"Draw keypoints   : {self.draw_keypoints}",
            f"Focal length     : {self.focal_length}",
            f"Enable contact   : {contact}",
            f"Timeout          : {self.timeout}s",
            f"Client session ID: {self.client_session_id}",
            sep,
        ]
        return "\n".join(lines)

    def validate_config(self) -> bool:
        """Validate the 3D Body Pose configuration.

        Raises:
            FileNotFoundError: If input files don't exist
            RuntimeError: If file formats or values are invalid
        """
        if not is_file_available(self.video_filepath, VIDEO_FILE_TYPES):
            raise RuntimeError("Only MP4, WebM and MKV video files are supported")
        if not is_file_available(self.bbox_filepath, ["txt"]):
            raise RuntimeError("Only TXT format is supported for the bounding-box file")
        if os.path.splitext(self.output_filepath)[1].lower() != ".json":
            raise RuntimeError("Output pose file must have a .json extension")
        if self.overlay_filepath and not self.overlay_filepath.lower().endswith(".mp4"):
            raise RuntimeError("Overlay output file must have a .mp4 extension")

        # The overlay writer opens its file before the input video is read, so
        # the same path would truncate the input.
        if self.overlay_filepath and os.path.realpath(self.overlay_filepath) == os.path.realpath(
            self.video_filepath
        ):
            raise RuntimeError("Overlay output file must differ from the input video")

        # gRPC accepts only printable ASCII metadata values and would otherwise
        # reject the call only once it is placed.
        sid = self.client_session_id
        if sid and not (sid.isascii() and sid.isprintable()):
            raise RuntimeError("--client-session-id must be printable ASCII")
        return True
