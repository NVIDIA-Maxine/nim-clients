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

"""Constants for Active Speaker Detection NIM client."""

import os
import sys
import pathlib

# Importing gRPC compiler auto-generated active speaker detection library
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(os.path.join(SCRIPT_PATH, "../interfaces"))
from nvidia.ai4m.activespeakerdetection.v1 import activespeakerdetection_pb2  # noqa: E402
from nvidia.ai4m.audio.v1 import audio_pb2  # noqa: E402
from nvidia.ai4m.video.v1 import video_pb2  # noqa: E402

# Constants for data handling
DATA_CHUNK_SIZE = 64 * 1024  # bytes, send files in 64KB chunks
DIARIZATION_WORDS_BATCH_SIZE = 100  # Number of words to send per batch

# Default asset paths
DEFAULT_VIDEO_PATH = "../assets/sample_video_streamable.mp4"
DEFAULT_AUDIO_PATH = "../assets/sample_audio.wav"
DEFAULT_DIARIZATION_PATH = "../assets/sample_diarization.json"

# Audio codec configurations
AUDIO_ENCODING_CONFIGS = {
    "mp3": audio_pb2.AUDIO_CODEC_MP3,
    "wav": audio_pb2.AUDIO_CODEC_WAV,
    "opus": audio_pb2.AUDIO_CODEC_OPUS,
}

# Video codec configurations
VIDEO_CODEC_CONFIGS = {
    "h264": video_pb2.VIDEO_CODEC_H264,
}

# Voice-activity smoothing levels. Maps the CLI choice to the proto enum value.
# Omitting the option leaves the field unset (UNSPECIFIED), so the deployment
# default from NV_AI4M_ASD_VA_SMOOTHING is used.
VOICE_ACTIVITY_SMOOTHING_CONFIGS = {
    "off": activespeakerdetection_pb2.VOICE_ACTIVITY_SMOOTHING_OFF,
    "low": activespeakerdetection_pb2.VOICE_ACTIVITY_SMOOTHING_LOW,
    "high": activespeakerdetection_pb2.VOICE_ACTIVITY_SMOOTHING_HIGH,
}
