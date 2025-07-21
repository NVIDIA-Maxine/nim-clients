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

# Standard library imports
import argparse
import json
import os
import pathlib
import sys
from dataclasses import dataclass

# Third-party imports
from google.protobuf import any_pb2, wrappers_pb2

# Setup paths for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))  # noqa: E402
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(os.path.join(SCRIPT_PATH, "../interfaces"))

# Local imports
from constants import (  # noqa: E402
    DEFAULT_BITRATE,
    DEFAULT_IDR_INTERVAL,
    DEFAULT_NON_STREAMABLE_VIDEO_PATH,
    DEFAULT_STREAMABLE_VIDEO_PATH,
    DEFAULT_TEMPORAL,
    DEFAULT_DETECT_CLOSURE,
    DEFAULT_EYE_SIZE_SENSITIVITY,
    DEFAULT_ENABLE_LOOKAWAY,
    DEFAULT_LOOKAWAY_MAX_OFFSET,
    DEFAULT_LOOKAWAY_INTERVAL_MIN,
    DEFAULT_LOOKAWAY_INTERVAL_RANGE,
    DEFAULT_GAZE_PITCH_THRESHOLD_LOW,
    DEFAULT_GAZE_PITCH_THRESHOLD_HIGH,
    DEFAULT_GAZE_YAW_THRESHOLD_LOW,
    DEFAULT_GAZE_YAW_THRESHOLD_HIGH,
    DEFAULT_HEAD_PITCH_THRESHOLD_LOW,
    DEFAULT_HEAD_PITCH_THRESHOLD_HIGH,
    DEFAULT_HEAD_YAW_THRESHOLD_LOW,
    DEFAULT_HEAD_YAW_THRESHOLD_HIGH,
    PARAM_RANGES,
)
from utils.utils import (  # noqa: E402
    check_streamable,
    is_file_available,
    add_ssl_arguments,
    add_preview_arguments,
)
import eyecontact_pb2  # noqa: E402


class SmartFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    """
    Custom formatter that combines raw description preservation and default
    value help text.
    """

    pass


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for Eye Contact.

    Returns:
        argparse.ArgumentParser: Configured argument parser with all Eye
            Contact options
    """
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Process mp4 video files using gRPC and apply eye-contact "
        "with comprehensive parameter control",
        formatter_class=lambda prog: SmartFormatter(prog, max_help_position=60),
    )

    # Add SSL and connection arguments from utils
    add_ssl_arguments(parser)

    # Add preview mode arguments from utils
    add_preview_arguments(parser)

    # Input/Output arguments
    parser.add_argument(
        "--input",
        type=str,
        default=DEFAULT_NON_STREAMABLE_VIDEO_PATH,
        help="The path to the input video file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output.mp4",
        help="The path for the output video file.",
    )

    # Streaming support
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Flag to enable grpc streaming mode. Required for streamable " "video input.",
    )

    # Video encoding arguments
    parser.add_argument(
        "--bitrate",
        type=int,
        default=DEFAULT_BITRATE,
        help=f"Output video bitrate in bps (default: {DEFAULT_BITRATE}). "
        f"This is only applicable when lossless mode is disabled.",
    )
    parser.add_argument(
        "--idr-interval",
        type=int,
        default=DEFAULT_IDR_INTERVAL,
        help=f"The interval for IDR frames in the output video. This is only "
        f"applicable when lossless mode is disabled. "
        f"(default: {DEFAULT_IDR_INTERVAL})",
    )
    parser.add_argument(
        "--lossless",
        action="store_true",
        help="Flag to enable lossless mode for video encoding.",
    )
    parser.add_argument(
        "--custom-encoding-params",
        type=str,
        default=None,
        help="Custom encoding parameters in JSON format.",
    )

    # Eye Contact specific parameters
    parser.add_argument(
        "--temporal",
        type=int,
        default=DEFAULT_TEMPORAL,
        help=f"Flag to control temporal filtering (default: {DEFAULT_TEMPORAL})",
    )
    parser.add_argument(
        "--detect-closure",
        type=int,
        default=DEFAULT_DETECT_CLOSURE,
        help=f"Flag to toggle detection of eye closure and occlusion on/off "
        f"(default: {DEFAULT_DETECT_CLOSURE})",
    )
    parser.add_argument(
        "--eye-size-sensitivity",
        type=int,
        default=DEFAULT_EYE_SIZE_SENSITIVITY,
        help=f"Eye size sensitivity parameter "
        f"(default: {DEFAULT_EYE_SIZE_SENSITIVITY}, range: [2, 6])",
    )
    parser.add_argument(
        "--enable-lookaway",
        type=int,
        default=DEFAULT_ENABLE_LOOKAWAY,
        choices=[0, 1],
        help=f"Flag to toggle look away on/off " f"(default: {DEFAULT_ENABLE_LOOKAWAY})",
    )
    parser.add_argument(
        "--lookaway-max-offset",
        type=int,
        default=DEFAULT_LOOKAWAY_MAX_OFFSET,
        help=f"Maximum value of gaze offset angle (degrees) during a random "
        f"look away (default: {DEFAULT_LOOKAWAY_MAX_OFFSET}, "
        f"range: [1, 10])",
    )
    parser.add_argument(
        "--lookaway-interval-min",
        type=int,
        default=DEFAULT_LOOKAWAY_INTERVAL_MIN,
        help=f"Minimum limit for the number of frames at which random look "
        f"away occurs (default: {DEFAULT_LOOKAWAY_INTERVAL_MIN}, "
        f"range: [1, 600])",
    )
    parser.add_argument(
        "--lookaway-interval-range",
        type=int,
        default=DEFAULT_LOOKAWAY_INTERVAL_RANGE,
        help=f"Range for picking the number of frames at which random look "
        f"away occurs (default: {DEFAULT_LOOKAWAY_INTERVAL_RANGE}, "
        f"range: [1, 600])",
    )
    parser.add_argument(
        "--gaze-pitch-threshold-low",
        type=float,
        default=DEFAULT_GAZE_PITCH_THRESHOLD_LOW,
        help=f"Gaze pitch threshold (degrees) at which the redirection starts "
        f"transitioning (default: {DEFAULT_GAZE_PITCH_THRESHOLD_LOW}, "
        f"range: [10, 35])",
    )
    parser.add_argument(
        "--gaze-pitch-threshold-high",
        type=float,
        default=DEFAULT_GAZE_PITCH_THRESHOLD_HIGH,
        help=f"Gaze pitch threshold (degrees) at which the redirection is "
        f"equal to estimated gaze "
        f"(default: {DEFAULT_GAZE_PITCH_THRESHOLD_HIGH}, "
        f"range: [10, 35])",
    )
    parser.add_argument(
        "--gaze-yaw-threshold-low",
        type=float,
        default=DEFAULT_GAZE_YAW_THRESHOLD_LOW,
        help=f"Gaze yaw threshold (degrees) at which the redirection starts "
        f"transitioning (default: {DEFAULT_GAZE_YAW_THRESHOLD_LOW}, "
        f"range: [10, 35])",
    )
    parser.add_argument(
        "--gaze-yaw-threshold-high",
        type=float,
        default=DEFAULT_GAZE_YAW_THRESHOLD_HIGH,
        help=f"Gaze yaw threshold (degrees) at which the redirection is equal "
        f"to estimated gaze (default: {DEFAULT_GAZE_YAW_THRESHOLD_HIGH}, "
        f"range: [10, 35])",
    )
    parser.add_argument(
        "--head-pitch-threshold-low",
        type=float,
        default=DEFAULT_HEAD_PITCH_THRESHOLD_LOW,
        help=f"Head pose pitch threshold (degrees) at which the redirection "
        f"starts transitioning away from camera towards estimated gaze "
        f"(default: {DEFAULT_HEAD_PITCH_THRESHOLD_LOW}, range: [10, 35])",
    )
    parser.add_argument(
        "--head-pitch-threshold-high",
        type=float,
        default=DEFAULT_HEAD_PITCH_THRESHOLD_HIGH,
        help=f"Head pose pitch threshold (degrees) at which the redirection "
        f"is equal to estimated gaze "
        f"(default: {DEFAULT_HEAD_PITCH_THRESHOLD_HIGH}, "
        f"range: [10, 35])",
    )
    parser.add_argument(
        "--head-yaw-threshold-low",
        type=float,
        default=DEFAULT_HEAD_YAW_THRESHOLD_LOW,
        help=f"Head pose yaw threshold (degrees) at which the redirection "
        f"starts transitioning (default: {DEFAULT_HEAD_YAW_THRESHOLD_LOW}, "
        f"range: [10, 35])",
    )
    parser.add_argument(
        "--head-yaw-threshold-high",
        type=float,
        default=DEFAULT_HEAD_YAW_THRESHOLD_HIGH,
        help=f"Head pose yaw threshold (degrees) at which the redirection is "
        f"equal to estimated gaze "
        f"(default: {DEFAULT_HEAD_YAW_THRESHOLD_HIGH}, range: [10, 35])",
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
class EyeContactConfig:
    """Configuration class for Eye Contact parameters.

    Attributes:
        video_filepath: Path to input video file
        output_filepath: Path for output video
        streaming: Whether to use streaming mode
        lossless: Whether to use lossless encoding
        bitrate: Output video bitrate
        idr_interval: IDR frame interval
        custom_encoding_params: Custom encoding parameters in JSON format
        temporal: Temporal filtering flag
        detect_closure: Eye closure detection flag
        eye_size_sensitivity: Eye size sensitivity parameter
        enable_lookaway: Look away feature flag
        lookaway_max_offset: Maximum gaze offset angle for look away
        lookaway_interval_min: Minimum frames for look away interval
        lookaway_interval_range: Range for look away interval
        gaze_pitch_threshold_low: Low threshold for gaze pitch
        gaze_pitch_threshold_high: High threshold for gaze pitch
        gaze_yaw_threshold_low: Low threshold for gaze yaw
        gaze_yaw_threshold_high: High threshold for gaze yaw
        head_pitch_threshold_low: Low threshold for head pitch
        head_pitch_threshold_high: High threshold for head pitch
        head_yaw_threshold_low: Low threshold for head yaw
        head_yaw_threshold_high: High threshold for head yaw
    """

    video_filepath: os.PathLike
    output_filepath: os.PathLike
    streaming: bool
    lossless: bool
    bitrate: int
    idr_interval: int
    custom_encoding_params: dict | None
    temporal: int
    detect_closure: int
    eye_size_sensitivity: int
    enable_lookaway: int
    lookaway_max_offset: int
    lookaway_interval_min: int
    lookaway_interval_range: int
    gaze_pitch_threshold_low: float
    gaze_pitch_threshold_high: float
    gaze_yaw_threshold_low: float
    gaze_yaw_threshold_high: float
    head_pitch_threshold_low: float
    head_pitch_threshold_high: float
    head_yaw_threshold_low: float
    head_yaw_threshold_high: float

    @classmethod
    def from_args(cls, args):
        """Create config from command line arguments."""
        # Parse custom encoding parameters if provided
        custom_params = None
        if hasattr(args, "custom_encoding_params") and args.custom_encoding_params:
            try:
                custom_params = json.loads(args.custom_encoding_params)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format for custom encoding parameters: {e}")

        return cls(
            video_filepath=args.input,
            output_filepath=args.output,
            streaming=args.streaming,
            lossless=args.lossless,
            bitrate=args.bitrate,
            idr_interval=args.idr_interval,
            custom_encoding_params=custom_params,
            temporal=args.temporal,
            detect_closure=args.detect_closure,
            eye_size_sensitivity=args.eye_size_sensitivity,
            enable_lookaway=args.enable_lookaway,
            lookaway_max_offset=args.lookaway_max_offset,
            lookaway_interval_min=args.lookaway_interval_min,
            lookaway_interval_range=args.lookaway_interval_range,
            gaze_pitch_threshold_low=args.gaze_pitch_threshold_low,
            gaze_pitch_threshold_high=args.gaze_pitch_threshold_high,
            gaze_yaw_threshold_low=args.gaze_yaw_threshold_low,
            gaze_yaw_threshold_high=args.gaze_yaw_threshold_high,
            head_pitch_threshold_low=args.head_pitch_threshold_low,
            head_pitch_threshold_high=args.head_pitch_threshold_high,
            head_yaw_threshold_low=args.head_yaw_threshold_low,
            head_yaw_threshold_high=args.head_yaw_threshold_high,
        )

    def __str__(self) -> str:
        """Return string representation of config."""
        output = (
            "=" * 60
            + "\n"
            + "Eye Contact Configuration\n"
            + "=" * 60
            + "\n"
            + f"Video input : {self.video_filepath}\n"
            + f"Temporal    : {self.temporal}\n"
            + f"Detect closure: {self.detect_closure}\n"
            + f"Eye size sensitivity: {self.eye_size_sensitivity}\n"
            + f"Enable lookaway: {self.enable_lookaway}\n"
            + f"Lookaway max offset: {self.lookaway_max_offset}\n"
            + f"Lookaway interval min: {self.lookaway_interval_min}\n"
            + f"Lookaway interval range: {self.lookaway_interval_range}\n"
            + f"Gaze pitch threshold low: {self.gaze_pitch_threshold_low}\n"
            + f"Gaze pitch threshold high: {self.gaze_pitch_threshold_high}\n"
            + f"Gaze yaw threshold low: {self.gaze_yaw_threshold_low}\n"
            + f"Gaze yaw threshold high: {self.gaze_yaw_threshold_high}\n"
            + f"Head pitch threshold low: {self.head_pitch_threshold_low}\n"
            + f"Head pitch threshold high: {self.head_pitch_threshold_high}\n"
            + f"Head yaw threshold low: {self.head_yaw_threshold_low}\n"
            + f"Head yaw threshold high: {self.head_yaw_threshold_high}\n"
        )
        if self.lossless:
            output += "Encoding    : Lossless\n"
        elif self.custom_encoding_params:
            output += f"Encoding    : Custom parameters: " f"{self.custom_encoding_params}\n"
        else:
            output += (
                f"Bitrate     : {self.bitrate:,} bps\n" + f"IDR interval: {self.idr_interval}\n"
            )
        output += (
            f"Output file : {self.output_filepath}\n"
            + f"Streaming   : {self.streaming}\n"
            + f"Lossless    : {self.lossless}\n"
            + "=" * 60
        )
        return output

    def validate_eyecontact_config(self) -> bool:
        """Validate the eye contact configuration.

        Checks that:
        - Input file exists and has correct format
        - Parameters are within valid ranges
        - Streaming mode requirements are met

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If file format is invalid or parameters are out of
                range
        """
        # Validate video file
        is_video_available = is_file_available(self.video_filepath, ["mp4"])
        if not is_video_available:
            raise RuntimeError("Only MP4 video format is supported")

        if self.streaming:
            # Check if file is streamable
            is_streamable = check_streamable(self.video_filepath)
            if not is_streamable:
                # If using the default non-streamable video, suggest the
                # streamable version
                if self.video_filepath == DEFAULT_NON_STREAMABLE_VIDEO_PATH:
                    raise RuntimeError(
                        f"Default video file is not streamable. For streaming "
                        f"mode, use: --input {DEFAULT_STREAMABLE_VIDEO_PATH}"
                    )
                else:
                    raise RuntimeError(
                        f"Video file '{self.video_filepath}' is not streamable. "
                        f"Please use a streamable MP4 file when using streaming "
                        f"mode. To make a video streamable, you can use: "
                        f"ffmpeg -i input.mp4 -movflags +faststart "
                        f"output_streamable.mp4"
                    )

        # Validate parameter ranges
        params_to_check = {
            "temporal": self.temporal,
            "detect_closure": self.detect_closure,
            "eye_size_sensitivity": self.eye_size_sensitivity,
            "enable_lookaway": self.enable_lookaway,
            "lookaway_max_offset": self.lookaway_max_offset,
            "lookaway_interval_min": self.lookaway_interval_min,
            "lookaway_interval_range": self.lookaway_interval_range,
            "gaze_pitch_threshold_low": self.gaze_pitch_threshold_low,
            "gaze_pitch_threshold_high": self.gaze_pitch_threshold_high,
            "gaze_yaw_threshold_low": self.gaze_yaw_threshold_low,
            "gaze_yaw_threshold_high": self.gaze_yaw_threshold_high,
            "head_pitch_threshold_low": self.head_pitch_threshold_low,
            "head_pitch_threshold_high": self.head_pitch_threshold_high,
            "head_yaw_threshold_low": self.head_yaw_threshold_low,
            "head_yaw_threshold_high": self.head_yaw_threshold_high,
        }

        for param_name, param_value in params_to_check.items():
            if param_name in PARAM_RANGES:
                min_val, max_val = PARAM_RANGES[param_name]
                if param_value < min_val or param_value > max_val:
                    raise RuntimeError(
                        f"Parameter {param_name} value {param_value} is out of "
                        f"range [{min_val}, {max_val}]"
                    )

        return True

    def get_config_params(self) -> dict:
        """Get configuration parameters as a dictionary for the gRPC request."""
        params = {
            "temporal": self.temporal,
            "detect_closure": self.detect_closure,
            "eye_size_sensitivity": self.eye_size_sensitivity,
            "enable_lookaway": self.enable_lookaway,
            "lookaway_max_offset": self.lookaway_max_offset,
            "lookaway_interval_min": self.lookaway_interval_min,
            "lookaway_interval_range": self.lookaway_interval_range,
            "gaze_pitch_threshold_low": self.gaze_pitch_threshold_low,
            "gaze_pitch_threshold_high": self.gaze_pitch_threshold_high,
            "gaze_yaw_threshold_low": self.gaze_yaw_threshold_low,
            "gaze_yaw_threshold_high": self.gaze_yaw_threshold_high,
            "head_pitch_threshold_low": self.head_pitch_threshold_low,
            "head_pitch_threshold_high": self.head_pitch_threshold_high,
            "head_yaw_threshold_low": self.head_yaw_threshold_low,
            "head_yaw_threshold_high": self.head_yaw_threshold_high,
        }

        # Add output video encoding configuration
        if self.lossless:
            params["output_video_encoding"] = eyecontact_pb2.OutputVideoEncoding(lossless=True)
        elif self.custom_encoding_params:
            # Use custom encoding parameters if provided
            custom_params_proto = eyecontact_pb2.CustomEncodingParams()
            for key, value in self.custom_encoding_params.items():
                any_value = any_pb2.Any()
                if isinstance(value, str):
                    wrapper = wrappers_pb2.StringValue(value=value)
                    any_value.Pack(wrapper)
                elif isinstance(value, int):
                    wrapper = wrappers_pb2.Int32Value(value=value)
                    any_value.Pack(wrapper)
                elif isinstance(value, float):
                    wrapper = wrappers_pb2.FloatValue(value=value)
                    any_value.Pack(wrapper)
                custom_params_proto.custom[key].CopyFrom(any_value)
            params["output_video_encoding"] = eyecontact_pb2.OutputVideoEncoding(
                custom_encoding=custom_params_proto
            )
        else:
            # Use default lossy encoding
            params["output_video_encoding"] = eyecontact_pb2.OutputVideoEncoding(
                lossy=eyecontact_pb2.LossyEncoding(
                    bitrate=self.bitrate, idr_interval=self.idr_interval
                )
            )

        return params
