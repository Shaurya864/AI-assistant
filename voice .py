"""
Optional voice I/O. Only imported/used if config.VOICE_ENABLED = True.
Uses faster-whisper for speech-to-text and piper-tts for text-to-speech.

Install (only needed if you want voice):
    pip install faster-whisper sounddevice numpy
    (Piper is a separate binary — see README for setup)
"""

import subprocess
import tempfile
import os

_whisper_model = None


def _add_nvidia_dll_dirs():
    """
    On Windows, pip-installed NVIDIA CUDA libraries (cublas, cudnn) sit
    inside Python's site-packages folder, not on the system PATH — so
    Windows can't find them by default. This explicitly tells Python
    where to look, using os.add_dll_directory (Python 3.8+, Windows only).
    """
    if os.name != "nt":
        return
    import importlib.util
    for pkg in ("nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_runtime", "nvidia.cufft"):
        try:
            spec = importlib.util.find_spec(pkg)
            if spec and spec.submodule_search_locations:
                base = list(spec.submodule_search_locations)[0]
                bin_dir = os.path.join(base, "bin")
                if os.path.isdir(bin_dir):
                    os.add_dll_directory(bin_dir)
        except Exception:
            pass


def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        _add_nvidia_dll_dirs()
        from faster_whisper import WhisperModel
        import numpy as np
        import config

        model_size = getattr(config, "WHISPER_MODEL", "base.en")
        device = getattr(config, "WHISPER_DEVICE", "cpu")

        if device == "cuda":
            try:
                candidate = WhisperModel(model_size, device="cuda", compute_type="float16")
                # Actually run a tiny test transcription — this is what
                # catches missing CUDA libraries (like cublas64_12.dll),
                # since just loading the model doesn't trigger that error.
                silence = np.zeros(16000, dtype=np.float32)  # 1 second of silence
                list(candidate.transcribe(silence, language="en")[0])
                _whisper_model = candidate
                print(f"[voice] Whisper loaded on GPU ({model_size}) — should be fast.")
            except Exception as e:
                print(f"[voice] GPU transcription test failed ({e}) — falling back to CPU.")
                _whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        else:
            _whisper_model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _whisper_model


def listen(duration: int = None) -> str:
    """Record from the mic for `duration` seconds and transcribe it."""
    import sounddevice as sd
    import numpy as np
    import config

    duration = duration or getattr(config, "LISTEN_DURATION", 5)
    samplerate = 16000
    print(f"Listening for {duration}s...")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype="float32")
    sd.wait()

    model = _load_whisper()
    segments, _ = model.transcribe(audio.flatten(), language="en")
    text = " ".join(seg.text for seg in segments).strip()
    return text


def speak(text: str):
    """
    Speak text aloud using Piper TTS, using the exact paths configured
    in config.py (no reliance on PATH — avoids common setup issues).
    """
    import config

    if not os.path.isfile(config.PIPER_EXE_PATH):
        print(f"[voice] Piper not found at {config.PIPER_EXE_PATH} — falling back to text only.")
        print(f"Jarvis: {text}")
        return

    if not os.path.isfile(config.PIPER_VOICE_PATH):
        print(f"[voice] Voice model not found at {config.PIPER_VOICE_PATH} — falling back to text only.")
        print(f"Jarvis: {text}")
        return

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        subprocess.run(
            [config.PIPER_EXE_PATH, "--model", config.PIPER_VOICE_PATH, "--output_file", wav_path],
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
        )

        if os.name == "nt":
            import winsound
            winsound.PlaySound(wav_path, winsound.SND_FILENAME)
        else:
            os.system(f'aplay {wav_path} 2>/dev/null || afplay {wav_path}')

        os.remove(wav_path)
    except subprocess.CalledProcessError as e:
        print(f"[voice] Piper failed to generate audio: {e.stderr}")
        print(f"Jarvis: {text}")
    except Exception as e:
        print(f"[voice] TTS failed ({e}) — falling back to text only.")
        print(f"Jarvis: {text}")