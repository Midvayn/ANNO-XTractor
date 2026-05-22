# ANNO XTractor

ANNO XTractor is a small local web tool for extracting screenshots and training frames from videos. It is useful for preparing reference images, AI datasets, LoRA training material, thumbnails, and general frame-based image collections.

The app uses FFmpeg as the primary extraction backend and can fall back to OpenCV when available.

## Features

- Upload a video through a local Gradio interface
- Extract every N-th frame
- Save extracted frames into a local output folder
- Preview extracted frames in a gallery
- Open the output folder directly from the UI
- Show basic system diagnostics
- FFmpeg-first workflow with optional OpenCV fallback
- Local-only processing

## Project Structure

```text
ANNO-XTractor/
├─ ANNO_XTractor.py
├─ Run_ANNO_XTractor.bat
├─ requirements.txt
├─ README.md
├─ LICENSE.txt
└─ .gitignore
```

## Installation

Install Python 3.10 or newer.

Install dependencies:

```bash
pip install -r requirements.txt
```

Install FFmpeg and make sure it is available in your system PATH.

Windows FFmpeg download:

```text
https://ffmpeg.org/download.html
```

## Running

On Windows, run:

```bat
Run_ANNO_XTractor.bat
```

Or run manually:

```bash
python ANNO_XTractor.py
```

The app will open a local Gradio interface in your browser.

## Basic Workflow

1. Upload a video.
2. Set `Extract every N-th frame`.
3. Keep `Save frames to a folder` enabled if you want permanent files.
4. Click `Extract frames`.
5. Review the generated frames in the gallery.
6. Click `Open frame folder` to view the saved screenshots.

Example output folder:

```text
frames_my_video/
├─ frame_00001.jpg
├─ frame_00002.jpg
├─ frame_00003.jpg
└─ ...
```

## Notes

- The app runs locally.
- FFmpeg is recommended for best compatibility.
- OpenCV is included as an optional fallback through `opencv-python`.
- Extracted frame folders are ignored by Git through `.gitignore`.
- Large videos can produce many files, so choose the frame step carefully.

## Credits

Powered by ChatGPT and ANNO
