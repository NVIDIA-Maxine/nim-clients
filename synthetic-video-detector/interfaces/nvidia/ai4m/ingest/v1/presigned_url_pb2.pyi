from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UrlProvider(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    URL_PROVIDER_UNSPECIFIED: _ClassVar[UrlProvider]
    URL_PROVIDER_S3: _ClassVar[UrlProvider]

class ChecksumType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CHECKSUM_TYPE_UNSPECIFIED: _ClassVar[ChecksumType]
    CHECKSUM_TYPE_MD5: _ClassVar[ChecksumType]
    CHECKSUM_TYPE_SHA256: _ClassVar[ChecksumType]
    CHECKSUM_TYPE_SHA512: _ClassVar[ChecksumType]
URL_PROVIDER_UNSPECIFIED: UrlProvider
URL_PROVIDER_S3: UrlProvider
CHECKSUM_TYPE_UNSPECIFIED: ChecksumType
CHECKSUM_TYPE_MD5: ChecksumType
CHECKSUM_TYPE_SHA256: ChecksumType
CHECKSUM_TYPE_SHA512: ChecksumType

class FileChecksum(_message.Message):
    __slots__ = ("type", "md5_hex", "sha256_hex", "sha512_hex")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    MD5_HEX_FIELD_NUMBER: _ClassVar[int]
    SHA256_HEX_FIELD_NUMBER: _ClassVar[int]
    SHA512_HEX_FIELD_NUMBER: _ClassVar[int]
    type: ChecksumType
    md5_hex: str
    sha256_hex: str
    sha512_hex: str
    def __init__(self, type: _Optional[_Union[ChecksumType, str]] = ..., md5_hex: _Optional[str] = ..., sha256_hex: _Optional[str] = ..., sha512_hex: _Optional[str] = ...) -> None: ...

class ProviderSpecificParams(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PresignedUrl(_message.Message):
    __slots__ = ("url", "checksum", "verify_checksum", "expected_content_length_bytes", "content_type", "expires_at_unix_ms", "url_provider", "provider_specific_params")
    URL_FIELD_NUMBER: _ClassVar[int]
    CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    VERIFY_CHECKSUM_FIELD_NUMBER: _ClassVar[int]
    EXPECTED_CONTENT_LENGTH_BYTES_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_AT_UNIX_MS_FIELD_NUMBER: _ClassVar[int]
    URL_PROVIDER_FIELD_NUMBER: _ClassVar[int]
    PROVIDER_SPECIFIC_PARAMS_FIELD_NUMBER: _ClassVar[int]
    url: str
    checksum: FileChecksum
    verify_checksum: bool
    expected_content_length_bytes: int
    content_type: str
    expires_at_unix_ms: int
    url_provider: UrlProvider
    provider_specific_params: ProviderSpecificParams
    def __init__(self, url: _Optional[str] = ..., checksum: _Optional[_Union[FileChecksum, _Mapping]] = ..., verify_checksum: bool = ..., expected_content_length_bytes: _Optional[int] = ..., content_type: _Optional[str] = ..., expires_at_unix_ms: _Optional[int] = ..., url_provider: _Optional[_Union[UrlProvider, str]] = ..., provider_specific_params: _Optional[_Union[ProviderSpecificParams, _Mapping]] = ...) -> None: ...
