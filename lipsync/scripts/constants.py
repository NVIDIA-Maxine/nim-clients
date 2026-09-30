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

import os
import sys
import pathlib

# Importing gRPC compiler auto-generated maxine lipsync library
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.insert(0, os.path.join(SCRIPT_PATH, "../interfaces"))
import nvidia.ai4m.lipsync.v1.lipsync_pb2 as lipsync_pb2  # noqa: E402
import nvidia.ai4m.audio.v1.audio_pb2 as audio_pb2  # noqa: E402

# Constants for data handling
DATA_CHUNK_SIZE = 64 * 1024  # bytes, we send the mp4 file in 64KB chunks
SPEAKER_DATA_BATCH_SIZE = 2048  # Number of speaker data entries to send in each batch
DEFAULT_BITRATE = 30  # Mbps
DEFAULT_IDR_INTERVAL = 8  # frames
DEFAULT_STREAMABLE_VIDEO_PATH = "../assets/sample_video_streamable.mp4"
DEFAULT_NON_STREAMABLE_VIDEO_PATH = "../assets/sample_video.mp4"
DEFAULT_AUDIO_PATH = "../assets/sample_audio_20s.wav"


# Configuration mappings for different options
EXTEND_AUDIO_CONFIGS = {
    "unspecified": lipsync_pb2.ExtendAudio.EXTEND_AUDIO_UNSPECIFIED,
    "silence": lipsync_pb2.ExtendAudio.EXTEND_AUDIO_SILENCE,
}

# Configuration constants for extend video options
EXTEND_VIDEO_CONFIGS = {
    "unspecified": lipsync_pb2.ExtendVideo.EXTEND_VIDEO_UNSPECIFIED,
    "forward": lipsync_pb2.ExtendVideo.EXTEND_VIDEO_FORWARD,
    "reverse": lipsync_pb2.ExtendVideo.EXTEND_VIDEO_REVERSE,
}

# Configuration constants for audio codec options
AUDIO_CODEC_CONFIGS = {
    "mp3": audio_pb2.AudioCodec.AUDIO_CODEC_MP3,
    "wav": audio_pb2.AudioCodec.AUDIO_CODEC_WAV,
    "opus": audio_pb2.AudioCodec.AUDIO_CODEC_OPUS,
}

# The NIM decodes only WAV and MP3 on the way in, and muxes only Opus and MP3 on
# the way out. Sending anything else is rejected server-side with INVALID_ARGUMENT,
# so the client validates against these rather than the full codec map above.
INPUT_AUDIO_CODECS = ("wav", "mp3")
OUTPUT_AUDIO_CODECS = ("opus", "mp3")
