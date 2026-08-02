# NVIDIA AI for Media NIMs

NVIDIA AI for Media is a suite of high-performance, easy-to-use, NVIDIA Inference Microservices (NIMs) for deploying AI features that enhance audio, video, and augmented reality effects for video conferencing and tele-presence.


## NVIDIA AI for Media NIM Clients

This repository provides sample client applications to interact with NVIDIA AI for Media NIMs

- [`active-speaker-detection`](active-speaker-detection) - NVIDIA Active Speaker Detection feature uses state-of-the-art AI models to detect and identify active speakers within a video stream through the analysis of visual and diarized audio data.
[[Demo](https://build.nvidia.com/nvidia/active-speaker-detection)] , [[Docs](https://docs.nvidia.com/nim/maxine/active-speaker-detection/latest/index.html)]

- [`bnr`](bnr) - NVIDIA Background Noise Removal (BNR) model is an audio background noise removal model from NVIDIA. It removes a variety of background noises from audio recordings. It also retains emotive tones in speech, such as happy, sad, excited and angry tones.
[[Demo](https://build.nvidia.com/nvidia/bnr)] , [[Docs](https://docs.nvidia.com/nim/maxine/bnr/latest/index.html)]

- [`eye-contact`](eye-contact) - NVIDIA Eye Contact feature estimates the gaze angles of a person in a video and redirects the gaze in the output video to make it frontal.
[[Demo](https://build.nvidia.com/nvidia/eyecontact)] , [[Docs](https://docs.nvidia.com/nim/maxine/eye-contact/latest/index.html)]

- [`lipsync`](lipsync) - NVIDIA LipSync syncs lip movements in a video to match the provided speech audio, enhancing realism and accuracy in speech animation. Takes an audio and video input, generating a synchronized output video. [[Demo](https://build.nvidia.com/nvidia/lipsync)] , [[Docs](https://docs.nvidia.com/nim/maxine/lipsync/latest/index.html)]

- [`relighting`](relighting) - NVIDIA Relighting applies AI-powered HDR lighting effects to video streams. Supports streaming and transactional modes, multiple background modes, and a Python client.[[Demo](https://build.nvidia.com/nvidia/relighting)], [[Docs](https://docs.nvidia.com/nim/maxine/relighting/latest/index.html)]


- [`studio-voice`](studio-voice) - NVIDIA Studio Voice feature enhances the input speech recorded through low quality microphones in noisy and reverberant environments to studio-recorded quality speech.
[[Demo](https://build.nvidia.com/nvidia/studiovoice)] , [[Docs](https://docs.nvidia.com/nim/maxine/studio-voice/latest/index.html)]

- [`synthetic-video-detector`](synthetic-video-detector) - NVIDIA Synthetic Video Detector analyzes video files to detect whether they are synthetic (AI-generated) or real.
[[Demo](https://build.nvidia.com/nvidia/synthetic-video-detector)] , [[Docs](https://docs.nvidia.com/nim/maxine/synthetic-video-detector/latest/index.html)]

## NVIDIA AI for Media ST 2110 NIMs

For live IP video workflows, the following NIMs are designed to run with [NVIDIA Holoscan for Media](https://docs.nvidia.com/holoscan-for-media/latest/index.html) over SMPTE ST 2110. Each directory provides Helm charts and a sample client.

- [`st2110/active-speaker-detection`](st2110/active-speaker-detection) - NVIDIA Active Speaker Detection ST 2110 NIM analyzes video, audio, and diarization data to identify and track active speakers across frames in real-time live IP video workflows, returning per-frame speaker data including bounding boxes, speaker identifiers, active speaking state, and confidence scores.
[[Demo](https://build.nvidia.com/nvidia/active-speaker-detection)] , [[Docs](https://docs.nvidia.com/nim/maxine/active-speaker-detection-h4m/latest/index.html)]

- [`st2110/lipsync`](st2110/lipsync) - NVIDIA LipSync ST 2110 NIM processes video and speech inputs to generate lip movements synchronized with the input speech for real-time dubbing and localization workflows in live IP broadcast environments, with support for per-frame speaker bounding box metadata in multi-speaker scenes.
[[Demo](https://build.nvidia.com/nvidia/lipsync)] , [[Docs](https://docs.nvidia.com/nim/maxine/lipsync-h4m/latest/index.html)]

- [`st2110/studio-voice`](st2110/studio-voice) - NVIDIA Studio Voice ST 2110 NIM performs real-time AI-based speech enhancement over IP media networks, ingesting and publishing PCM audio over SMPTE ST 2110-30 to produce studio-recorded quality speech for live broadcast and production workflows.
[[Demo](https://build.nvidia.com/nvidia/studiovoice)] , [[Docs](https://docs.nvidia.com/nim/maxine/studio-voice-h4m/latest/index.html)]
