from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DetectSyntheticVideoRequest(_message.Message):
    __slots__ = ("video_file_data",)
    VIDEO_FILE_DATA_FIELD_NUMBER: _ClassVar[int]
    video_file_data: bytes
    def __init__(self, video_file_data: _Optional[bytes] = ...) -> None: ...

class DetectSyntheticVideoResponse(_message.Message):
    __slots__ = ("clip_result", "final_result", "keepalive")
    CLIP_RESULT_FIELD_NUMBER: _ClassVar[int]
    FINAL_RESULT_FIELD_NUMBER: _ClassVar[int]
    KEEPALIVE_FIELD_NUMBER: _ClassVar[int]
    clip_result: ClipResult
    final_result: VideoResult
    keepalive: _empty_pb2.Empty
    def __init__(self, clip_result: _Optional[_Union[ClipResult, _Mapping]] = ..., final_result: _Optional[_Union[VideoResult, _Mapping]] = ..., keepalive: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class ClipResult(_message.Message):
    __slots__ = ("index", "logit")
    INDEX_FIELD_NUMBER: _ClassVar[int]
    LOGIT_FIELD_NUMBER: _ClassVar[int]
    index: int
    logit: float
    def __init__(self, index: _Optional[int] = ..., logit: _Optional[float] = ...) -> None: ...

class VideoResult(_message.Message):
    __slots__ = ("logit", "probability", "csv_data", "total_clips")
    LOGIT_FIELD_NUMBER: _ClassVar[int]
    PROBABILITY_FIELD_NUMBER: _ClassVar[int]
    CSV_DATA_FIELD_NUMBER: _ClassVar[int]
    TOTAL_CLIPS_FIELD_NUMBER: _ClassVar[int]
    logit: float
    probability: float
    csv_data: str
    total_clips: int
    def __init__(self, logit: _Optional[float] = ..., probability: _Optional[float] = ..., csv_data: _Optional[str] = ..., total_clips: _Optional[int] = ...) -> None: ...
