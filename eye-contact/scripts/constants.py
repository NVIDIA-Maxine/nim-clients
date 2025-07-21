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

# Constants for data handling
DATA_CHUNK_SIZE = 64 * 1024  # bytes, we send the mp4 file in 64KB chunks
DEFAULT_BITRATE = 3000000  # bps
DEFAULT_IDR_INTERVAL = 8  # frames
DEFAULT_STREAMABLE_VIDEO_PATH = "../assets/sample_streamable.mp4"
DEFAULT_NON_STREAMABLE_VIDEO_PATH = "../assets/sample_transactional.mp4"

# Default values from eyecontact.proto
DEFAULT_TEMPORAL = 0xFFFFFFFF
DEFAULT_DETECT_CLOSURE = 0
DEFAULT_EYE_SIZE_SENSITIVITY = 3
DEFAULT_ENABLE_LOOKAWAY = 0
DEFAULT_LOOKAWAY_MAX_OFFSET = 5
DEFAULT_LOOKAWAY_INTERVAL_MIN = 3
DEFAULT_LOOKAWAY_INTERVAL_RANGE = 8
DEFAULT_GAZE_PITCH_THRESHOLD_LOW = 25.0
DEFAULT_GAZE_PITCH_THRESHOLD_HIGH = 30.0
DEFAULT_GAZE_YAW_THRESHOLD_LOW = 20.0
DEFAULT_GAZE_YAW_THRESHOLD_HIGH = 30.0
DEFAULT_HEAD_PITCH_THRESHOLD_LOW = 20.0
DEFAULT_HEAD_PITCH_THRESHOLD_HIGH = 25.0
DEFAULT_HEAD_YAW_THRESHOLD_LOW = 25.0
DEFAULT_HEAD_YAW_THRESHOLD_HIGH = 30.0

# Parameter validation ranges
PARAM_RANGES = {
    "temporal": (0, 0xFFFFFFFF),
    "detect_closure": (0, 1),
    "eye_size_sensitivity": (2, 6),
    "enable_lookaway": (0, 1),
    "lookaway_max_offset": (1, 10),
    "lookaway_interval_min": (1, 600),
    "lookaway_interval_range": (1, 600),
    "gaze_pitch_threshold_low": (10.0, 35.0),
    "gaze_pitch_threshold_high": (10.0, 35.0),
    "gaze_yaw_threshold_low": (10.0, 35.0),
    "gaze_yaw_threshold_high": (10.0, 35.0),
    "head_pitch_threshold_low": (10.0, 35.0),
    "head_pitch_threshold_high": (10.0, 35.0),
    "head_yaw_threshold_low": (10.0, 35.0),
    "head_yaw_threshold_high": (10.0, 35.0),
}
