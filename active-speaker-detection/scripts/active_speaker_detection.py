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
"""Main script for running Active Speaker Detection NIM inference.

This script provides functionality to:
- Parse command line arguments for configuring Active Speaker Detection
- Set up gRPC communication with the Active Speaker Detection service
- Send video, audio, and diarization data to the service
- Process responses with speaker detection results

The script supports different SSL modes for secure communication and handles
various input/output formats and configurations.
"""

import os
import sys
import time
from typing import Iterator, Optional
import pathlib

import cv2
import grpc
from tqdm import tqdm

from config import ActiveSpeakerDetectionConfig, parse_args
from constants import (
    AUDIO_ENCODING_CONFIGS,
    VIDEO_CODEC_CONFIGS,
    VOICE_ACTIVITY_SMOOTHING_CONFIGS,
    DATA_CHUNK_SIZE,
    DIARIZATION_WORDS_BATCH_SIZE,
)
from diarization import load_diarization

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
SCRIPT_PATH = str(pathlib.Path(__file__).parent.resolve())
sys.path.insert(0, os.path.join(SCRIPT_PATH, "../interfaces"))

from utils.utils import (  # noqa: E402
    create_channel_credentials,
    create_request_metadata,
    validate_preview_args,
    validate_ssl_args,
    read_file_chunks,
)
from nvidia.ai4m.activespeakerdetection.v1 import activespeakerdetection_pb2  # noqa: E402
from nvidia.ai4m.activespeakerdetection.v1 import activespeakerdetection_pb2_grpc  # noqa: E402
from nvidia.ai4m.audio.v1 import audio_pb2  # noqa: E402
from nvidia.ai4m.video.v1 import video_pb2  # noqa: E402

# gRPC metadata key the server inspects to recover the client-assigned session
# id (see NV_AI4M_SESSION_ID_METADATA_KEY on the server; defaults to this).
CLIENT_SESSION_ID_METADATA_KEY = "client-session-id"


def build_request_metadata(args) -> Optional[tuple]:
    """Build the gRPC request metadata, including the client session id.

    Combines the preview-mode metadata (authorization / function-id) with the
    optional client-session-id header so the server can echo it back in
    ServiceInfo and correlate logs.

    Args:
        args: Parsed command line arguments.

    Returns:
        A tuple of ``(key, value)`` metadata pairs, or ``None`` if empty.
    """
    metadata = list(create_request_metadata(args) or ())
    client_session_id = getattr(args, "client_session_id", None)
    if client_session_id:
        metadata.append((CLIENT_SESSION_ID_METADATA_KEY, client_session_id))
    return tuple(metadata) if metadata else None


def generate_request_for_inference(
    config: ActiveSpeakerDetectionConfig,
) -> Iterator[activespeakerdetection_pb2.DetectActiveSpeakerRequest]:
    """Generate a stream of DetectActiveSpeakerRequest messages.

    Args:
        config: Configuration object containing all parameters

    Yields:
        DetectActiveSpeakerRequest messages containing either configuration or chunks of input data

    Raises:
        RuntimeError: If there are errors reading input files
    """
    print("Generating request for inference")

    # Prepare video/audio files
    video_file_to_send = config.video_filepath
    audio_file_to_send = config.audio_filepath if not config.skip_audio else None

    # Create video config
    video_config = video_pb2.VideoConfig(
        codec=VIDEO_CODEC_CONFIGS[config.input_video_format],
    )

    # Create config message
    detection_config = activespeakerdetection_pb2.ActiveSpeakerDetectionConfig(
        input_video_config=video_config
    )

    # Voice-activity smoothing (optional). Leave unset to use the deployment
    # default (NV_AI4M_ASD_VA_SMOOTHING).
    if config.voice_activity_smoothing is not None:
        detection_config.voice_activity_smoothing = VOICE_ACTIVITY_SMOOTHING_CONFIGS[
            config.voice_activity_smoothing
        ]
        print(f"Voice-activity smoothing: {config.voice_activity_smoothing}")

    # Speaker detection threshold (optional). Leave unset to use the server's
    # configured default; the server validates the (0, 1) range.
    if config.speaker_detection_threshold is not None:
        detection_config.speaker_detection_threshold = config.speaker_detection_threshold
        print(f"Speaker detection threshold: {config.speaker_detection_threshold}")

    # Set audio source mode and config
    if not config.skip_audio:
        audio_config = audio_pb2.AudioConfig(
            encoding=AUDIO_ENCODING_CONFIGS[config.input_audio_format],
        )
        detection_config.input_audio_config.CopyFrom(audio_config)
        detection_config.audio_source_config = (
            activespeakerdetection_pb2.AUDIO_SOURCE_CONFIG_SEPARATE_STREAM
        )
        print("Sending configuration with separate audio stream")
    else:
        audio_config = audio_pb2.AudioConfig(
            encoding=AUDIO_ENCODING_CONFIGS[config.embedded_audio_codec],
        )
        detection_config.input_audio_config.CopyFrom(audio_config)
        detection_config.audio_source_config = (
            activespeakerdetection_pb2.AUDIO_SOURCE_CONFIG_EMBEDDED_IN_VIDEO
        )
        print(
            f"Sending configuration with embedded audio " f"(codec={config.embedded_audio_codec})"
        )

    print("Sending configuration")
    yield activespeakerdetection_pb2.DetectActiveSpeakerRequest(config=detection_config)

    print("Loading diarization data...")
    diarization_info = load_diarization(config.diarization_filepath)
    print(f"Loaded diarization with {len(diarization_info.segments)} segments")

    print("Sending data for inference")

    # Build iterators for each data stream
    video_iter = read_file_chunks(video_file_to_send, DATA_CHUNK_SIZE)
    audio_iter = (
        read_file_chunks(audio_file_to_send, DATA_CHUNK_SIZE) if not config.skip_audio else iter([])
    )

    # Send video, audio, and diarization data in interleaved chunks
    video_chunk_count = 0
    audio_chunk_count = 0
    diarization_batch_count = 0

    video_done = False
    audio_done = config.skip_audio
    diarization_done = diarization_info is None
    segment_index = 0

    while not (video_done and audio_done and diarization_done):
        if not video_done:
            chunk = next(video_iter, None)
            if chunk is None:
                video_done = True
                print(f"Video transfer complete: {video_chunk_count} chunks sent")
            else:
                video_chunk_count += 1
                data = activespeakerdetection_pb2.ActiveSpeakerDetectionData(video_data=chunk)
                yield activespeakerdetection_pb2.DetectActiveSpeakerRequest(data=data)

        if not audio_done:
            chunk = next(audio_iter, None)
            if chunk is None:
                audio_done = True
                print(f"Audio transfer complete: {audio_chunk_count} chunks sent")
            else:
                audio_chunk_count += 1
                data = activespeakerdetection_pb2.ActiveSpeakerDetectionData(audio_data=chunk)
                yield activespeakerdetection_pb2.DetectActiveSpeakerRequest(data=data)

        if not diarization_done and diarization_info is not None:
            all_segments = diarization_info.segments
            total_segments = len(all_segments)
            if segment_index >= total_segments:
                diarization_done = True
                print(f"Diarization transfer complete:" f" {diarization_batch_count} batches sent")
            else:
                batch_end = min(segment_index + DIARIZATION_WORDS_BATCH_SIZE, total_segments)
                batch = all_segments[segment_index:batch_end]
                is_last_batch = batch_end >= total_segments
                segment_index = batch_end
                diarization_batch_count += 1

                batch_info = activespeakerdetection_pb2.AudioDiarizationInfo(
                    segments=batch,
                    transcript=diarization_info.transcript if is_last_batch else "",
                )
                data = activespeakerdetection_pb2.ActiveSpeakerDetectionData(
                    diarization_info=batch_info
                )
                yield activespeakerdetection_pb2.DetectActiveSpeakerRequest(data=data)


def print_service_info(service_info) -> None:
    """Print the one-shot ServiceInfo provenance banner from the server.

    Identifies the NIM producing the stream and the request being served
    (feature name/version, model identity, and request/session IDs).

    Args:
        service_info: nvidia.ai4m.common.v1.ServiceInfo message from the response.
    """
    print("\n" + "-" * 60)
    print("Service info (from server)")
    print("-" * 60)
    print(f"Feature name      : {service_info.feature_name}")
    print(f"Feature version   : {service_info.feature_version}")
    print(f"Model info        : {service_info.model_info}")
    print(f"Server request ID : {service_info.server_request_id}")
    print(f"Client session ID : {service_info.client_session_id}")
    print("-" * 60)
    sys.stdout.flush()


def process_responses(
    response_iter: Iterator[activespeakerdetection_pb2.DetectActiveSpeakerResponse],
    config: ActiveSpeakerDetectionConfig,
) -> None:
    """Process responses from the Active Speaker Detection service.

    Collects per-frame speaker detections and writes an output video
    with bounding boxes overlaid on the original frames.

    Args:
        response_iter: Iterator of responses from the server
        config: Configuration object
    """
    print("Processing responses from server")
    sys.stdout.flush()

    frame_detections: dict[int, list[dict]] = {}
    config_received = False
    service_info_received = False

    pbar = tqdm(
        desc="Receiving results",
        unit="frames",
        dynamic_ncols=True,
        bar_format="{desc}: {n} frames | {rate_fmt}",
    )

    try:
        for response in response_iter:
            if response.HasField("service_info"):
                if not service_info_received:
                    print_service_info(response.service_info)
                    service_info_received = True
                continue

            if response.HasField("config") or response.HasField("keepalive"):
                if response.HasField("config") and not config_received:
                    print("\nReceived configuration acknowledgment from server")
                    config_received = True
                continue

            if response.HasField("active_speaker_detection_result"):
                result = response.active_speaker_detection_result
                pbar.update(1)
                speakers = []
                for s in result.speaker_data:
                    speakers.append(
                        {
                            "diarized_speaker_id": s.diarized_speaker_id,
                            "face_id": s.face_id,
                            "is_speaking": s.is_speaking,
                            "confidence_score": s.face_detection_confidence,
                            "bbox": {
                                "x": s.speaker_bbox.x,
                                "y": s.speaker_bbox.y,
                                "width": s.speaker_bbox.width,
                                "height": s.speaker_bbox.height,
                            },
                        }
                    )
                frame_detections[result.frame_id] = speakers

    finally:
        pbar.close()

    print(f"\nCompleted: Received detections for {len(frame_detections)} frames")

    write_output_video(
        input_video_path=config.video_filepath,
        output_video_path=config.output_filepath,
        frame_detections=frame_detections,
    )


_COLOR_UNESTABLISHED = (0, 0, 255)  # Red  – no audio assigned (tracked only)
_COLOR_SPEAKING = (0, 255, 0)  # Green – currently speaking
_COLOR_NOT_SPEAKING = (255, 0, 0)  # Blue  – audio assigned, not speaking


def _face_color(spk: dict) -> tuple:
    """Three-color scheme: Red=tracked, Blue=audio assigned, Green=speaking."""
    if spk.get("is_speaking"):
        return _COLOR_SPEAKING
    if spk.get("diarized_speaker_id", -1) != -1:
        return _COLOR_NOT_SPEAKING
    return _COLOR_UNESTABLISHED


def _draw_bboxes(
    frame,
    speakers: list[dict],
    fw: int,
    fh: int,
) -> int:
    high_res = fh >= 1440
    font_scale = 1.2 if high_res else 0.6
    font_thickness = 4 if high_res else 2
    box_thickness = 6 if high_res else 3
    label_padding = 20 if high_res else 10
    label_offset = 10 if high_res else 5

    font = cv2.FONT_HERSHEY_SIMPLEX
    drawn = 0
    for spk in speakers:
        bbox = spk["bbox"]
        tracking_id = spk["face_id"]
        confidence = spk["confidence_score"]
        audio_id = spk.get("diarized_speaker_id", -1)
        is_speaking = spk.get("is_speaking", False)

        x = max(0, min(int(bbox["x"]), fw - 1))
        y = max(0, min(int(bbox["y"]), fh - 1))
        w = min(int(bbox["width"]), fw - x)
        h = min(int(bbox["height"]), fh - y)

        color = _face_color(spk)
        text_color = (0, 0, 0) if is_speaking else (255, 255, 255)
        # Draw bbox
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, box_thickness)

        track_label = f"Track:{tracking_id} ({confidence:.2f})"
        (ttw, tth), _ = cv2.getTextSize(track_label, font, font_scale, font_thickness)
        tl_x1, tl_y1 = x, y - tth - label_padding
        tl_x2, tl_y2 = x + ttw, y
        if tl_y1 < 0:
            tl_y1, tl_y2 = y, y + tth + label_padding
        # Draw face tracking information
        cv2.rectangle(frame, (tl_x1, tl_y1), (tl_x2, tl_y2), color, -1)
        text_y = (y - label_offset) if tl_y1 <= y - tth - label_padding else (tl_y2 - label_offset)
        cv2.putText(
            frame,
            track_label,
            (x, text_y),
            font,
            font_scale,
            text_color,
            font_thickness,
            cv2.LINE_AA,
        )

        if audio_id != -1:
            audio_label = f"Audio:{audio_id}"
            (atw, ath), _ = cv2.getTextSize(audio_label, font, font_scale, font_thickness)
            br_x1 = x + w - atw
            br_y1 = y + h
            br_x2 = br_x1 + atw
            br_y2 = br_y1 + ath + label_padding
            if br_y2 > fh:
                br_y2 = fh
                br_y1 = br_y2 - ath - label_padding
            # Draw speaker track id information
            cv2.rectangle(frame, (br_x1, br_y1), (br_x2, br_y2), color, -1)
            cv2.putText(
                frame,
                audio_label,
                (br_x1, br_y1 + ath + label_offset),
                font,
                font_scale,
                text_color,
                font_thickness,
                cv2.LINE_AA,
            )
        drawn += 1
    return drawn


def write_output_video(
    input_video_path: str,
    output_video_path: str,
    frame_detections: dict[int, list[dict]],
) -> None:
    """Read the input video, draw speaker bboxes, and write to output.

    Three-color scheme: Red=tracked only, Blue=audio assigned, Green=speaking.
    Track label (with confidence) at top-left, Audio ID at bottom-right.

    Args:
        input_video_path: Path to the source video.
        output_video_path: Destination path for the annotated video.
        frame_detections: Mapping of frame ID to a list of speaker dicts,
            each with keys ``bbox`` (dict), ``is_speaking``,
            ``face_id``, ``diarized_speaker_id``, ``confidence_score``.
    """
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open input video: {input_video_path}")

    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_video_path, fourcc, fps, (fw, fh))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot open output video for writing: {output_video_path}")

    frame_id_offset = min(frame_detections.keys()) if frame_detections else 0
    print(f"Video: {fw}x{fh} @ {fps:.2f} fps, {total_frames} frames")

    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            det_fid = frame_idx + frame_id_offset
            if det_fid in frame_detections:
                _draw_bboxes(frame, frame_detections[det_fid], fw, fh)

            writer.write(frame)
            frame_idx += 1

    finally:
        cap.release()
        writer.release()

    print(f"Output video written to {output_video_path} ({frame_idx} frames)")


def process_request(
    channel: grpc.Channel,
    config: ActiveSpeakerDetectionConfig,
    request_metadata: Optional[tuple] = None,
) -> None:
    """Process gRPC request and handle responses.

    Args:
        channel: gRPC channel for server client communication
        config: Configuration for the Active Speaker Detection service
        request_metadata: Optional tuple of metadata to include in the gRPC
            request (used for preview mode authentication)
    """
    try:
        stub = activespeakerdetection_pb2_grpc.ActiveSpeakerDetectionServiceStub(channel)
        start_time = time.time()

        responses = stub.DetectActiveSpeaker(
            generate_request_for_inference(config=config),
            metadata=request_metadata,
        )

        process_responses(response_iter=responses, config=config)

        end_time = time.time()
        print(f"Function invocation completed in {end_time - start_time:.2f}s")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise


def main():
    """Main entry point for the Active Speaker Detection client."""
    args = parse_args()

    try:
        validate_ssl_args(args)
        validate_preview_args(args)
    except RuntimeError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    try:
        config = ActiveSpeakerDetectionConfig.from_args(args)
        config.validate_config()
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    print(config)
    print(f"Server      : {args.target}")
    print(f"SSL mode    : {args.ssl_mode}")
    if args.preview_mode:
        print("Preview mode: Enabled")
        print(f"Function ID : {args.function_id}")
    if args.client_session_id:
        print(f"Session ID  : {args.client_session_id}")
    print("=" * 60 + "\n")

    request_metadata = build_request_metadata(args)

    try:
        if args.ssl_mode != "DISABLED":
            channel_credentials = create_channel_credentials(args)
            print(f"Establishing secure channel to {args.target}")
            with grpc.secure_channel(args.target, channel_credentials) as channel:
                process_request(channel, config, request_metadata)
        elif args.preview_mode:
            print(f"Connecting to NVCF preview server at {args.target}")
            with grpc.secure_channel(
                args.target, credentials=grpc.ssl_channel_credentials()
            ) as channel:
                process_request(channel, config, request_metadata)
        else:
            print(f"Establishing insecure channel to {args.target}")
            with grpc.insecure_channel(args.target) as channel:
                process_request(channel, config, request_metadata)

        print("\nDetection completed successfully!")

    except grpc.RpcError as e:
        print(f"\nGRPC Error: {e.code()} - {e.details()}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
