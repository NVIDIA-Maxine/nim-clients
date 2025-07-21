from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LossyEncoding(_message.Message):
    __slots__ = ("bitrate", "idr_interval")
    BITRATE_FIELD_NUMBER: _ClassVar[int]
    IDR_INTERVAL_FIELD_NUMBER: _ClassVar[int]
    bitrate: int
    idr_interval: int
    def __init__(self, bitrate: _Optional[int] = ..., idr_interval: _Optional[int] = ...) -> None: ...

class CustomEncodingParams(_message.Message):
    __slots__ = ("custom",)
    class CustomEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _any_pb2.Any
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
    CUSTOM_FIELD_NUMBER: _ClassVar[int]
    custom: _containers.MessageMap[str, _any_pb2.Any]
    def __init__(self, custom: _Optional[_Mapping[str, _any_pb2.Any]] = ...) -> None: ...

class OutputVideoEncoding(_message.Message):
    __slots__ = ("lossless", "lossy", "custom_encoding")
    LOSSLESS_FIELD_NUMBER: _ClassVar[int]
    LOSSY_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_ENCODING_FIELD_NUMBER: _ClassVar[int]
    lossless: bool
    lossy: LossyEncoding
    custom_encoding: CustomEncodingParams
    def __init__(self, lossless: bool = ..., lossy: _Optional[_Union[LossyEncoding, _Mapping]] = ..., custom_encoding: _Optional[_Union[CustomEncodingParams, _Mapping]] = ...) -> None: ...

class RedirectGazeConfig(_message.Message):
    __slots__ = ("temporal", "detect_closure", "eye_size_sensitivity", "enable_lookaway", "lookaway_max_offset", "lookaway_interval_min", "lookaway_interval_range", "gaze_pitch_threshold_low", "gaze_pitch_threshold_high", "gaze_yaw_threshold_low", "gaze_yaw_threshold_high", "head_pitch_threshold_low", "head_pitch_threshold_high", "head_yaw_threshold_low", "head_yaw_threshold_high", "output_video_encoding")
    TEMPORAL_FIELD_NUMBER: _ClassVar[int]
    DETECT_CLOSURE_FIELD_NUMBER: _ClassVar[int]
    EYE_SIZE_SENSITIVITY_FIELD_NUMBER: _ClassVar[int]
    ENABLE_LOOKAWAY_FIELD_NUMBER: _ClassVar[int]
    LOOKAWAY_MAX_OFFSET_FIELD_NUMBER: _ClassVar[int]
    LOOKAWAY_INTERVAL_MIN_FIELD_NUMBER: _ClassVar[int]
    LOOKAWAY_INTERVAL_RANGE_FIELD_NUMBER: _ClassVar[int]
    GAZE_PITCH_THRESHOLD_LOW_FIELD_NUMBER: _ClassVar[int]
    GAZE_PITCH_THRESHOLD_HIGH_FIELD_NUMBER: _ClassVar[int]
    GAZE_YAW_THRESHOLD_LOW_FIELD_NUMBER: _ClassVar[int]
    GAZE_YAW_THRESHOLD_HIGH_FIELD_NUMBER: _ClassVar[int]
    HEAD_PITCH_THRESHOLD_LOW_FIELD_NUMBER: _ClassVar[int]
    HEAD_PITCH_THRESHOLD_HIGH_FIELD_NUMBER: _ClassVar[int]
    HEAD_YAW_THRESHOLD_LOW_FIELD_NUMBER: _ClassVar[int]
    HEAD_YAW_THRESHOLD_HIGH_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_VIDEO_ENCODING_FIELD_NUMBER: _ClassVar[int]
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
    output_video_encoding: OutputVideoEncoding
    def __init__(self, temporal: _Optional[int] = ..., detect_closure: _Optional[int] = ..., eye_size_sensitivity: _Optional[int] = ..., enable_lookaway: _Optional[int] = ..., lookaway_max_offset: _Optional[int] = ..., lookaway_interval_min: _Optional[int] = ..., lookaway_interval_range: _Optional[int] = ..., gaze_pitch_threshold_low: _Optional[float] = ..., gaze_pitch_threshold_high: _Optional[float] = ..., gaze_yaw_threshold_low: _Optional[float] = ..., gaze_yaw_threshold_high: _Optional[float] = ..., head_pitch_threshold_low: _Optional[float] = ..., head_pitch_threshold_high: _Optional[float] = ..., head_yaw_threshold_low: _Optional[float] = ..., head_yaw_threshold_high: _Optional[float] = ..., output_video_encoding: _Optional[_Union[OutputVideoEncoding, _Mapping]] = ...) -> None: ...

class RedirectGazeRequest(_message.Message):
    __slots__ = ("config", "video_file_data")
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    VIDEO_FILE_DATA_FIELD_NUMBER: _ClassVar[int]
    config: RedirectGazeConfig
    video_file_data: bytes
    def __init__(self, config: _Optional[_Union[RedirectGazeConfig, _Mapping]] = ..., video_file_data: _Optional[bytes] = ...) -> None: ...

class RedirectGazeResponse(_message.Message):
    __slots__ = ("config", "video_file_data", "keepalive")
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    VIDEO_FILE_DATA_FIELD_NUMBER: _ClassVar[int]
    KEEPALIVE_FIELD_NUMBER: _ClassVar[int]
    config: RedirectGazeConfig
    video_file_data: bytes
    keepalive: _empty_pb2.Empty
    def __init__(self, config: _Optional[_Union[RedirectGazeConfig, _Mapping]] = ..., video_file_data: _Optional[bytes] = ..., keepalive: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...
