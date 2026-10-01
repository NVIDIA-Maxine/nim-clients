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

"""Main script for running 3D Body Pose NIM inference.

This script provides functionality to:
- Parse command line arguments for configuring 3D Body Pose
- Set up gRPC communication with the 3D Body Pose service
- Send the compressed video and the tracked bounding boxes to the service
- Write the per-frame poses to a JSON Lines file
- Optionally render the Nova-77 skeleton overlay onto the input video

The script supports different SSL modes for secure communication and the NVCF
preview mode.
"""

import json
import os
import pathlib
import sys
import time
from collections import defaultdict
from typing import Iterator, Optional

import cv2
import grpc
import numpy as np
from tqdm import tqdm

from config import BodyPoseClientConfig, parse_args
from constants import (
    ABSENT_BODY_BBOX,
    BBOX_MARGIN,
    CLIENT_SESSION_ID_METADATA_KEY,
    COLOR_2D,
    COLOR_3D,
    DATA_CHUNK_SIZE,
    DRAW_KEYPOINTS_CONFIGS,
    MAX_BOXES_PER_FRAME,
    NOVA77_SKELETON_LINKS,
    TRACK_COLORS,
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.insert(0, os.path.join(SCRIPT_PATH, "../interfaces"))

from utils.utils import (  # noqa: E402
    create_channel_credentials,
    create_request_metadata,
    read_file_chunks,
    validate_preview_args,
    validate_ssl_args,
)
from nvidia.ai4m.body_pose.v1 import body_pose_pb2  # noqa: E402
from nvidia.ai4m.body_pose.v1 import body_pose_pb2_grpc  # noqa: E402


def read_tracked_bboxes(bbox_filepath: os.PathLike) -> list[body_pose_pb2.FrameBoxes]:
    """Read the tracked bounding-box annotation file.

    Line 1 is the number of tracked bodies; each following line is
    ``frame_id tracking_id x y w h`` in full-image pixels. Rows equal to
    ``-1 -1 -1 -1`` mark a body as absent in that frame and are skipped; any
    other invalid box is sent as-is for the server to report.

    Args:
        bbox_filepath: Path to the annotation file

    Returns:
        Tracked boxes grouped per frame, sorted by frame id

    Raises:
        ValueError: If the file is malformed or exceeds the per-frame box capacity
    """
    boxes_by_frame = defaultdict(list)
    with open(bbox_filepath, "r") as bbox_file:
        header = bbox_file.readline().split()
        try:
            num_bodies = int(header[0]) if header else 0
        except ValueError:
            num_bodies = 0
        if not 0 < num_bodies <= MAX_BOXES_PER_FRAME:
            raise ValueError(
                f"{bbox_filepath}: line 1 must be the number of tracked bodies, "
                f"between 1 and {MAX_BOXES_PER_FRAME}"
            )
        for line_number, line in enumerate(bbox_file, start=2):
            fields = line.split()
            if not fields:
                continue
            if len(fields) != 6:
                raise ValueError(
                    f"{bbox_filepath}: line {line_number} has {len(fields)} fields, "
                    "expected 6 (frame_id tracking_id x y w h)"
                )
            try:
                frame_id, tracking_id = int(fields[0]), int(fields[1])
                x, y, width, height = (float(v) for v in fields[2:])
                if (x, y, width, height) == ABSENT_BODY_BBOX:
                    continue
                boxes_by_frame[frame_id].append(
                    body_pose_pb2.BoundingBox(
                        x=x, y=y, width=width, height=height, tracking_id=tracking_id
                    )
                )
            except ValueError as e:
                raise ValueError(f"{bbox_filepath}: line {line_number}: {e}") from None

    if not boxes_by_frame:
        raise ValueError(f"{bbox_filepath}: no bounding box to send, every row is absent")
    crowded = sorted(
        fid for fid, boxes in boxes_by_frame.items() if len(boxes) > MAX_BOXES_PER_FRAME
    )
    if crowded:
        raise ValueError(
            f"{bbox_filepath}: {len(crowded)} frame(s) have more than {MAX_BOXES_PER_FRAME} "
            f"boxes, starting with frame {crowded[0]}"
        )
    return [
        body_pose_pb2.FrameBoxes(frame_id=frame_id, boxes=boxes)
        for frame_id, boxes in sorted(boxes_by_frame.items())
    ]


def generate_request_for_inference(
    config: BodyPoseClientConfig,
    tracked_bboxes: list[body_pose_pb2.FrameBoxes],
) -> Iterator[body_pose_pb2.BodyPoseRequest]:
    """Generate the stream of BodyPoseRequest messages for the 3D Body Pose service.

    The first request carries the configuration and every tracked box; the
    following requests carry the compressed video file in chunks.

    Args:
        config: Configuration object containing all 3D Body Pose parameters
        tracked_bboxes: Tracked boxes grouped per frame

    Yields:
        BodyPoseRequest messages
    """
    pose_config = body_pose_pb2.BodyPoseConfig(focal_length=config.focal_length)
    if config.enable_contact is not None:
        pose_config.enable_contact = config.enable_contact
    yield body_pose_pb2.BodyPoseRequest(config=pose_config, tracked_bboxes=tracked_bboxes)

    for chunk in read_file_chunks(config.video_filepath, DATA_CHUNK_SIZE):
        yield body_pose_pb2.BodyPoseRequest(video_data=chunk)


def print_service_info(service_info) -> None:
    """Print the provenance banner the server sends ahead of the poses."""
    print("-" * 60)
    print("Service info (from server)")
    print("-" * 60)
    print(f"Feature name     : {service_info.feature_name}")
    print(f"Feature version  : {service_info.feature_version}")
    print(f"Model info       : {service_info.model_info}")
    print(f"Server request ID: {service_info.server_request_id}")
    print(f"Client session ID: {service_info.client_session_id}")
    print("-" * 60, flush=True)


def body_to_dict(body: body_pose_pb2.Body) -> dict:
    """Convert one body to the JSON shape of the AR SDK sample app."""
    root_pose = body.root_pose
    return {
        "tracking_id": body.bbox.tracking_id,
        "bbox": [body.bbox.x, body.bbox.y, body.bbox.width, body.bbox.height],
        "keypoints_2d": [[p.x, p.y] for p in body.keypoints_2d],
        "keypoints_confidence": list(body.keypoint_confidence),
        "keypoints_3d": [[p.x, p.y, p.z] for p in body.keypoints_3d],
        "rest_pose": [[p.x, p.y, p.z] for p in body.rest_pose],
        "joint_rotations": [[q.x, q.y, q.z, q.w] for q in body.joint_rotations],
        "root_pose": {
            "translation": [
                root_pose.translation.x,
                root_pose.translation.y,
                root_pose.translation.z,
            ],
            "rotation": [
                root_pose.rotation.x,
                root_pose.rotation.y,
                root_pose.rotation.z,
                root_pose.rotation.w,
            ],
        },
    }


def process_responses(
    response_iter: Iterator[body_pose_pb2.BodyPoseResponse],
    config: BodyPoseClientConfig,
) -> tuple[dict, float]:
    """Write the poses from the response stream to the output JSON Lines file.

    Outputs are delayed: the server fills its temporal window before sending the
    first pose, then sends one ready response per decoded frame, and ends with a
    stream_flushed response. The output file is opened on the first pose, and a
    stream that fails or carries no pose leaves it renamed to ``<output>.partial``
    so it cannot be mistaken for a result.

    Args:
        response_iter: Responses from the server
        config: Configuration for the 3D Body Pose service

    Returns:
        Poses per frame kept for the overlay (empty when no overlay is requested),
        and the focal length the server reprojects the 3D keypoints with

    Raises:
        RuntimeError: If the server returned no pose
    """
    keep_for_overlay = config.overlay_filepath is not None
    poses_by_frame = {}
    focal_length = 0.0
    frames_with_bodies = 0
    output_file = None
    pbar = None
    completed = False
    try:
        for response in response_iter:
            if response.HasField("service_info"):
                print_service_info(response.service_info)
                print(
                    "Buffering: the server sends the first poses once its temporal window "
                    "has filled, then one pose frame per input frame",
                    flush=True,
                )
                continue
            if response.focal_length > 0.0:
                focal_length = response.focal_length
            if response.ready:
                if output_file is None:
                    output_file = open(config.output_filepath, "w")
                    pbar = tqdm(desc="Receiving poses", unit="frame", disable=None)
                detections = [body_to_dict(body) for body in response.bodies]
                output_file.write(
                    json.dumps({"frame_id": response.frame_id, "detections": detections}) + "\n"
                )
                if detections:
                    frames_with_bodies += 1
                if keep_for_overlay:
                    poses_by_frame[response.frame_id] = [
                        (
                            det["tracking_id"],
                            det["bbox"],
                            np.asarray(det["keypoints_2d"], np.float32).reshape(-1, 2),
                            np.asarray(det["keypoints_confidence"], np.float32),
                            np.asarray(det["keypoints_3d"], np.float32).reshape(-1, 3),
                        )
                        for det in detections
                    ]
                pbar.update(1)
            if response.stream_flushed:
                break
        completed = frames_with_bodies > 0
    finally:
        if pbar is not None:
            pbar.close()
        if output_file is not None:
            output_file.close()
            if not completed:
                partial_filepath = f"{config.output_filepath}.partial"
                os.replace(config.output_filepath, partial_filepath)
                print(f"Incomplete output moved to {partial_filepath}", file=sys.stderr)

    if frames_with_bodies == 0:
        raise RuntimeError("The server returned no poses; check the server log")
    print(f"Received poses for {frames_with_bodies} frame(s)")
    return poses_by_frame, focal_length


def draw_skeleton(frame, points, visible, color, radius: int) -> None:
    """Draw the visible Nova-77 joints and the bones joining two visible joints."""

    def pixel(p):
        return round(float(p[0])), round(float(p[1]))

    for joint in np.flatnonzero(visible):
        cv2.circle(frame, pixel(points[joint]), radius, color, -1)
    for child, parent in NOVA77_SKELETON_LINKS:
        if visible[child] and visible[parent]:
            cv2.line(frame, pixel(points[child]), pixel(points[parent]), color, 2)


def draw_overlay(frame, bodies: list, frame_id: int, focal_length: float, draw_keypoints: str):
    """Draw one frame's overlay, mirroring the AR SDK sample BodyPose3DApp.

    Boxes and ID labels are colored per tracking id; 2D keypoints are drawn in
    green inside their box, and 3D keypoints reprojected with a pinhole camera
    are drawn in red inside the frame.
    """
    draw_2d, draw_3d = DRAW_KEYPOINTS_CONFIGS[draw_keypoints]
    height, width = frame.shape[:2]
    cv2.putText(
        frame, f"Frame: {frame_id}", (18, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
    )
    for tracking_id, bbox, keypoints_2d, confidence, keypoints_3d in bodies:
        x, y, w, h = bbox
        color = TRACK_COLORS[tracking_id % len(TRACK_COLORS)]
        cv2.rectangle(frame, (round(x), round(y)), (round(x + w), round(y + h)), color, 2)
        cv2.putText(
            frame,
            f"ID: {tracking_id}",
            (round(x), max(round(y) - 8, 12)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

        if draw_2d and len(keypoints_2d):
            mx, my = w * BBOX_MARGIN, h * BBOX_MARGIN
            px, py = keypoints_2d[:, 0], keypoints_2d[:, 1]
            visible = (
                (confidence > 0.0)
                & np.isfinite(keypoints_2d).all(axis=1)
                & (px >= x - mx)
                & (px <= x + w + mx)
                & (py >= y - my)
                & (py <= y + h + my)
            )
            draw_skeleton(frame, keypoints_2d, visible, COLOR_2D, 4)

        if draw_3d and len(keypoints_3d):
            z = keypoints_3d[:, 2:3]
            with np.errstate(divide="ignore", invalid="ignore"):
                projected = focal_length * keypoints_3d[:, :2] / z + (width * 0.5, height * 0.5)
            px, py = projected[:, 0], projected[:, 1]
            visible = (
                (z[:, 0] > 1e-6)
                & np.isfinite(projected).all(axis=1)
                & (px >= 0)
                & (px < width)
                & (py >= 0)
                & (py < height)
            )
            draw_skeleton(frame, projected, visible, COLOR_3D, 3)


def write_overlay_video(
    config: BodyPoseClientConfig, poses_by_frame: dict, focal_length: float
) -> None:
    """Read the input video, draw the skeleton overlay, and write it to the overlay output.

    Args:
        config: Configuration for the 3D Body Pose service
        poses_by_frame: Poses per frame returned by process_responses
        focal_length: Focal length the server reprojects with; 0 uses the frame diagonal
    """
    cap = cv2.VideoCapture(str(config.video_filepath))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open input video: {config.video_filepath}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or None
    focal_length = focal_length or float(np.hypot(width, height))

    writer = cv2.VideoWriter(
        str(config.overlay_filepath), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot open overlay video for writing: {config.overlay_filepath}")

    frame_id = 0
    try:
        with tqdm(total=total_frames, desc="Drawing overlay", unit="frame", disable=None) as pbar:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                draw_overlay(
                    frame,
                    poses_by_frame.get(frame_id, []),
                    frame_id,
                    focal_length,
                    config.draw_keypoints,
                )
                writer.write(frame)
                frame_id += 1
                pbar.update(1)
    finally:
        cap.release()
        writer.release()
    print(f"Overlay video written to {config.overlay_filepath} ({frame_id} frames)")


def process_request(
    channel: grpc.Channel,
    config: BodyPoseClientConfig,
    tracked_bboxes: list[body_pose_pb2.FrameBoxes],
    request_metadata: Optional[tuple] = None,
) -> None:
    """Process gRPC request and handle responses.

    Args:
        channel: gRPC channel for server client communication
        config: Configuration for the 3D Body Pose service
        tracked_bboxes: Tracked boxes grouped per frame
        request_metadata: Optional tuple of metadata to include in the gRPC request
    """
    stub = body_pose_pb2_grpc.BodyPoseServiceStub(channel)
    start_time = time.time()

    responses = stub.EstimateBodyPose(
        generate_request_for_inference(config, tracked_bboxes),
        metadata=request_metadata,
        timeout=config.timeout or None,
    )
    # A mismatched --enable-contact is served with the server's own value and
    # announced here, ahead of the first pose.
    for key, value in responses.initial_metadata() or ():
        if key == "warning":
            print(f"Server warning: {value}", flush=True)

    poses_by_frame, focal_length = process_responses(responses, config)
    print(f"Function invocation completed in {time.time() - start_time:.2f}s")
    print(f"Poses written to {config.output_filepath}")

    if config.overlay_filepath:
        write_overlay_video(config, poses_by_frame, focal_length)


def main():
    """Main entry point for the 3D Body Pose client."""
    args = parse_args()

    try:
        validate_ssl_args(args)
        validate_preview_args(args)
        config = BodyPoseClientConfig.from_args(args)
        config.validate_config()
        tracked_bboxes = read_tracked_bboxes(config.bbox_filepath)
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    print(config)
    print(f"Server      : {args.target}")
    print(f"SSL mode    : {args.ssl_mode}")
    if args.preview_mode:
        print("Preview mode: Enabled")
        print(f"Function ID : {args.function_id}")
    num_bodies = len({box.tracking_id for frame in tracked_bboxes for box in frame.boxes})
    print(f"Loaded {num_bodies} tracked body(ies) across {len(tracked_bboxes)} frame(s)")
    print("=" * 60 + "\n")

    request_metadata = create_request_metadata(args) or ()
    if config.client_session_id:
        request_metadata += ((CLIENT_SESSION_ID_METADATA_KEY, config.client_session_id),)

    try:
        if args.ssl_mode != "DISABLED":
            channel_credentials = create_channel_credentials(args)
            print(f"Establishing secure channel to {args.target}")
            with grpc.secure_channel(args.target, channel_credentials) as channel:
                process_request(channel, config, tracked_bboxes, request_metadata)
        elif args.preview_mode:
            print(f"Connecting to NVCF preview server at {args.target}")
            with grpc.secure_channel(
                args.target, credentials=grpc.ssl_channel_credentials()
            ) as channel:
                process_request(channel, config, tracked_bboxes, request_metadata)
        else:
            print(f"Establishing insecure channel to {args.target}")
            with grpc.insecure_channel(args.target) as channel:
                process_request(channel, config, tracked_bboxes, request_metadata)

    except grpc.RpcError as e:
        print(f"\ngRPC error: {e.code().name}: {e.details()}")
        too_large = "larger than max" in (e.details() or "")
        if e.code() == grpc.StatusCode.RESOURCE_EXHAUSTED and too_large:
            print(
                "Hint: the annotation is sent as one message and exceeds the server's size limit. "
                "Raise NV_AI4M_GRPC_MAX_MESSAGE_SIZE_BYTES on the server, or process the clip in "
                "shorter segments."
            )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
