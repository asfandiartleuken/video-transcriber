"""Exercise frozen imports, tool execution, Tcl/Tk, and multiprocessing offline."""
import json
import multiprocessing as mp
import subprocess
import sys
from pathlib import Path


def _worker(result_queue):
    import whisper
    import torch
    from whisper.audio import mel_filters

    # This reads Whisper's bundled mel_filters.npz without downloading a model.
    filters = mel_filters(torch.device("cpu"), 80)
    result_queue.put(list(filters.shape))


def run_smoke_test():
    import customtkinter
    import certifi
    import tkinter as tk
    from utils.media import ensure_dependencies, get_tool_binary, get_yt_dlp_command

    ensure_dependencies()
    assert Path(certifi.where()).is_file(), "Missing CA certificates"
    assert tk.Tcl().eval("info patchlevel"), "Missing Tcl runtime"
    for tool in ("ffmpeg", "ffprobe"):
        binary = get_tool_binary(tool)
        if not binary:
            raise RuntimeError(f"Missing bundled {tool}")
        subprocess.run([binary, "--version" if tool == "yt-dlp" else "-version"],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    subprocess.run([*get_yt_dlp_command(), "--version"], check=True, timeout=60)
    ctx = mp.get_context("spawn")
    results = ctx.Queue()
    worker = ctx.Process(target=_worker, args=(results,))
    worker.start()
    try:
        shape = results.get(timeout=120)
        worker.join(timeout=15)
        if worker.exitcode != 0 or shape != [80, 201]:
            raise RuntimeError(f"Whisper worker failed: {worker.exitcode}, {shape}")
    finally:
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=5)
        results.close()
    # Windowed Windows builds have no console: the report is the success signal.
    report = Path(sys.argv[sys.argv.index("--smoke-test") + 1])
    report.write_text(json.dumps({"ok": True, "platform": sys.platform}), encoding="utf-8")
