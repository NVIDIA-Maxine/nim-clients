from google.protobuf import empty_pb2 as _empty_pb2
from nvidia.ai4m.ingest.v1 import presigned_url_pb2 as _presigned_url_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class DetectSyntheticVideoRequest(_message.Message):
    __slots__ = ("video_file_data", "presigned_url")
    VIDEO_FILE_DATA_FIELD_NUMBER: _ClassVar[int]
    PRESIGNED_URL_FIELD_NUMBER: _ClassVar[int]
    video_file_data: bytes
    presigned_url: _presigned_url_pb2.PresignedUrl
    def __init__(self, video_file_data: _Optional[bytes] = ..., presigned_url: _Optional[_Union[_presigned_url_pb2.PresignedUrl, _Mapping]] = ...) -> None: ...

class DetectSyntheticVideoResponse(_message.Message):
    __slots__ = ("service_info", "frame_results", "final_result", "keepalive")
    SERVICE_INFO_FIELD_NUMBER: _ClassVar[int]
    FRAME_RESULTS_FIELD_NUMBER: _ClassVar[int]
    FINAL_RESULT_FIELD_NUMBER: _ClassVar[int]
    KEEPALIVE_FIELD_NUMBER: _ClassVar[int]
    service_info: ServiceInfo
    frame_results: FrameResultBatch
    final_result: DetectionResult
    keepalive: _empty_pb2.Empty
    def __init__(self, service_info: _Optional[_Union[ServiceInfo, _Mapping]] = ..., frame_results: _Optional[_Union[FrameResultBatch, _Mapping]] = ..., final_result: _Optional[_Union[DetectionResult, _Mapping]] = ..., keepalive: _Optional[_Union[_empty_pb2.Empty, _Mapping]] = ...) -> None: ...

class FrameResult(_message.Message):
    __slots__ = ("frame_id", "logit", "timestamp_ns")
    FRAME_ID_FIELD_NUMBER: _ClassVar[int]
    LOGIT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_NS_FIELD_NUMBER: _ClassVar[int]
    frame_id: int
    logit: float
    timestamp_ns: int
    def __init__(self, frame_id: _Optional[int] = ..., logit: _Optional[float] = ..., timestamp_ns: _Optional[int] = ...) -> None: ...

class FrameResultBatch(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[FrameResult]
    def __init__(self, results: _Optional[_Iterable[_Union[FrameResult, _Mapping]]] = ...) -> None: ...

class DetectionResult(_message.Message):
    __slots__ = ("mean_logit", "synthetic_probability", "total_frames")
    MEAN_LOGIT_FIELD_NUMBER: _ClassVar[int]
    SYNTHETIC_PROBABILITY_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FRAMES_FIELD_NUMBER: _ClassVar[int]
    mean_logit: float
    synthetic_probability: float
    total_frames: int
    def __init__(self, mean_logit: _Optional[float] = ..., synthetic_probability: _Optional[float] = ..., total_frames: _Optional[int] = ...) -> None: ...

class ServiceInfo(_message.Message):
    __slots__ = ("nim_version", "model_version", "request_id")
    NIM_VERSION_FIELD_NUMBER: _ClassVar[int]
    MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    REQUEST_ID_FIELD_NUMBER: _ClassVar[int]
    nim_version: str
    model_version: str
    request_id: str
    def __init__(self, nim_version: _Optional[str] = ..., model_version: _Optional[str] = ..., request_id: _Optional[str] = ...) -> None: ...
