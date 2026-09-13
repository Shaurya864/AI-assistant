"""
Full system/hardware status: battery, CPU, RAM, storage, network speed,
and GPU (via nvidia-smi, which ships with your NVIDIA driver).
"""

import psutil
import subprocess
import time


def battery_status() -> str:
    battery = psutil.sensors_battery()
    if battery is None:
        return "No battery detected — this looks like a desktop, not a laptop."

    percent = battery.percent
    plugged = battery.power_plugged
    status = "Charging" if plugged else "Discharging (running on battery)"

    time_left = ""
    if not plugged and battery.secsleft not in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN, -1):
        mins = battery.secsleft // 60
        hours, mins = divmod(mins, 60)
        time_left = f", about {hours}h {mins}m remaining"

    return f"Battery: {percent}% — {status}{time_left}."


def cpu_status() -> str:
    percent = psutil.cpu_percent(interval=1)
    cores = psutil.cpu_count(logical=False)
    threads = psutil.cpu_count(logical=True)
    freq = psutil.cpu_freq()
    freq_str = f", {freq.current:.0f} MHz" if freq else ""
    return f"CPU: {percent}% usage across {cores} cores / {threads} threads{freq_str}."


def ram_status() -> str:
    mem = psutil.virtual_memory()
    used_gb = mem.used / (1024 ** 3)
    total_gb = mem.total / (1024 ** 3)
    return f"RAM: {used_gb:.1f} GB / {total_gb:.1f} GB used ({mem.percent}%)."


def storage_status() -> str:
    lines = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            used_gb = usage.used / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            lines.append(f"{part.device} {used_gb:.0f}GB/{total_gb:.0f}GB ({usage.percent}%)")
        except (PermissionError, OSError):
            continue
    return "Storage: " + "; ".join(lines) if lines else "Couldn't read storage info."


def network_speed() -> str:
    """Measures current network throughput over a 1-second sample."""
    counters1 = psutil.net_io_counters()
    time.sleep(1)
    counters2 = psutil.net_io_counters()
    download_kbs = (counters2.bytes_recv - counters1.bytes_recv) / 1024
    upload_kbs = (counters2.bytes_sent - counters1.bytes_sent) / 1024
    return f"Network right now: {download_kbs:.1f} KB/s down, {upload_kbs:.1f} KB/s up."


def gpu_status() -> str:
    """Reads live GPU stats via nvidia-smi (ships with NVIDIA drivers)."""
    try:
        result = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            return "Couldn't read GPU info — nvidia-smi not available, or no NVIDIA GPU."
        line = result.stdout.strip().splitlines()[0]
        name, util, mem_used, mem_total, temp = [x.strip() for x in line.split(",")]
        return f"GPU: {name} — {util}% usage, {mem_used}MB/{mem_total}MB VRAM, {temp}°C."
    except FileNotFoundError:
        return "nvidia-smi not found — no NVIDIA GPU detected, or drivers not installed."
    except Exception as e:
        return f"Couldn't read GPU info: {e}"


def full_system_report() -> str:
    """Everything at once — battery, CPU, RAM, GPU, storage, network."""
    parts = [
        battery_status(),
        cpu_status(),
        ram_status(),
        gpu_status(),
        storage_status(),
        network_speed(),
    ]
    return "\n".join(parts)