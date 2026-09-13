"""
Bluetooth utilities for Windows.

Windows doesn't allow easy, reliable programmatic on/off toggling of the
Bluetooth radio without admin rights and extra tools, so this module
focuses on what's genuinely reliable: listing paired devices and jumping
straight to the Bluetooth settings panel so you can toggle it yourself
in one click.
"""

import os
import subprocess
import platform
import tempfile

IS_WINDOWS = platform.system() == "Windows"


def open_bluetooth_settings() -> str:
    """Opens the Windows Bluetooth settings panel directly."""
    if not IS_WINDOWS:
        return "Bluetooth settings shortcut is Windows-only right now."
    os.system("start ms-settings:bluetooth")
    return "Opened Bluetooth settings — toggle it there."


def list_bluetooth_devices() -> str:
    """Lists paired/known Bluetooth devices using PowerShell."""
    if not IS_WINDOWS:
        return "Bluetooth device listing is Windows-only right now."

    try:
        # Get-PnpDevice lists Bluetooth-class devices Windows knows about
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-PnpDevice -Class Bluetooth | Select-Object -ExpandProperty FriendlyName"],
            capture_output=True, text=True, timeout=15
        )
        devices = [d.strip() for d in result.stdout.splitlines() if d.strip()]
        if not devices:
            return "No Bluetooth devices found — is Bluetooth on, and is anything paired?"
        listed = "\n".join(f"- {d}" for d in devices)
        return f"Bluetooth devices found:\n{listed}"
    except FileNotFoundError:
        return "PowerShell isn't available — can't check Bluetooth devices."
    except subprocess.TimeoutExpired:
        return "Checking Bluetooth devices took too long — try again."
    except Exception as e:
        return f"Couldn't check Bluetooth devices: {e}"


# --- Optional / advanced: real on-off toggle ---
# This requires admin rights and is more fragile across different PCs.
# Only use this if open_bluetooth_settings() isn't good enough for you.
def toggle_bluetooth(turn_on: bool) -> str:
    if not IS_WINDOWS:
        return "Bluetooth toggling is Windows-only right now."

    state = "Enable-PnpDevice" if turn_on else "Disable-PnpDevice"
    try:
        # This targets the actual Bluetooth radio/adapter hardware
        # (matches names like "Realtek Wireless Bluetooth Adapter",
        # "Intel Wireless Bluetooth", or "...Radio" depending on your PC)
        # while excluding paired accessories like earbuds.
        cmd = (
            f"Get-PnpDevice -Class Bluetooth | "
            f"Where-Object {{$_.FriendlyName -like '*Adapter*' -or "
            f"$_.FriendlyName -like '*Radio*'}} | "
            f"ForEach-Object {{ {state} -InstanceId $_.InstanceId -Confirm:$false }}"
        )
        print(f"[DEBUG] cmd being sent: {cmd}")

        # Write the command to a temporary .ps1 script file instead of
        # passing it inline — this avoids PowerShell's fragile nested-quote
        # parsing when combined with Start-Process -ArgumentList.
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as tmp:
            tmp.write(cmd)
            script_path = tmp.name

        elevate_wrapper = (
            f"Start-Process powershell -Verb RunAs -Wait "
            f"-ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"{script_path}\"'"
        )
        result = subprocess.run(["powershell", "-Command", elevate_wrapper],
                                 capture_output=True, text=True, timeout=30)
        os.remove(script_path)
        print(f"[DEBUG] returncode: {result.returncode}")
        print(f"[DEBUG] stdout: {result.stdout}")
        print(f"[DEBUG] stderr: {result.stderr}")
        if result.returncode == 0:
            return f"Bluetooth turned {'on' if turn_on else 'off'} (if run as Administrator)."
        return ("Couldn't toggle Bluetooth — this usually needs the terminal "
                "to be run as Administrator. Try 'open bluetooth settings' instead.")
    except Exception as e:
        return f"Bluetooth toggle failed: {e}"