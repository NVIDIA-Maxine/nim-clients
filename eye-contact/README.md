
# NVIDIA Maxine Eye Contact NIM Client

This package has a sample client which demonstrates interaction with a Maxine Eye Contact NIM

## Getting Started

NVIDIA Maxine NIM Client packages use gRPC APIs. Instructions below demonstrate usage of Eye contact NIM using Python gRPC client.
To experience the NVIDIA Maxine Eye Contact NIM API without having to host your own servers, use the [Try API](https://build.nvidia.com/nvidia/eyecontact/api) feature, which uses the NVIDIA Cloud Function backend.

## Pre-requisites

- Ensure you have Python 3.10 or above installed on your system.
For download and installation instructions, refer to the [Python documentation](https://www.python.org/downloads/).
- Access to NVIDIA Maxine Eye Contact NIM container and service.
- MP4 input files with H.264 video codec (audio optional) and videos with Variable Frame Rate (VFR) are not supported.

## Usage guide

### 1. Clone the repository

```bash
git clone https://github.com/nvidia-maxine/nim-clients.git

// Go to the 'eye-contact' folder
cd nim-clients/eye-contact
```

### 2. Install dependencies

```bash
sudo apt-get install python3-pip
pip install -r requirements.txt
```

### 3. Compile the Protos (optional)

If you want to use the client code provided in the github Client repository, you can skip this step.
The proto files are available in the eye-contact/protos folder. You can compile them to generate client interfaces in your preferred programming language. For more details, refer to [Supported languages](https://grpc.io/docs/languages/) in the gRPC documentation.

Here is an example of how to compile the protos for Python on Linux and Windows.

#### Python

The `grpcio` version needed for compilation can be referred at `requirements.txt`

To compile protos on Linux, run:
```bash
# Go to eye-contact/protos/linux folder
cd eye-contact/protos/linux/

chmod +x compile_protos.sh
./compile_protos.sh
```

To compile protos on Windows, run:
```bash
# Go to eye-contact/protos/windows folder
cd eye-contact/protos/windows/

./compile_protos.bat
```
The compiled proto files will be generated in `nim-clients/eye-contact/interfaces` directory.

### 4. Host the NIM Server

Before running client part of Maxine Eye Contact, please set up a server.
The simplest way to do that is to follow the [quick start guide](https://docs.nvidia.com/nim/maxine/eye-contact/latest/index.html)
This step can be skipped when using [Try API](https://build.nvidia.com/nvidia/eyecontact/api).

### 5. Run the Python Client

- Go to the scripts directory

```bash
    cd scripts
```

#### Usage for Hosted NIM request

```bash
python eye-contact.py \
  --target <server_ip:port> \
  --input <input_file_path> \
  --output <output_file_path_and_name> \
  --ssl-mode <ssl_mode_value> \
  --ssl-key <ssl_key_file_path> \
  --ssl-cert <ssl_cert_filepath> \
  --ssl-root-cert <ssl_root_cert_filepath>
 ```

The following command uses the sample video file and generates an `output.mp4` file in the current folder:

   ```bash
   python eye-contact.py --target 127.0.0.1:8001 --input ../assets/transactional.mp4 --output output.mp4
   ```

The following command uses streaming mode (for streamable video files):

   ```bash
   python eye-contact.py --target 127.0.0.1:8001 --input ../assets/streamable.mp4 --output output.mp4 --streaming
   ```

> **Note:** The supported file type is MP4.

#### Usage for Preview API request

```bash
    python eye-contact.py --preview-mode \
    --target grpc.nvcf.nvidia.com:443 \
    --function-id 15c6f1a0-3843-4cde-b5bc-803a4966fbb6 \
    --api-key $API_KEY_REQUIRED_IF_EXECUTING_OUTSIDE_NGC \
    --input <input file path> \
    --output <output file path and the file name>
```

#### Command line arguments

-  `-h, --help` show this help message and exit
-  `--preview-mode` Flag to send request to preview NVCF NIM server on https://build.nvidia.com/nvidia/eyecontact/api.
-  `--ssl-mode` {DISABLED,MTLS,TLS} Flag to set SSL mode, default is DISABLED
-  `--ssl-key SSL_KEY`  The path to ssl private key.
-  `--ssl-cert SSL_CERT`    The path to ssl certificate chain.
-  `--ssl-root-cert`    The path to ssl root certificate.
-  `--target`   IP:port of gRPC service, when hosted locally. Use grpc.nvcf.nvidia.com:443 when hosted on NVCF.
-  `--input`    The path to the input video file.
-  `--output`   The path for the output video file.
-  `--streaming` Flag to enable gRPC streaming mode. Required for streamable video input.
-  `--api-key`  NGC API key required for authentication, utilized when using TRY API ignored otherwise
-  `--function-id`  NVCF function ID for the service, utilized when using TRY API ignored otherwise

#### Advanced Configuration Parameters

The Eye Contact client supports extensive parameter customization for fine-tuning behavior:

**Video Encoding Parameters**

- `lossless`: Enables lossless video encoding. This setting overrides any bitrate configuration to ensure maximum quality output, although it results in larger file sizes. Use this mode when quality is the top priority.
   ```bash
   python eye-contact.py --target 127.0.0.1:8001 --lossless
   ```

- `bitrate`: Sets the target bitrate for video encoding in bits per second (bps). Higher bitrates result in better video quality but larger file sizes. This parameter allows balancing quality and file size by controlling the video bitrate. The default is 3,000,000 bps (3 Mbps). For example, setting `--bitrate 5000000` targets 5 Mbps encoding.
   ```bash
   python eye-contact.py --target 127.0.0.1:8001 --bitrate 5000000
   ```

- `idr-interval`: Sets the interval between instantaneous decoding refresh (IDR) frames in the encoded video. IDR frames are special I-frames that clear all reference buffers, allowing the video to be decoded from that point without needing previous frames. Lower values improve seeking accuracy, random access, and overall encoding quality but increase file size; higher values reduce file size but may impact seeking performance and quality. The default is 8 frames.
   ```bash
   python eye-contact.py --target 127.0.0.1:8001 --idr-interval 10
   ```

- `custom-encoding-params`: Passes custom encoding parameters as a JSON string, which provides fine-grained control for expert users via JSON configuration. These parameters are used to configure properties of the GStreamer nvvideo4linux2 encoder plugin, allowing direct control over the underlying hardware encoder settings.
   ```bash
   python eye-contact.py --custom-encoding-params '{"idrinterval": 20, "maxbitrate": 3000000}'
   ```

**Note:** Custom encoding parameters are for expert users who need fine-grained control over video encoding. Incorrect values can cause encoding failures or poor-quality output. To configure the nvenc encoder, refer to [Gst properties of the Gst-nvvideo4linux2 encoder plugin](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvvideo4linux2.html#:~:text=The%20following%20table%20summarizes%20the%20Gst%20properties%20of%20the%20Gst%2Dnvvideo4linux2%20encoder%20plugin).

**Eye Contact Behavior Parameters**
-  `--temporal` Flag to control temporal filtering (default: 4294967295).
-  `--detect-closure` Flag to toggle detection of eye closure and occlusion (default: 0, choices: [0, 1]).
-  `--eye-size-sensitivity` Eye size sensitivity parameter (default: 3, range: [2, 6]).
-  `--enable-lookaway` Flag to toggle look away (default: 0, choices: [0, 1]).
-  `--lookaway-max-offset` Maximum value of gaze offset angle (degrees) during a random look away (default: 5, range: [1, 10]).
-  `--lookaway-interval-min` Minimum number of frames at which random look away occurs (default: 100, range: [1, 600]).
-  `--lookaway-interval-range` Range for picking the number of frames at which random look away occurs (default: 250, range: [1, 600]).

**Gaze Threshold Parameters**
-  `--gaze-pitch-threshold-low` Gaze pitch threshold (degrees) at which the redirection starts transitioning (default: 20.0, range: [10, 35]).
-  `--gaze-pitch-threshold-high` Gaze pitch threshold (degrees) at which the redirection is equal to estimated gaze (default: 30.0, range: [10, 35]).
-  `--gaze-yaw-threshold-low` Gaze yaw threshold (degrees) at which the redirection starts transitioning (default: 20.0, range: [10, 35]).
-  `--gaze-yaw-threshold-high` Gaze yaw threshold (degrees) at which the redirection is equal to estimated gaze (default: 30.0, range: [10, 35]).

**Head Pose Threshold Parameters**
-  `--head-pitch-threshold-low` Head pose pitch threshold (degrees) at which the redirection starts transitioning away from camera toward estimated gaze (default: 15.0, range: [10, 35]).
-  `--head-pitch-threshold-high` Head pose pitch threshold (degrees) at which the redirection is equal to estimated gaze (default: 15.0, range: [10, 35]).
-  `--head-yaw-threshold-low` Head pose yaw threshold (degrees) at which the redirection starts transitioning (default: 15.0, range: [10, 35]).
-  `--head-yaw-threshold-high` Head pose yaw threshold (degrees) at which the redirection is equal to estimated gaze (default: 15.0, range: [10, 35]).

#### Important Notes about Streaming Mode

Streaming mode (`--streaming`) is required when processing videos that are optimized for streaming (that is, they have the 'moov' atom at the beginning).

If you encounter an error when processing non-streamable video files, you can convert your video to be streamable using the following command:
  ```bash
  ffmpeg -i input.mp4 -movflags +faststart output_streamable.mp4
  ```
The client automatically validates video compatibility with the selected mode and provides helpful error messages.

When using SSL mode, the default path for the credentials is `../ssl_key/<filename>.pem`.

For more information, refer to [Basic Inference](https://docs.nvidia.com/nim/maxine/eye-contact/latest/basic-inference.html) in the Eye Contact NIM documentation.
