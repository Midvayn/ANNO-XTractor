# ANNO XTractor
# Local video frame extraction tool using FFmpeg, with optional OpenCV fallback.

import sys
import subprocess
import shutil
import os
import tempfile
import json
from fractions import Fraction


def check_ffmpeg():
    """Check whether FFmpeg is available in PATH."""
    return shutil.which("ffmpeg") is not None


def install_package(package):
    """Install a Python package through pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except Exception:
        return False


# Dependency check
required_modules = ["gradio", "PIL"]
missing = []

for mod in required_modules:
    try:
        if mod == "PIL":
            from PIL import Image
        else:
            __import__(mod)
    except ImportError:
        missing.append(mod if mod != "PIL" else "pillow")

if missing:
    print(f"Missing modules: {', '.join(missing)}")
    print(f"Install them with: pip install {' '.join(missing)}")
    exit(1)


# Main imports
import gradio as gr
from PIL import Image


def _safe_fps(rate):
    """Parse FFmpeg frame-rate strings such as '30000/1001' safely."""
    try:
        return float(Fraction(rate))
    except Exception:
        return 0.0


def extract_frames_ffmpeg(video_path, step=30, save_permanent=True):
    """Extract frames with FFmpeg."""
    if video_path is None:
        return [], "No video selected", ""

    if not check_ffmpeg():
        return [], (
            "FFmpeg was not found. Install FFmpeg:\n"
            "Windows: https://ffmpeg.org/download.html\n"
            "Ubuntu: sudo apt install ffmpeg\n"
            "macOS: brew install ffmpeg"
        ), ""

    try:
        step = max(1, int(step))

        if save_permanent:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = os.path.join(os.getcwd(), f"frames_{video_name}")
            os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = tempfile.mkdtemp()

        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-select_streams", "v:0", video_path,
        ]

        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return [], "Could not read video information", ""

        video_info = json.loads(result.stdout)
        stream = video_info["streams"][0]

        output_pattern = os.path.join(output_dir, "frame_%05d.jpg")

        extract_cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"select='not(mod(n\\,{step}))'",
            "-vsync", "vfr", "-q:v", "2", output_pattern, "-y",
        ]

        result = subprocess.run(extract_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return [], f"FFmpeg error: {result.stderr}", ""

        frames = []
        for filename in sorted(os.listdir(output_dir)):
            if filename.startswith("frame_") and filename.endswith(".jpg"):
                frames.append(os.path.join(output_dir, filename))

        if not frames:
            return [], "No frames were extracted", ""

        duration = float(stream.get("duration", 0) or 0)
        fps = _safe_fps(stream.get("r_frame_rate", "0/1"))
        width = stream.get("width", "unknown")
        height = stream.get("height", "unknown")

        status = f"Extracted {len(frames)} frames, every {step} frame(s)\n"
        status += f"Duration: {duration:.1f}s, FPS: {fps:.1f}\n"
        status += f"Resolution: {width}x{height}\n"

        if save_permanent:
            status += f"Saved to: {output_dir}"
            save_path = output_dir
        else:
            status += "Temporary files will be removed after closing"
            save_path = ""

        return frames, status, save_path

    except Exception as e:
        return [], f"Error: {str(e)}", ""


def extract_frames_opencv_fallback(video_path, step=30, save_permanent=True):
    """Try OpenCV as a fallback extractor."""
    try:
        import cv2

        if video_path is None:
            return [], "No video selected", ""

        step = max(1, int(step))

        if save_permanent:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            output_dir = os.path.join(os.getcwd(), f"frames_{video_name}")
            os.makedirs(output_dir, exist_ok=True)
        else:
            output_dir = tempfile.mkdtemp()

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return [], "OpenCV cannot open this video", ""

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        count = 0
        frame_idx = 0
        frames = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if count % step == 0:
                frame_path = os.path.join(output_dir, f"frame_{frame_idx:05d}.jpg")
                cv2.imwrite(frame_path, frame)
                frames.append(frame_path)
                frame_idx += 1

            count += 1

        cap.release()

        duration = total_frames / fps if fps > 0 else 0
        status = f"OpenCV extracted {len(frames)} frames, every {step} frame(s)\n"
        status += f"Duration: {duration:.1f}s, FPS: {fps:.1f}\n"

        if save_permanent:
            status += f"Saved to: {output_dir}"
            save_path = output_dir
        else:
            status += "Temporary files will be removed after closing"
            save_path = ""

        return frames, status, save_path

    except ImportError:
        return [], "OpenCV is not installed", ""
    except Exception as e:
        return [], f"OpenCV error: {str(e)}", ""


def extract_frames(video_path, step=30, save_permanent=True):
    """Main frame extraction function."""
    frames, status, save_path = extract_frames_ffmpeg(video_path, step, save_permanent)

    if not frames and "FFmpeg was not found" not in status:
        frames, status, save_path = extract_frames_opencv_fallback(video_path, step, save_permanent)

    return frames, status


def clear_gallery():
    return [], "Gallery cleared"


def open_folder(folder_path):
    """Open the output folder in the system file manager."""
    if not folder_path or not os.path.exists(folder_path):
        return "Folder not found"

    try:
        if os.name == "nt":
            os.startfile(folder_path)
        elif os.name == "posix":
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", folder_path])
        return f"Opened folder: {folder_path}"
    except Exception as e:
        return f"Could not open folder: {str(e)}"


def get_system_info():
    """Return system information for diagnostics."""
    info = []
    info.append(f"Python: {sys.version}")
    info.append(f"FFmpeg: {'Found' if check_ffmpeg() else 'Not found'}")

    try:
        import cv2
        info.append(f"OpenCV: {cv2.__version__}")
    except ImportError:
        info.append("OpenCV: Not installed")

    return "\n".join(info)


# GUI
with gr.Blocks(title="ANNO XTractor") as demo:
    gr.Markdown("## 🎬 ANNO XTractor")
    gr.Markdown("Local video frame extractor for AI datasets, screenshots, references, and LoRA training material.")

    with gr.Row():
        with gr.Column():
            video_input = gr.Video(label="Upload video")
            step_input = gr.Number(
                value=30,
                label="Extract every N-th frame",
                precision=0,
                minimum=1,
                maximum=1000,
            )
            save_permanent_checkbox = gr.Checkbox(
                value=True,
                label="Save frames to a folder",
                info="If disabled, extracted frames will be temporary.",
            )

            with gr.Row():
                extract_btn = gr.Button("Extract frames", variant="primary")
                clear_btn = gr.Button("Clear", variant="secondary")
                info_btn = gr.Button("System info")

        with gr.Column():
            output_text = gr.Textbox(label="Status", lines=5, interactive=False)
            folder_path = gr.Textbox(label="Frame output folder", visible=False)
            open_folder_btn = gr.Button("Open frame folder", visible=False)

    gallery = gr.Gallery(
        label="Extracted frames",
        show_label=True,
        columns=4,
        rows=2,
        height="auto",
    )

    def extract_and_show_folder(video_path, step, save_permanent):
        frames, status = extract_frames(video_path, step, save_permanent)

        if save_permanent and video_path:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            save_path = os.path.join(os.getcwd(), f"frames_{video_name}")
            show_folder_btn = True
        else:
            save_path = ""
            show_folder_btn = False

        return (
            frames,
            status,
            gr.update(value=save_path, visible=show_folder_btn),
            gr.update(visible=show_folder_btn),
        )

    extract_btn.click(
        fn=extract_and_show_folder,
        inputs=[video_input, step_input, save_permanent_checkbox],
        outputs=[gallery, output_text, folder_path, open_folder_btn],
    )

    clear_btn.click(
        fn=clear_gallery,
        outputs=[gallery, output_text],
    )

    info_btn.click(
        fn=get_system_info,
        outputs=output_text,
    )

    open_folder_btn.click(
        fn=open_folder,
        inputs=folder_path,
        outputs=output_text,
    )


if __name__ == "__main__":
    demo.launch()

# Powered by ChatGPT and ANNO
