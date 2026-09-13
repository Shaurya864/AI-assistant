"""
Audio control: mute/unmute speakers and microphone, and set volume.
Uses Windows' Core Audio API via pycaw.

Requires: pip install pycaw comtypes
"""

from ctypes import cast, POINTER


def _get_endpoint_volume(capture: bool = False):
    """
    Get the volume control interface for speakers (default) or mic
    (capture=True), talking to Windows' Core Audio API directly rather
    than through pycaw's AudioUtilities helper — that helper's return
    type varies across pycaw versions and caused compatibility issues.
    """
    from comtypes import CLSCTX_ALL, CoCreateInstance, GUID
    from pycaw.pycaw import IMMDeviceEnumerator, IAudioEndpointVolume

    CLSID_MMDeviceEnumerator = GUID("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
    enumerator = CoCreateInstance(CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, CLSCTX_ALL)

    # Windows API constants (stable across all versions):
    # EDataFlow: eRender=0 (speakers), eCapture=1 (microphone)
    # ERole: eMultimedia=1
    data_flow = 1 if capture else 0
    device = enumerator.GetDefaultAudioEndpoint(data_flow, 1)

    interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


def mute_speakers() -> str:
    try:
        volume = _get_endpoint_volume(capture=False)
        volume.SetMute(1, None)
        return "Muted."
    except ImportError:
        return "Audio control needs two more packages — run `pip install pycaw comtypes` first."
    except Exception as e:
        return f"Couldn't mute speakers: {e}"


def unmute_speakers() -> str:
    try:
        volume = _get_endpoint_volume(capture=False)
        volume.SetMute(0, None)
        return "Unmuted."
    except ImportError:
        return "Audio control needs two more packages — run `pip install pycaw comtypes` first."
    except Exception as e:
        return f"Couldn't unmute speakers: {e}"


def mic_off() -> str:
    try:
        volume = _get_endpoint_volume(capture=True)
        volume.SetMute(1, None)
        return "Microphone turned off."
    except ImportError:
        return "Audio control needs two more packages — run `pip install pycaw comtypes` first."
    except Exception as e:
        return f"Couldn't turn off the microphone: {e}"


def mic_on() -> str:
    try:
        volume = _get_endpoint_volume(capture=True)
        volume.SetMute(0, None)
        return "Microphone turned on."
    except ImportError:
        return "Audio control needs two more packages — run `pip install pycaw comtypes` first."
    except Exception as e:
        return f"Couldn't turn on the microphone: {e}"


def set_volume(percent: int) -> str:
    try:
        percent = max(0, min(100, percent))
        volume = _get_endpoint_volume(capture=False)
        volume.SetMasterVolumeLevelScalar(percent / 100, None)
        return f"Volume set to {percent}%."
    except ImportError:
        return "Audio control needs two more packages — run `pip install pycaw comtypes` first."
    except Exception as e:
        return f"Couldn't set volume: {e}"