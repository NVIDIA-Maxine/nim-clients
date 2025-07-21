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

import os
import csv
import itertools
from typing import Iterator, List, Union
import argparse
import grpc
from google.protobuf import any_pb2, wrappers_pb2


def add_ssl_arguments(parser: argparse.ArgumentParser) -> None:
    """Add SSL-related arguments to an argument parser.

    Args:
        parser: The argument parser to add SSL arguments to
    """
    # SSL and connection arguments
    parser.add_argument(
        "--ssl-mode",
        type=str,
        help="Flag to set SSL mode, default is DISABLED",
        default="DISABLED",
        choices=["DISABLED", "MTLS", "TLS"],
    )
    parser.add_argument(
        "--ssl-key",
        type=str,
        default="../ssl_key/ssl_key_client.pem",
        help="The path to ssl private key.",
    )
    parser.add_argument(
        "--ssl-cert",
        type=str,
        default="../ssl_key/ssl_cert_client.pem",
        help="The path to ssl certificate chain.",
    )
    parser.add_argument(
        "--ssl-root-cert",
        type=str,
        default="../ssl_key/ssl_ca_cert.pem",
        help="The path to ssl root certificate.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="127.0.0.1:8001",
        help="IP:port of gRPC service, when hosted locally. Use "
        "grpc.nvcf.nvidia.com:443 when hosted on NVCF.",
    )


def add_preview_arguments(parser: argparse.ArgumentParser) -> None:
    """Add preview mode related arguments to an argument parser.

    Args:
        parser: The argument parser to add preview arguments to
    """
    # Preview mode and NVCF arguments
    parser.add_argument(
        "--preview-mode",
        action="store_true",
        help="Flag to send request to preview NVCF NIM server on "
        "https://build.nvidia.com/nvidia/eyecontact/api. ",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="NGC API key required for authentication, utilized when using "
        "TRY API ignored otherwise",
    )
    parser.add_argument(
        "--function-id",
        type=str,
        help="NVCF function ID for the service, utilized when using TRY API " "ignored otherwise",
    )


def validate_ssl_args(args: argparse.Namespace) -> None:
    """Validate SSL-related arguments.

    Args:
        args: Parsed command line arguments

    Raises:
        RuntimeError: If SSL configuration is invalid
    """
    if args.ssl_mode == "MTLS":
        if not (args.ssl_key and args.ssl_cert and args.ssl_root_cert):
            raise RuntimeError(
                "If --ssl-mode is MTLS, --ssl-key, --ssl-cert and " "--ssl-root-cert are required."
            )
    elif args.ssl_mode == "TLS":
        if not args.ssl_root_cert:
            raise RuntimeError("If --ssl-mode is TLS, --ssl-root-cert is required.")


def validate_preview_args(args: argparse.Namespace) -> None:
    """Validate preview mode related arguments.

    Args:
        args: Parsed command line arguments

    Raises:
        RuntimeError: If preview configuration is invalid
    """
    if args.preview_mode:
        if not args.api_key or not args.function_id:
            raise RuntimeError(
                "If --preview-mode is specified, both --api-key and " "--function-id are required."
            )


def create_request_metadata(args: argparse.Namespace) -> tuple | None:
    """Create request metadata for preview mode.

    Args:
        args: Parsed command line arguments

    Returns:
        Request metadata tuple or None
    """
    if args.preview_mode:
        return (
            ("authorization", "Bearer {}".format(args.api_key)),
            ("function-id", args.function_id),
        )
    return None


def is_file_available(file_path: os.PathLike, file_types: List[str]) -> bool:
    """Check if the file exists.

    Args:
        file_path: Path to input file
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found")
    for file_type in file_types:
        if os.path.splitext(file_path)[1].lower() == f".{file_type}":
            return True
    return False


def read_file_content(file_path: os.PathLike) -> bytes:
    """Read file content as bytes.

    Args:
        file_path: Path to input file

    Returns:
        File contents as bytes
    """
    with open(file_path, "rb") as file:
        return file.read()


def roi_csv_reader(reader: csv.reader, row_count: int) -> Iterator[list]:
    """Read CSV data as multiple rows .

    Args:
        reader: CSV reader object to read from
        row_count: Number of rows to include in each batch

    Yields:
        List of CSV rows as multiple rows of the specified row count
    """
    while True:
        rows = list(itertools.islice(reader, row_count))
        if not rows:
            break
        yield rows


def check_streamable(file_path: os.PathLike) -> bool:
    """
    Checks if the video is streamable by checking if the moov atom follows
    immediately after the ftyp atom in an MP4 file.

    For streamable MP4s, the moov atom must come immediately after:
    [4 bytes: size][4 bytes: "ftyp"][... ftyp data ...][4 bytes: size]
    [4 bytes: "moov"][... moov data ...]

    For non-streamable MP4s, other atoms like mdat may come between ftyp and
    moov:
    [4 bytes: size][4 bytes: "ftyp"][... ftyp data ...][4 bytes: size]
    [4 bytes: "mdat"][... mdat data ...][moov atom]

    Args:
        mp4_header_data: bytes of the first chunk of the MP4 file. Ideally we
            need to have at least 40 bytes to check.

    Returns:
        A tuple of (is_streamable, ftyp_size).
    """
    # Read first 40 bytes of the file
    with open(file_path, "rb") as f:
        mp4_header_data = f.read(40)
        if len(mp4_header_data) < 40:
            raise RuntimeError("MP4 file is too small to check if it is streamable")

    # Read the first atom size
    ftyp_size = int.from_bytes(mp4_header_data[0:4], byteorder="big")

    # Check if it's a ftyp atom
    if mp4_header_data[4:8] != b"ftyp":
        return False, -1

    next_atom_type = bytes(mp4_header_data[ftyp_size + 4 : ftyp_size + 8])

    # Check if the next atom is a moov atom
    if next_atom_type == b"moov":
        return True
    else:
        return False


def create_channel_credentials(args: argparse.Namespace) -> grpc.ChannelCredentials:
    """Create channel credentials based on SSL mode.

    Args:
        args: Command line arguments containing SSL configuration

    Returns:
        Configured channel credentials

    Raises:
        RuntimeError: If required SSL files are missing
    """
    channel_credentials = None
    if args.ssl_mode == "MTLS":
        if not (args.ssl_key and args.ssl_cert and args.ssl_root_cert):
            raise RuntimeError(
                "If --ssl-mode is MTLS, --ssl-key, --ssl-cert and " "--ssl-root-cert are required."
            )
        private_key = read_file_content(args.ssl_key)
        certificate_chain = read_file_content(args.ssl_cert)
        root_certificates = read_file_content(args.ssl_root_cert)
        channel_credentials = grpc.ssl_channel_credentials(
            root_certificates=root_certificates,
            private_key=private_key,
            certificate_chain=certificate_chain,
        )
    else:
        if not (args.ssl_root_cert):
            raise RuntimeError("If --ssl-mode is TLS, --ssl-root-cert is required.")
        root_certificates = read_file_content(args.ssl_root_cert)
        channel_credentials = grpc.ssl_channel_credentials(root_certificates=root_certificates)
    return channel_credentials


def create_protobuf_any_value(value: Union[bool, int, float, str]) -> any_pb2.Any:
    """Create a google.protobuf.Any message from a Python value.

    Args:
        value: The value to convert (bool, int, float, or str)

    Returns:
        google.protobuf.Any message
    """
    any_message = any_pb2.Any()

    if isinstance(value, bool):
        wrapper = wrappers_pb2.BoolValue(value=value)
        any_message.Pack(wrapper)
    elif isinstance(value, int):
        if value > 2147483647 or value < -2147483648:  # int32 range
            wrapper = wrappers_pb2.Int64Value(value=value)
        else:
            wrapper = wrappers_pb2.Int32Value(value=value)
        any_message.Pack(wrapper)
    elif isinstance(value, float):
        wrapper = wrappers_pb2.FloatValue(value=value)
        any_message.Pack(wrapper)
    elif isinstance(value, str):
        wrapper = wrappers_pb2.StringValue(value=value)
        any_message.Pack(wrapper)
    else:
        raise ValueError(f"Unsupported type: {type(value)}")

    return any_message
