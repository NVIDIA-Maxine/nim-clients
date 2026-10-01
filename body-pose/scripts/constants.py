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

"""Constants for the 3D Body Pose NIM client."""

# Constants for data handling
DATA_CHUNK_SIZE = 256 * 1024  # bytes, the video file is streamed in 256KB chunks
DEFAULT_TIMEOUT = 3600.0  # seconds, RPC deadline bounding a stalled stream

# Default asset paths
DEFAULT_VIDEO_PATH = "../assets/sample_video.mp4"
DEFAULT_BBOX_PATH = "../assets/sample_bbox.txt"
DEFAULT_OUTPUT_PATH = "body_pose_output.json"

# Supported input video containers
VIDEO_FILE_TYPES = ["mp4", "webm", "mkv"]

# Per-frame tracked-box capacity of the 3D Body Pose backend. The client rejects
# an over-capacity annotation up front instead of streaming the whole video first.
MAX_BOXES_PER_FRAME = 50

# The exact quadruple marking a tracked body as absent in a frame. Any other box
# with a non-positive width or height is malformed and is rejected by the server.
ABSENT_BODY_BBOX = (-1.0, -1.0, -1.0, -1.0)

# gRPC metadata key the server reads the client-assigned session id from.
CLIENT_SESSION_ID_METADATA_KEY = "client-session-id"

# Skeleton overlay, mirroring the AR SDK sample BodyPose3DApp.
# Nova-77 kinematic tree: parent joint of each of the 77 joints, index 0 (Hips) is the root.
NOVA77_PARENTS = [
    -1, 0, 1, 2, 3, 4, 5, 6, 6, 6, 6, 3, 11, 12, 13, 14, 15, 16, 17,
    14, 19, 20, 21, 22, 14, 24, 25, 26, 27, 14, 29, 30, 31, 32, 14, 34, 35, 36, 37,
    3, 39, 40, 41, 42, 43, 44, 45, 42, 47, 48, 49, 50, 42, 52, 53, 54, 55, 42, 57,
    58, 59, 60, 42, 62, 63, 64, 65, 0, 67, 68, 69, 70, 0, 72, 73, 74, 75,
]  # fmt: skip
# (child, parent) bone list, root excluded.
NOVA77_SKELETON_LINKS = [(i, p) for i, p in enumerate(NOVA77_PARENTS) if p >= 0]

# Per-tracking-id BGR colors for bounding boxes and ID labels.
TRACK_COLORS = [
    (0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 0, 255),
    (255, 255, 0), (255, 128, 0), (128, 0, 255), (0, 128, 255), (128, 255, 0),
]  # fmt: skip
COLOR_2D = (0, 255, 0)  # 2D keypoints and skeleton in green (BGR)
COLOR_3D = (0, 0, 255)  # reprojected 3D keypoints and skeleton in red (BGR)

# Keypoints that may land outside their box by this fraction of its size are still drawn.
BBOX_MARGIN = 0.25

# Keypoint overlay options: which keypoint sets to draw.
DRAW_KEYPOINTS_CONFIGS = {
    "2d": (True, False),
    "3d": (False, True),
    "both": (True, True),
}
