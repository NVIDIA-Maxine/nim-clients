#
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
#
"""Configuration and argument parsing for Active Speaker Detection NIM client."""

import argparse
import os
import sys
from dataclasses import dataclass

from constants import (
    AUDIO_ENCODING_CONFIGS,
    DEFAULT_AUDIO_PATH,
    DEFAULT_DIARIZATION_PATH,
    DEFAULT_VIDEO_PATH,
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from utils.utils import (  # noqa: E402
    add_preview_arguments,
    add_ssl_arguments,
    is_file_available,
)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for Active Speaker Detection.

    Returns:
        argparse.ArgumentParser: Configured argument parser with all options
    """
    parser = argparse.ArgumentParser(
        description=(
            "Run Active Speaker Detection inference with video," " audio, and diarization files"
        ),
    )

    add_ssl_arguments(parser)
    add_preview_arguments(parser)

    parser.add_argument(
        "--video-input",
        type=str,
        default=None,
        help="The path to the input video file (MP4 format). "
        f"If omitted, the bundled sample video ({DEFAULT_VIDEO_PATH}) is used.",
    )
    parser.add_argument(
        "--audio-input",
        type=str,
        default=None,
        help="The path to the input audio file (WAV/MP3 format). "
        "Only defaults to the bundled sample audio when the sample video is "
        "also used; it is required when a custom --video-input is provided "
        "(unless --skip-audio is set).",
    )
    parser.add_argument(
        "--diarization-input",
        type=str,
        default=None,
        help="The path to the diarization file (JSON format with word-level speaker info). "
        "Only defaults to the bundled sample diarization when the sample video "
        "is also used; it is required when a custom --video-input is provided. "
        "The sample diarization only matches the sample video.",
    )
    parser.add_argument(
        "--skip-audio",
        action="store_true",
        help="Skip sending separate audio data. "
        "Audio will be extracted from embedded video stream.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="speaker_detection_output.mp4",
        help="The path for the output video file with speaker bounding boxes.",
    )
    parser.add_argument(
        "--client-session-id",
        type=str,
        default=None,
        help="Client-assigned session identifier sent as gRPC metadata "
        "(key 'client-session-id'). The server echoes it back in ServiceInfo and "
        "uses it to correlate client and server logs. If omitted, none is sent.",
    )
    parser.add_argument(
        "--voice-activity-smoothing",
        type=str,
        default=None,
        choices=["off", "low", "high"],
        help="Voice-activity smoothing level applied to speaking decisions. "
        "If omitted, the deployment default (NV_AI4M_ASD_VA_SMOOTHING) is used.",
    )
    parser.add_argument(
        "--speaker-detection-threshold",
        type=float,
        default=None,
        help="Minimum confidence score in the open interval (0, 1) required to "
        "classify a detected face as actively speaking. If omitted, the server's "
        "configured default is used. A value <= 0 also falls back to the default; "
        "values outside (0, 1) are rejected by the server with INVALID_ARGUMENT.",
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
class ActiveSpeakerDetectionConfig:
    """Configuration class for Active Speaker Detection parameters."""

    video_filepath: os.PathLike
    audio_filepath: os.PathLike
    diarization_filepath: os.PathLike
    output_filepath: os.PathLike
    skip_audio: bool = False
    embedded_audio_codec: str = "opus"
    input_audio_format: str | None = None
    input_video_format: str | None = None
    voice_activity_smoothing: str | None = None
    speaker_detection_threshold: float | None = None

    @classmethod
    def from_args(cls, args):
        """Create config from command line arguments.

        The bundled sample assets (video, audio, diarization) form a matched
        set: the sample diarization/audio are only meaningful with the sample
        video. An explicitly passed path is always honored; the sample
        diarization/audio are used only when the sample video is also used.
        With a custom --video-input, the matching --diarization-input (and
        --audio-input unless --skip-audio) must be provided explicitly, or a
        ValueError is raised instead of silently substituting sample assets.
        """
        using_sample_video = args.video_input is None
        video_filepath = DEFAULT_VIDEO_PATH if using_sample_video else args.video_input

        # Diarization: honor an explicit path; fall back to the sample only
        # with the sample video; otherwise refuse rather than mismatch.
        if args.diarization_input is not None:
            diarization_filepath = args.diarization_input
        elif using_sample_video:
            diarization_filepath = DEFAULT_DIARIZATION_PATH
        else:
            raise ValueError(
                "--diarization-input is required with a custom --video-input. "
                "The bundled sample diarization only matches the sample video."
            )

        # Audio: same rule (irrelevant when --skip-audio uses embedded audio).
        if args.skip_audio:
            audio_filepath = None
        elif args.audio_input is not None:
            audio_filepath = args.audio_input
        elif using_sample_video:
            audio_filepath = DEFAULT_AUDIO_PATH
        else:
            raise ValueError(
                "--audio-input is required with a custom --video-input "
                "(or pass --skip-audio to use the video's embedded audio). "
                "The bundled sample audio only matches the sample video."
            )

        return cls(
            video_filepath=video_filepath,
            audio_filepath=audio_filepath,
            diarization_filepath=diarization_filepath,
            output_filepath=args.output,
            skip_audio=args.skip_audio,
            voice_activity_smoothing=args.voice_activity_smoothing,
            speaker_detection_threshold=args.speaker_detection_threshold,
        )

    def __str__(self) -> str:
        """Return string representation of config."""
        sep = "=" * 60
        audio_display = (
            "(skipped - using embedded)" if self.skip_audio else str(self.audio_filepath)
        )
        diarization_display = str(self.diarization_filepath)
        lines = [
            sep,
            "Active Speaker Detection Configuration",
            sep,
            f"Video input       : {self.video_filepath}",
            f"Audio input       : {audio_display}",
            f"Diarization input : {diarization_display}",
            f"Output file       : {self.output_filepath}",
            f"Skip audio        : {self.skip_audio}",
            f"VA smoothing      : {self.voice_activity_smoothing or '(deployment default)'}",
            f"Speaker threshold : "
            f"{self.speaker_detection_threshold if self.speaker_detection_threshold is not None else '(deployment default)'}",
            sep,
        ]
        return "\n".join(lines)

    def validate_config(self) -> bool:
        """Validate the active speaker detection configuration.

        Raises:
            FileNotFoundError: If input files don't exist.
            RuntimeError: If file formats are invalid.
        """
        # Validate video file
        is_file_available(self.video_filepath, ["mp4"])
        self.input_video_format = "h264"

        # Validate diarization file
        is_file_available(self.diarization_filepath, ["json"])

        # Validate audio file
        if not self.skip_audio:
            is_file_available(self.audio_filepath, ["wav", "mp3"])
            audio_ext = os.path.splitext(self.audio_filepath)[1].lower().lstrip(".")
            if audio_ext not in AUDIO_ENCODING_CONFIGS:
                raise RuntimeError(
                    f"Unsupported audio format: {audio_ext}. "
                    f"Supported formats: {list(AUDIO_ENCODING_CONFIGS.keys())}"
                )
            self.input_audio_format = audio_ext
        else:
            self.input_audio_format = None
        return True
