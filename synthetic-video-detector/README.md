# NVIDIA Synthetic Video Detector NIM Client

This folder contains the sample Python clients for the NVIDIA Synthetic Video Detector NIM, which analyzes video files to detect whether they are synthetic (AI-generated) or real.

Two client versions are provided because the NIM ships in two mutually incompatible gRPC API generations:

| Client | gRPC API | Use it for |
|--------|----------|------------|
| [v1](docs/v1.md) | `nvidia.maxine.syntheticvideodetector.v1` | The NVCF-hosted [Try API](https://build.nvidia.com/nvidia/synthetic-video-detector/api) and v1 self-hosted servers. Supports `--preview-mode` (NVCF). |
| [v2](docs/v2.md) | `nvidia.ai4m.syntheticvideodetector.v1` | A v2 self-hosted NIM. Supports self-hosted gRPC (insecure/SSL) plus pre-signed S3 URL ingest. No NVCF/Try API. |

The two APIs are **not cross-compatible**. Pointing a client at the wrong server generation fails fast with a gRPC `UNIMPLEMENTED` error and a message telling you which client to use.

## Folder layout

```
synthetic-video-detector/
  assets/                  # sample videos shared by both clients
  requirements.txt         # shared Python dependencies
  LICENSE.md               # shared license
  docs/
    v1.md                  # v1 usage guide
    v2.md                  # v2 usage guide
  protos/                  # both API generations, split by namespace
    proto/nvidia/maxine/   # v1 API
    proto/nvidia/ai4m/     # v2 API (service + shared ingest proto)
    linux/                 # compile_protos.sh (compiles both)
    windows/               # compile_protos.bat (compiles both)
  interfaces/              # generated stubs, mirroring the proto packages
    nvidia/maxine/syntheticvideodetector/v1/
    nvidia/ai4m/syntheticvideodetector/v1/
    nvidia/ai4m/ingest/v1/
  scripts/
    v1/                    # v1 client
    v2/                    # v2 client
  notebook/
    v1/                    # v1 notebook
    v2/                    # v2 notebook
```

`assets/`, `requirements.txt`, `LICENSE.md`, `protos/`, and `interfaces/` are shared; only the client code under `scripts/` and `notebook/` is version-specific.

Because each generation lives in its own protobuf package (`nvidia.maxine` vs `nvidia.ai4m`), the generated stubs sit in separate Python packages under a single `interfaces/` tree and never collide. Each client imports the generation it targets explicitly, for example:

```python
# v1 client
from nvidia.maxine.syntheticvideodetector.v1 import syntheticvideodetector_pb2

# v2 client
from nvidia.ai4m.syntheticvideodetector.v1 import syntheticvideodetector_pb2
```

## Quick start

Install the shared dependencies once from this folder, then run the client for your server generation:

```bash
# from this folder
pip install -r requirements.txt

# v2 self-hosted server
cd scripts/v2
python3 synthetic-video-detector.py --target <server_ip:port>

# or the v1 / NVCF Try API client
cd scripts/v1
python3 synthetic-video-detector.py --target <server_ip:port>
```

See [docs/v1.md](docs/v1.md) and [docs/v2.md](docs/v2.md) for the full usage guides, command-line arguments, and examples.

## License

See [LICENSE.md](LICENSE.md) for license information.
