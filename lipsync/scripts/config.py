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

from dataclasses import dataclass
import argparse
import os
from constants import (
    DEFAULT_AUDIO_PATH,
    DEFAULT_BITRATE,
    DEFAULT_IDR_INTERVAL,
    DEFAULT_NON_STREAMABLE_VIDEO_PATH,
    EXTEND_AUDIO_CONFIGS,
    EXTEND_VIDEO_CONFIGS,
    INPUT_AUDIO_CODECS,
    OUTPUT_AUDIO_CODECS,
)

import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from utils.utils import is_file_available, add_ssl_arguments  # noqa: E402


class SmartFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    """
    Custom formatter that combines raw description preservation and default
    value help text.
    """

    pass


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for LipSync.

    Returns:
        argparse.ArgumentParser: Configured argument parser with all LipSync options
    """
    parser = argparse.ArgumentParser(
        description="Run LipSync inference with input video and audio files",
        formatter_class=lambda prog: SmartFormatter(prog, max_help_position=60),
    )
    add_ssl_arguments(parser)

    parser.add_argument(
        "--video-input",
        type=str,
        default=DEFAULT_NON_STREAMABLE_VIDEO_PATH,
        help="The path to the input video file.",
    )
    parser.add_argument(
        "--audio-input",
        type=str,
        default=DEFAULT_AUDIO_PATH,
        help="The path to the input audio file.",
    )
    parser.add_argument(
        "--speaker-data-input",
        type=str,
        default=None,
        help="Path to JSON file containing speaker data (bounding boxes, speaker_id, is_speaking).",
    )
    parser.add_argument(
        "--extend-audio",
        choices=list(EXTEND_AUDIO_CONFIGS.keys()),
        default="unspecified",
        help="How to handle audio extension (default: unspecified)",
    )
    parser.add_argument(
        "--extend-video",
        choices=list(EXTEND_VIDEO_CONFIGS.keys()),
        default="unspecified",
        help="How to handle video extension (default: unspecified)",
    )
    parser.add_argument(
        "--bitrate",
        type=int,
        default=DEFAULT_BITRATE,
        help=f"Output video bitrate in Mbps (default: {DEFAULT_BITRATE}). This is applicable only "
        "when lossless mode is disabled.",
    )
    parser.add_argument(
        "--idr-interval",
        type=int,
        default=DEFAULT_IDR_INTERVAL,
        help=f"The interval for IDR frames in the output video. This is applicable only when "
        f"lossless mode is disabled. (default: {DEFAULT_IDR_INTERVAL})",
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
    parser.add_argument(
        "--output",
        type=str,
        default="lipsync_output.mp4",
        help="The path for the output video file.",
    )
    parser.add_argument(
        "--output-audio-codec",
        type=str,
        default="opus",
        help="Audio codec for output video file (opus or mp3).",
    )
    parser.add_argument(
        "--head-movement-speed",
        type=int,
        default=None,
        help="Speed of head movement in input video. 0 for static or slow-moving head, "
        "1 for fast-moving head.",
    )
    parser.add_argument(
        "--mix-background-audio",
        action="store_true",
        help="Mix background audio with the output audio.",
    )
    parser.add_argument(
        "--background-audio-input",
        type=str,
        default=None,
        help="Path to background audio file (wav or mp3).",
    )
    parser.add_argument(
        "--background-audio-volume",
        type=float,
        default=0.5,
        help="Volume of the background audio (0.0 to 1.0). Default: 0.5.",
    )
    parser.add_argument(
        "--client-session-id",
        type=str,
        default=None,
        help="Client-assigned session identifier, sent as gRPC metadata and echoed back in the "
        "ServiceInfo banner so this run can be correlated with the server logs. A random UUID "
        "is generated when omitted; pass an empty string to send no session id.",
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
class LipSyncConfig:
    """Configuration class for LipSync parameters."""

    audio_filepath: os.PathLike
    video_filepath: os.PathLike
    speaker_data_filepath: os.PathLike | None
    output_filepath: os.PathLike
    extend_audio: str
    extend_video: str
    bitrate: int
    idr_interval: int
    lossless: bool
    input_audio_codec: str | None
    is_speaker_info_provided: bool
    custom_encoding_params: dict | None
    output_audio_codec: str
    head_movement_speed: int | None
    mix_background_audio: bool
    background_audio_filepath: os.PathLike | None
    background_audio_volume: float

    @classmethod
    def from_args(cls, args):
        """Create config from command-line arguments."""
        custom_params = None
        if hasattr(args, "custom_encoding_params") and args.custom_encoding_params:
            try:
                custom_params = json.loads(args.custom_encoding_params)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format for custom encoding parameters: {e}")

        return cls(
            audio_filepath=args.audio_input,
            video_filepath=args.video_input,
            speaker_data_filepath=args.speaker_data_input,
            output_filepath=args.output,
            extend_audio=args.extend_audio,
            extend_video=args.extend_video,
            bitrate=args.bitrate,
            idr_interval=args.idr_interval,
            lossless=args.lossless,
            input_audio_codec=None,
            is_speaker_info_provided=args.speaker_data_input is not None,
            custom_encoding_params=custom_params,
            output_audio_codec=args.output_audio_codec,
            head_movement_speed=args.head_movement_speed,
            mix_background_audio=args.mix_background_audio,
            background_audio_filepath=args.background_audio_input,
            background_audio_volume=args.background_audio_volume,
        )

    def __str__(self) -> str:
        """Return string representation of config."""
        output = (
            "=" * 60
            + "\n"
            + "LipSync Configuration\n"
            + "=" * 60
            + "\n"
            + f"Video input : {self.video_filepath}\n"
            + f"Audio input : {self.audio_filepath}\n"
            + f"Speaker JSON: {self.speaker_data_filepath}\n"
            + f"Input audio codec: {self.input_audio_codec}\n"
            + f"Extend audio: {self.extend_audio}\n"
            + f"Extend video: {self.extend_video}\n"
        )
        if self.lossless:
            output += "Encoding    : Lossless\n"
        elif self.custom_encoding_params:
            output += f"Encoding    : Custom parameters: {self.custom_encoding_params}\n"
        else:
            output += (
                f"Bitrate     : {self.bitrate} Mbps\n" + f"IDR interval: {self.idr_interval}\n"
            )
        output += (
            f"Output file : {self.output_filepath}\n"
            + f"Lossless    : {self.lossless}\n"
            + f"Output audio codec: {self.output_audio_codec}\n"
            + f"Head movement speed: {self.head_movement_speed}\n"
            + f"Mix background audio: {self.mix_background_audio}\n"
            + f"Background audio file: {self.background_audio_filepath}\n"
            + f"Background audio volume: {self.background_audio_volume}\n"
            + "=" * 60
        )
        return output

    def validate_lipsync_config(self) -> bool:
        """Validate the lipsync configuration.

        Raises:
            FileNotFoundError: If input files don't exist
            RuntimeError: If file formats are invalid
        """
        # Validate video file
        is_video_available = is_file_available(self.video_filepath, ["mp4"])
        if not is_video_available:
            raise RuntimeError("Only MP4 video format is supported")

        # Validate audio file
        is_audio_available = is_file_available(self.audio_filepath, list(INPUT_AUDIO_CODECS))
        if not is_audio_available:
            raise RuntimeError("Only WAV and MP3 audio formats are supported for input")
        self.input_audio_codec = os.path.splitext(self.audio_filepath)[1].lower().lstrip(".")

        # Validate speaker data JSON file if provided
        if self.speaker_data_filepath:
            is_json_available = is_file_available(self.speaker_data_filepath, ["json"])
            if not is_json_available:
                raise RuntimeError("Only JSON format is supported for speaker data file")
            self._validate_speaker_data_file()
            self.is_speaker_info_provided = True
        else:
            self.is_speaker_info_provided = False

        if self.head_movement_speed is not None and self.head_movement_speed not in (0, 1):
            raise RuntimeError(
                "head_movement_speed must be 0 (static/slow-moving head) or 1 (fast-moving head)"
            )

        if self.output_audio_codec not in OUTPUT_AUDIO_CODECS:
            raise RuntimeError("Only Opus and MP3 audio codecs are supported for output")

        # Bitrate and IDR interval only reach the encoder on the lossy path, so they
        # are checked only when they will actually be sent.
        if not self.lossless and not self.custom_encoding_params:
            if self.bitrate <= 0:
                raise RuntimeError("bitrate must be a positive integer (Mbps)")
            if self.idr_interval <= 0:
                raise RuntimeError("idr_interval must be a positive integer (frames)")

        # The volume is validated whether or not mixing is enabled, so a bad value is
        # reported even when the user forgot --mix-background-audio.
        if not 0.0 <= self.background_audio_volume <= 1.0:
            raise RuntimeError("background_audio_volume must be between 0.0 and 1.0")

        # Validate background audio if mixing is enabled
        if self.mix_background_audio:
            if not self.background_audio_filepath:
                raise RuntimeError(
                    "Background audio file path is required when --mix-background-audio is set"
                )
            is_bg_audio_available = is_file_available(
                self.background_audio_filepath, list(INPUT_AUDIO_CODECS)
            )
            if not is_bg_audio_available:
                raise RuntimeError(
                    "Only WAV and MP3 audio formats are supported for background audio"
                )
        return True

    def _validate_speaker_data_file(self) -> None:
        """Parse and schema-check the speaker data file before the request opens.

        The request generator reads this file lazily while streaming, so without this
        check a syntax or schema error surfaces as an opaque gRPC UNKNOWN status mid
        request instead of an actionable message.

        Raises:
            RuntimeError: If the file is not valid JSON or does not match the schema.
        """
        path = self.speaker_data_filepath
        try:
            with open(path, "r") as fd:
                data = json.load(fd)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in speaker data file {path}: {e}") from e
        except OSError as e:
            raise RuntimeError(f"Could not read speaker data file {path}: {e}") from e

        if not isinstance(data, dict):
            raise RuntimeError(
                f"Speaker data file {path} must contain a JSON object with a 'frames' key"
            )

        frames = data.get("frames")
        if frames is None:
            raise RuntimeError(f"Speaker data file {path} is missing the 'frames' key")
        if not isinstance(frames, list):
            raise RuntimeError(f"'frames' in speaker data file {path} must be an array")

        for i, frame in enumerate(frames):
            where = f"frames[{i}]"
            if not isinstance(frame, dict):
                raise RuntimeError(f"{where} in {path} must be an object")

            if "bypass" in frame and not isinstance(frame["bypass"], bool):
                raise RuntimeError(f"{where}.bypass in {path} must be true or false")

            speakers = frame.get("speakers", [])
            if not isinstance(speakers, list):
                raise RuntimeError(f"{where}.speakers in {path} must be an array")

            for j, speaker in enumerate(speakers):
                sw = f"{where}.speakers[{j}]"
                if not isinstance(speaker, dict):
                    raise RuntimeError(f"{sw} in {path} must be an object")

                bbox = speaker.get("bbox")
                if bbox is None:
                    raise RuntimeError(f"{sw} in {path} is missing 'bbox'")
                if not isinstance(bbox, list) or len(bbox) != 4:
                    raise RuntimeError(
                        f"{sw}.bbox in {path} must be an array of 4 numbers "
                        f"[x, y, width, height]"
                    )
                for k, v in enumerate(bbox):
                    if isinstance(v, bool) or not isinstance(v, (int, float)):
                        raise RuntimeError(f"{sw}.bbox[{k}] in {path} must be a number")

                speaker_id = speaker.get("speaker_id")
                if speaker_id is not None and (
                    isinstance(speaker_id, bool) or not isinstance(speaker_id, int)
                ):
                    raise RuntimeError(f"{sw}.speaker_id in {path} must be an integer")

                is_speaking = speaker.get("is_speaking")
                if is_speaking is not None and not isinstance(is_speaking, bool):
                    raise RuntimeError(f"{sw}.is_speaking in {path} must be true or false")
