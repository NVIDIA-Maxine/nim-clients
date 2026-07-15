
# NVIDIA LipSync NIM Client

This package has a sample client that demonstrates interaction with Nvidia LipSync NIM.

## Getting Started

NVIDIA NIM Client packages use gRPC APIs. The following instructions demonstrate the LipSync NIM by using a Python client.

## Prerequisites

Access to NVIDIA LipSync NIM container and service.

### Python 
- Ensure that you have Python 3.12 or later installed on your system. For download and installation instructions, see [Download Python](https://www.python.org/downloads/).

## Usage Guide

### 1. Clone the Repository

```bash
git clone https://github.com/nvidia-maxine/nim-clients.git

# Go to the 'lipsync' folder
cd nim-clients/lipsync/
```

### 2. Install Dependencies
#### Python
```bash
# Install all the required packages using requirements.txt file in python directory  
pip install -r requirements.txt
```

### 3. Compile the Protos

If you want to use the client code provided in the GitHub client repository, you can skip this step.

The proto files are available in the `lipsync/protos/proto` folder, organized into the following packages:
- `nvidia/ai4m/lipsync/v1/lipsync.proto`: Main LipSync service definition
- `nvidia/ai4m/audio/v1/audio.proto`: Audio codec definitions
- `nvidia/ai4m/video/v1/video.proto`: Video encoding definitions
- `nvidia/ai4m/common/v1/common.proto`: Common types (BoundingBox)

You can compile them to generate client interfaces in your preferred programming language. For more details, refer to [Supported languages](https://grpc.io/docs/languages/) in the gRPC documentation.

The following example shows how to compile the protos for Python on Linux.

#### Python

The `grpcio` version needed for compilation can be referred at `requirements.txt`

To compile protos on Linux, run the following commands:
```bash
# Go to lipsync/protos/linux/ folder
cd lipsync/protos/linux/

chmod +x compile_protos.sh
./compile_protos.sh
```

To compile protos on Windows, run the following commands:
``` bash
# Go to lipsync/protos/windows/ folder
cd lipsync/protos/windows/

./compile_protos.bat
```

The compiled proto files appear in the `nim-clients/lipsync/interfaces/nvidia/` directory, organized by package.


### 4. Host the NIM Server

Before running the client part of NVIDIA LipSync, set up a server.
The simplest way to do that is to follow the instructions in [Getting Started](https://docs.nvidia.com/nim/maxine/lipsync/latest/getting-started.html).

### 5. Run the Python Client
Go to the `scripts` directory.

```bash
cd scripts
```

#### Usage for Hosted NIM Request

```bash
python3 lipsync.py \
  --target <server_ip:port> \
  --video-input <input_video_file_path> \
  --audio-input <input_audio_file_path> \
  --output <output_file_path_and_name> \
  --ssl-mode <ssl_mode_value> \
  --ssl-key <ssl_key_file_path> \
  --ssl-cert <ssl_cert_filepath> \
  --ssl-root-cert <ssl_root_cert_filepath>
```

Running the Python client script with no arguments uses the default arguments. All arguments are listed in the [Command-Line Arguments](#command-line-arguments) table.


To view details of the command-line arguments, run the following command:
```bash
python3 lipsync.py -h
```

#### Example Command to Process the Packaged Sample Inputs

The following command uses the sample streamable video and audio input to generate a lip-synced video output file named `out.mp4` in the current folder:

```bash
python3 lipsync.py --target 127.0.0.1:8001 --video-input ../assets/sample_video_streamable.mp4 --audio-input ../assets/sample_audio.wav --output out.mp4 
```

#### Command-Line Arguments

| Argument | Default Value | Required? | Description |
|----------|---------------|-----------|-------------|
| `-h, --help` | n/a | Optional | Show help message and exit. |
| `--ssl-mode` | `DISABLED` | Optional | SSL mode (`DISABLED`, `MTLS`, or `TLS`). |
| `--ssl-key` | `../ssl_key/ssl_key_client.pem` | Optional | Path to SSL private key. Required if ssl-mode is `MTLS`. |
| `--ssl-cert` | `../ssl_key/ssl_cert_client.pem` | Optional | Path to SSL certificate chain. Required if ssl-mode is `MTLS`. |
| `--ssl-root-cert` | `../ssl_key/ssl_ca_cert.pem` | Optional | Path to SSL root certificate. Required if ssl-mode is `MTLS` or `TLS`. |
| `--target` | `127.0.0.1:8001` | Optional | IP:port of gRPC service. |
| `--video-input` | `../assets/sample_video.mp4` | Optional | Path to input video file (.mp4 format). |
| `--audio-input` | `../assets/sample_audio.wav` | Optional | Path to input audio file (.wav or .mp3 format). |
| `--speaker-data-input` | None | Optional | Path to speaker data JSON file. See [Speaker Data](#speaker-data-option). |
| `--extend-audio` | `unspecified` | Optional | Audio extension handling (`unspecified` or `silence`). |
| `--extend-video` | `unspecified` | Optional | Video extension handling (`unspecified`, `reverse`, or `forward`). |
| `--bitrate` | `30` | Optional | Output video bitrate in Mbps. Specify for lossy encoding. |
| `--idr-interval` | `8` | Optional | IDR frame interval for output video. Specify for lossy encoding. |
| `--lossless` | `False` | Optional | Enable lossless video encoding (overrides bitrate and IDR settings). |
| `--output` | `lipsync_output.mp4` | Optional | Path for output video file. |
| `--output-audio-codec` | `opus` | Optional | Audio codec for output video file (`opus` or `mp3`). |
| `--custom-encoding-params` | None | Optional | Custom encoding parameters as a JSON string. |
| `--head-movement-speed` | None | Optional | Speed of head movement in input video. `0` for static or slow, `1` for fast. |
| `--mix-background-audio` | `False` | Optional | Enable mixing background audio with the output. |
| `--background-audio-input` | None | Optional | Path to background audio file (WAV or MP3). Required when `--mix-background-audio` is set. |
| `--background-audio-volume` | `0.5` | Optional | Volume of background audio (0.0 to 1.0). |




#### Examples
- Get help on all available options:
```python lipsync.py -h```

- Run with default input video and audio files (uses default video and audio paths):
```python lipsync.py --target 127.0.0.1:8001```

- Run with a streamable video (enables streaming mode automatically):
```python lipsync.py --target 127.0.0.1:8001 --video-input ../assets/sample_video_streamable.mp4```

- Run with custom output path:
```python lipsync.py --target 127.0.0.1:8001 --output /path/to/output.mp4```

- Run with output audio codec set to mp3:
```python lipsync.py --target 127.0.0.1:8001 --output-audio-codec mp3```

- Run with speaker data:
```python lipsync.py --target 127.0.0.1:8001 --speaker-data-input /path/to/speaker_data.json```

- Run with background audio mixing:
```python lipsync.py --target 127.0.0.1:8001 --mix-background-audio --background-audio-input /path/to/background.wav --background-audio-volume 0.3```

- Run with SSL TLS security enabled:
```python lipsync.py --target 127.0.0.1:8001 --ssl-mode TLS --ssl-root-cert ../ssl_key/ssl_ca.crt```

- Run with SSL mutual TLS (mTLS) authentication:
```python lipsync.py --target 127.0.0.1:8001 --ssl-mode MTLS --ssl-key ../ssl_key/ssl_client.key --ssl-cert ../ssl_key/ssl_client.crt --ssl-root-cert ../ssl_key/ssl_ca.crt```


### 6. Important Usage Notes
#### Supported Formats
| Format Type | Supported Formats | Notes |
|-------------|-------------------|-------|
| **Video Input** | MP4 (H264 only) | Must be Constant Frame Rate (CFR). Variable Frame Rate (VFR) not supported. |
| **Audio Input** | WAV, MP3 | Format for input audio |
| **Video Output** | MP4 (H264 only, MP3/OPUS audio) | Generated with specified encoding parameters. |


#### Input Modes


The LipSync NIM provides two modes for processing input files: streaming and transactional.

##### Streaming Mode

Streaming mode is the recommended way to use LipSync NIM. It allows inference to begin without receiving the whole video from the client. It processes video frames incrementally, and inference begins as soon as the first frame of information is available. The output frames are streamed back to the client immediately after inference.

The NIM automatically detects streamable videos and enables streaming mode. This mode delivers the lowest latency, best resource efficiency, and scales well to large files.

Use streaming mode for:

- Best overall performance — the NIM is optimized for this path
- Streamable video inputs
- Applications that benefit from receiving output as it is generated, without waiting for the entire file to be uploaded
- Large video files that benefit from incremental processing and reduced disk I/O

| Aspect | Streaming Mode | Transactional Mode |
|--------|-------------------|----------------|
| **Data Storage** | Only frames being processed are temporarily copied in memory | Entire video and audio files are temporarily copied on disk |
| **Processing Start** | NIM starts processing as soon as data chunk for first frame arrives | NIM waits to receive entire files before starting |
| **Processing Timing** | Continuous processing without waiting for complete input | Processing begins after all data is received |
| **Output Delivery** | Output frames are generated and returned immediately | Complete output video is returned to client after inference is finished for whole video |

Streaming mode works with streamable videos where metadata is positioned at the beginning of the file. The NIM automatically detects streamable videos and enables streaming mode. Videos that are not streamable can be easily converted to a streamable format.

To convert your video into a streamable video, see [Convert a Video to Streamable Video with FFmpeg](#7-convert-a-video-to-streamable-video-with-ffmpeg).

You can then specify the streamable video as input to the NIM by using the `--video-input` parameter.
```bash
   python lipsync.py --target 127.0.0.1:8001 --video-input ../assets/sample_video_streamable.mp4 --audio-input ../assets/sample_audio.wav 
```

##### Transactional Mode

In transactional mode, the entire video and audio files have to be received by the NIM before processing can begin. The NIM falls back to this mode when the input video is not streamable.
This mode is suitable for:

- Videos that are not optimized for streaming (such as non-streamable MP4 files where metadata is located at the end of the file, requiring the entire file to be downloaded before playback can begin).
- Processing of small video and audio files where streaming overhead is unnecessary.
- Applications that can wait for complete processing before receiving output.

To run LipSync in transactional mode, provide a non-streamable video as input:
```bash
   python lipsync.py --target 127.0.0.1:8001 --video-input ../assets/sample_video.mp4  --audio-input ../assets/sample_audio.wav 
```

```{tip}
For best performance, convert your videos to a streamable format so that the NIM can use streaming mode. 
```


#### Configurable Options for the NIM
##### extend-video Option
When the input video duration is shorter than the audio duration, the LipSync NIM can extend the video using one of two methods: 
  - `unspecified` : No video extension is performed. The output video will only be as long as the input video, even if the audio is longer. This is the default behavior and results in the fastest processing time.
  - `reverse`: Plays the last 5 seconds of video frames in reverse order. This mode creates a smooth transition effect, although the reversed motion might appear unnatural in some scenes.
  - `forward`: Plays the last 5 seconds of video frames in forward order. This mode maintains visual consistency but might appear repetitive over time.

This parameter can be useful when working with content in which the audio track extends beyond the video duration, such as when adding voiceovers or dubbing content.

The following example command extends a 20-second sample video in reverse to match the 30 seconds of audio:
```bash
python lipsync.py --target=127.0.0.1:8001 --extend-video reverse --video-input ../assets/sample_video_streamable_20s.mp4
```

> **Note:** <span style="color:red">Video extension operations can significantly increase processing time and memory usage. This is because the LipSync service needs to cache video frames in memory. Because raw frames are very large, they are stored as PNG files in memory, which require additional encoding and decoding steps.</span>


##### extend-audio Option
When the input audio duration is shorter than the video duration, the LipSync NIM can extend the audio with silence. 
  - `unspecified` : No audio extension is performed. The output video will only be as long as the input audio, even if the input video is longer. This is the default behavior.
  - `silence`: Extends the audio by adding silence at the end until it matches the video duration. This mode ensures that audio and video remain synchronized while maintaining the original audio content.

This parameter can be useful when working with content in which the video track extends beyond the audio duration, such as when processing silent video segments or incomplete audio recordings or when synchronizing content with varying durations.

The following example command extends 20 seconds of sample audio with silence to match the 30-second video:
```bash
python lipsync.py --target=127.0.0.1:8001 --extend-audio silence --audio-input ../assets/sample_audio_20s.wav
```

##### Encoding Options
- `lossless`: Enables lossless video encoding. This setting overrides any bitrate configuration to ensure maximum quality output, although it results in larger file sizes. Use this mode when quality is the top priority. 
   ```bash
   python lipsync.py --target 127.0.0.1:8001 --lossless
   ```

- `bitrate`: Sets the target bitrate for video encoding in megabits per second (Mbps). Higher bitrates result in better video quality but larger file sizes. The default is 30 Mbps. For example, setting `--bitrate 5` targets 5 Mbps encoding.
   ```bash
   python lipsync.py --target 127.0.0.1:8001 --bitrate 5
   ```

- `idr-interval`: Sets the interval between instantaneous decoding refresh (IDR) frames in the encoded video. IDR frames are special I-frames that clear all reference buffers, allowing the video to be decoded from that point without needing previous frames. Lower values improve seeking accuracy, random access, and overall encoding quality but increase file size; higher values reduce file size but can impact seeking performance and quality. The default is 8 frames.
   ```bash
   python lipsync.py --target 127.0.0.1:8001 --idr-interval 10
   ```

- `custom-encoding-params`: Passes custom encoding parameters as a JSON string, which provides fine-grained control for expert users via JSON configuration. These parameters are used to configure properties of the GStreamer nvvideo4linux2 encoder plugin, allowing direct control over the underlying hardware encoder settings.
   ```bash
   python lipsync.py --custom-encoding-params '{"idrinterval": 20, "maxbitrate": 3000000}'
   ```

**Note:** <span style="color:red">Custom encoding parameters are for expert users who need fine-grained control over video encoding. Incorrect values can cause encoding failures or poor-quality output. To configure the nvenc encoder, refer to [Gst properties of the Gst-nvvideo4linux2 encoder plugin](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_plugin_gst-nvvideo4linux2.html#:~:text=The%20following%20table%20summarizes%20the%20Gst%20properties%20of%20the%20Gst%2Dnvvideo4linux2%20encoder%20plugin).</span>

##### Speaker Data Option
The speaker data JSON file provides per-frame bounding box and speaker metadata so that the LipSync NIM can target specific facial regions rather than relying on automatic face detection.

```bash
python lipsync.py --target 127.0.0.1:8001 --video-input ../assets/sample_video_streamable.mp4 --audio-input ../assets/sample_audio.wav --speaker-data-input ../assets/sample_speaker_data.json
```

###### JSON File Format for Speaker Data

The JSON file must have the following structure:

```json
{
  "frames": [
    {
      "speakers": [
        {
          "bbox": [186, 191, 175, 254],
          "speaker_id": 1,
          "is_speaking": false
        },
        {
          "bbox": [815, 188, 263, 357],
          "speaker_id": 2,
          "is_speaking": true
        }
      ]
    },
    {
      "speakers": [
        {
          "bbox": [188, 191, 174, 254],
          "speaker_id": 1,
          "is_speaking": false
        }
      ],
      "bypass": false
    }
  ]
}
```

**Top Level:**
- `frames`: An array of objects, one per video frame, in frame order. Additional top-level fields are ignored by the client.

**Each Frame Object**
- `speakers`: An array of speaker entries for that frame. If empty or absent, the server auto-detects faces for that frame.
- `bypass`: (Optional) Boolean indicating whether to skip lip sync processing for this frame. If `true`, the original video frame is passed through unchanged. If `false` or absent, lip sync is applied normally.

**Each Speaker Entry in `speakers`**
- `bbox`: An array of 4 numbers `[x, y, width, height]` defining the bounding box of the speaker's face in pixel coordinates.
  - `x`: X-coordinate of the top-left corner.
  - `y`: Y-coordinate of the top-left corner.
  - `width`: Width of the bounding box.
  - `height`: Height of the bounding box.
- `speaker_id`: Integer identifier for tracking this speaker across frames.
- `is_speaking`: Boolean indicating whether this speaker is currently speaking.

The client reads all frames from the JSON file and sends them to the LipSync NIM in batches alongside the video and audio data.

##### Background Audio Mixing
The LipSync NIM supports mixing a separate background audio track into the output video. This is useful for preserving ambient sounds, music, or other background audio that should accompany the lip-synced output.

```bash
python lipsync.py --target 127.0.0.1:8001 --mix-background-audio --background-audio-input /path/to/background.wav --background-audio-volume 0.3
```

- `--mix-background-audio`: Enables background audio mixing.
- `--background-audio-input`: Path to the background audio file (WAV or MP3 format).
- `--background-audio-volume`: Controls the volume of the background audio relative to its original level (0.0 = silent, 1.0 = full volume). Default is 0.5.

> **Note:** The background audio and the speech audio must have the same sample rate.

##### Head Movement Speed
The `--head-movement-speed` option controls how the NIM handles head movement in the input video:
- `0`: Optimized for static or slow-moving heads.
- `1`: Optimized for fast-moving heads.

```bash
python lipsync.py --target 127.0.0.1:8001 --head-movement-speed 0
```


> **Note**: **For an interactive experience and to explore all the configuration options described above, you can use the provided Jupyter notebook that demonstrates comprehensive LipSync NIM functionality. The notebook is located at [`notebook/lipsync_notebook.ipynb`](notebook/lipsync_notebook.ipynb) and can be run directly within your VS Code editor or any Jupyter environment.**

##### Language Model Selection
The LipSync NIM ships a generic, language-agnostic model (default) plus fine-tuned models for German, Spanish, and French. The model is chosen when the NIM container is launched, using the `NIM_TAGS_SELECTOR` environment variable. There is no client-side language option.

```bash
# Generic, language-agnostic model (default): omit NIM_TAGS_SELECTOR
docker run ... nvcr.io/nim/nvidia/lipsync:latest

# Language-specific model (de, es, or fr):
docker run ... -e NIM_TAGS_SELECTOR="language=de" nvcr.io/nim/nvidia/lipsync:latest
```

Only `de`, `es`, and `fr` are supported. Any other values causes the container to fail at startup; omit the variable to use the generic model. For details, see [Getting Started](https://docs.nvidia.com/nim/maxine/lipsync/latest/getting-started.html).

> **Note:** Language selection is a server-side deployment setting. No client-side changes are required.


##### Lipsync Debug Mode
The LipSync NIM includes a debug mode that provides visual feedback during processing. When enabled, this mode overlays diagnostic information on each output frame, making it easier to verify effect behavior and troubleshoot issues.

To enable debug mode, set the environment variable `LIPSYNC_DEBUG_MODE=1` when launching the NIM container:

```bash
docker run -it --rm --name=lipsync-nim \
  --runtime=nvidia \
  --gpus=all \
  --shm-size=8GB \
  -e NGC_API_KEY=$NGC_API_KEY \
  -e LIPSYNC_DEBUG_MODE=1 \
  -p 8000:8000 \
  -p 8001:8001 \
  nvcr.io/nim/nvidia/lipsync:latest
```

When debug mode is enabled, the following overlays appear on each frame:

| Overlay | Description |
|---------|-------------|
| **Frame number** | Displayed at the top-center of each frame with a white background. |
| **LipSync effect status** | A `LIPSYNC ON` or `LIPSYNC OFF` indicator below the frame number. The background is green when the effect is active and red when it is bypassed. |
| **Activation bounding box** | A square bounding box showing where the LipSync effect is being applied. The box is green when the effect is active (strength > 0) and red when bypassed (strength = 0). Box coordinates and dimensions are labeled above the box. |
| **Speaker bounding boxes** | White bounding boxes for each speaker, shown only when speaker data is provided via `--speaker-data-input`. Each box is labeled with a speaker identifier (e.g., `S0`, `S1`) and shows `[speaking]` when the speaker is actively speaking. |

Debug mode is useful for:
- Verifying that speaker bounding boxes are correctly positioned.
- Confirming that the LipSync effect is being applied to the intended regions.
- Troubleshooting cases where the effect appears inactive or misaligned.

> **Note:** Debug mode is a server-side configuration. No client-side changes are required — the debug overlays are rendered directly onto the output video frames returned to the client.


### 7. Convert a Video to Streamable Video with FFmpeg
1. Install FFmpeg:
   - On Ubuntu or Debian, run the following commands:
     ```bash
     sudo apt update
     sudo apt install ffmpeg
     ```
   - On Windows:
     Download the installer from [Download FFmpeg](https://ffmpeg.org/download.html).

2. Convert video to streamable format:
   ```bash
   ffmpeg -i input.mp4 -movflags +faststart output_streamable.mp4
   ```

   The `-movflags +faststart` flag moves the video metadata to the beginning of the file, allowing it to start playing before the entire file is downloaded.


For more information, see the [NVIDIA LipSync NIM](https://docs.nvidia.com/nim/maxine/lipsync/latest/index.html) documentation.
