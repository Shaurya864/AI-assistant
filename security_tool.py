"""
Antivirus / security status, using Windows Defender's built-in
PowerShell cmdlets. Works with Defender specifically — if you use a
different antivirus (Norton, McAfee, etc.), Defender may show as
disabled because the other AV has taken over, which is normal and fine.
"""

import subprocess


def defender_status() -> str:
    """Reports whether Windows Defender is active and up to date."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-MpComputerStatus | Select-Object AntivirusEnabled, "
             "RealTimeProtectionEnabled, AntivirusSignatureLastUpdated, "
             "AntivirusSignatureVersion | ConvertTo-Json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15
        )
        import json
        if not result.stdout.strip():
            return ("Couldn't read antivirus status — if you use a non-Defender "
                    "antivirus (Norton, McAfee, etc.), that's likely why.")

        data = json.loads(result.stdout)
        av_on = data.get("AntivirusEnabled", False)
        rtp_on = data.get("RealTimeProtectionEnabled", False)
        sig_date = data.get("AntivirusSignatureLastUpdated", "unknown")
        sig_version = data.get("AntivirusSignatureVersion", "unknown")

        status = "ON" if av_on else "OFF"
        rtp_status = "ON" if rtp_on else "OFF"

        warning = ""
        if not av_on or not rtp_on:
            warning = " ⚠️ Your antivirus protection isn't fully active — worth checking Settings > Privacy & Security > Windows Security."

        return (f"Antivirus: {status} | Real-time protection: {rtp_status} | "
                f"Signatures updated: {sig_date} (v{sig_version}){warning}")
    except Exception as e:
        return f"Couldn't check antivirus status: {e}"


def run_quick_scan() -> str:
    """Triggers a Windows Defender quick scan (runs in the background)."""
    try:
        subprocess.Popen(
            ["powershell", "-Command", "Start-MpScan -ScanType QuickScan"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return ("Started a quick antivirus scan in the background — it'll keep "
                "running even after this. Check Windows Security app for results "
                "when it finishes.")
    except Exception as e:
        return f"Couldn't start a scan: {e}"


def firewall_status() -> str:
    """Reports whether the Windows Firewall is enabled for each network profile."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-NetFirewallProfile | Select-Object Name, Enabled | ConvertTo-Json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15
        )
        import json
        data = json.loads(result.stdout) if result.stdout.strip() else []
        if isinstance(data, dict):
            data = [data]
        if not data:
            return "Couldn't read firewall status."

        lines = [f"{p['Name']}: {'ON' if p['Enabled'] else 'OFF'}" for p in data]
        any_off = any(not p["Enabled"] for p in data)
        warning = " ⚠️ At least one profile has the firewall off." if any_off else ""
        return "Firewall — " + ", ".join(lines) + warning
    except Exception as e:
        return f"Couldn't check firewall status: {e}"


def recent_threats() -> str:
    """Lists any threats Windows Defender has detected recently."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-MpThreatDetection | Select-Object -First 5 ThreatID, "
             "InitialDetectionTime, Resources | ConvertTo-Json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15
        )
        if not result.stdout.strip():
            return "No recent threats detected — clean as far as Defender can tell."

        import json
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]
        if not data:
            return "No recent threats detected — clean as far as Defender can tell."

        lines = [f"- Detected {t.get('InitialDetectionTime', 'unknown time')}" for t in data]
        return "Recent threat detections:\n" + "\n".join(lines)
    except Exception as e:
        return f"Couldn't check threat history: {e}"


def full_security_report() -> str:
    """Everything at once — antivirus, firewall, recent threats."""
    return "\n".join([defender_status(), firewall_status(), recent_threats()])