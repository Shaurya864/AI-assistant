"""
JARVIS Dashboard — full GUI version.

Run:  python gui.py

Combines: a chat panel (like the terminal version), a live-updating
system stats sidebar, and quick-action buttons — all in one window.
Uses tkinter, which ships with Python, so no extra install is needed
for the GUI itself (your existing requirements.txt packages still
apply for voice/music/etc. features).
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import builtins

import config
from main import route_command, VOICE_SWITCH_ON, VOICE_SWITCH_OFF
from device_tool import battery_status, cpu_status, ram_status, gpu_status, storage_status
from audio_tool import mute_speakers, unmute_speakers
from system_tool import shutdown_pc, restart_pc


# ---------------------------------------------------------------
# Redirect confirmation prompts (install/uninstall/delete/clear
# history) from terminal input() to real GUI dialogs, since a
# console input() call would just freeze the GUI window otherwise.
# ---------------------------------------------------------------
def _gui_input_override(prompt: str = "") -> str:
    clean_prompt = prompt.replace("Jarvis: ", "").strip()
    result = messagebox.askyesno("Confirm", clean_prompt)
    return "yes" if result else "no"


builtins.input = _gui_input_override


class JarvisDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS Dashboard")
        self.root.geometry("1000x650")
        self.root.configure(bg="#1e1e1e")

        self.voice_mode = False

        self._build_layout()
        self._refresh_stats_loop()
        self._append_chat("Jarvis", "JARVIS online. What can I do for you?")

    # ---------------- Layout ----------------
    def _build_layout(self):
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Left: chat panel ---
        chat_frame = tk.Frame(main_frame, bg="#1e1e1e")
        chat_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.chat_box = scrolledtext.ScrolledText(
            chat_frame, wrap="word", bg="#121212", fg="#e0e0e0",
            font=("Consolas", 11), state="disabled"
        )
        self.chat_box.pack(fill="both", expand=True)

        input_frame = tk.Frame(chat_frame, bg="#1e1e1e")
        input_frame.pack(fill="x", pady=(8, 0))

        self.entry = tk.Entry(input_frame, bg="#2a2a2a", fg="#e0e0e0",
                               font=("Consolas", 11), insertbackground="#e0e0e0")
        self.entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.entry.bind("<Return>", lambda e: self._on_send())

        send_btn = tk.Button(input_frame, text="Send", command=self._on_send,
                              bg="#3a3a3a", fg="white")
        send_btn.pack(side="left", padx=(6, 0))

        # --- Right: stats + controls sidebar ---
        sidebar = tk.Frame(main_frame, bg="#242424", width=280)
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="System Status", bg="#242424", fg="white",
                 font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))

        self.stats_label = tk.Label(sidebar, text="Loading...", bg="#242424", fg="#a0d0a0",
                                     font=("Consolas", 9), justify="left", anchor="w")
        self.stats_label.pack(fill="x", padx=10, pady=(0, 15))

        tk.Label(sidebar, text="Quick Controls", bg="#242424", fg="white",
                 font=("Segoe UI", 12, "bold")).pack(pady=(5, 5))

        self.voice_btn = tk.Button(sidebar, text="🎤 Start Voice Mode", command=self._toggle_voice,
                                    bg="#3a3a3a", fg="white", width=24)
        self.voice_btn.pack(pady=4)

        tk.Button(sidebar, text="🔇 Mute", command=lambda: self._append_chat("Jarvis", mute_speakers()),
                  bg="#3a3a3a", fg="white", width=24).pack(pady=4)
        tk.Button(sidebar, text="🔊 Unmute", command=lambda: self._append_chat("Jarvis", unmute_speakers()),
                  bg="#3a3a3a", fg="white", width=24).pack(pady=4)
        tk.Button(sidebar, text="⏻ Shutdown PC", command=self._confirm_shutdown,
                  bg="#5a2a2a", fg="white", width=24).pack(pady=4)
        tk.Button(sidebar, text="🔄 Restart PC", command=self._confirm_restart,
                  bg="#5a2a2a", fg="white", width=24).pack(pady=4)

    # ---------------- Chat handling ----------------
    def _append_chat(self, sender: str, text: str):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{sender}: {text}\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def _on_send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._append_chat("You", text)
        self._process_input(text)

    def _process_input(self, text: str):
        lowered = text.lower()
        if lowered in VOICE_SWITCH_ON:
            self._toggle_voice(force_on=True)
            return
        if lowered in VOICE_SWITCH_OFF:
            self._toggle_voice(force_on=False)
            return

        response = route_command(text)
        self._append_chat("Jarvis", response)
        if self.voice_mode:
            from voice import speak
            threading.Thread(target=speak, args=(response,), daemon=True).start()

    # ---------------- Voice mode ----------------
    def _toggle_voice(self, force_on: bool = None):
        self.voice_mode = force_on if force_on is not None else not self.voice_mode
        if self.voice_mode:
            self.voice_btn.config(text="🎤 Stop Voice Mode (listening...)")
            self._append_chat("Jarvis", "Voice mode on. Say 'text mode' to switch back.")
            threading.Thread(target=self._voice_loop, daemon=True).start()
        else:
            self.voice_btn.config(text="🎤 Start Voice Mode")
            self._append_chat("Jarvis", "Voice mode off.")

    def _voice_loop(self):
        from voice import listen
        while self.voice_mode:
            try:
                text = listen()
                if not text:
                    continue
                self.root.after(0, self._append_chat, "You (voice)", text)
                if text.lower() in VOICE_SWITCH_OFF:
                    self.root.after(0, self._toggle_voice, False)
                    break
                response = route_command(text)
                self.root.after(0, self._append_chat, "Jarvis", response)
                from voice import speak
                speak(response)
            except Exception as e:
                self.root.after(0, self._append_chat, "Jarvis", f"Voice error: {e}")
                break

    # ---------------- Stats refresh ----------------
    def _refresh_stats_loop(self):
        def worker():
            try:
                text = "\n\n".join([battery_status(), cpu_status(), ram_status(), gpu_status()])
            except Exception as e:
                text = f"Stats error: {e}"
            self.root.after(0, lambda: self.stats_label.config(text=text))
        threading.Thread(target=worker, daemon=True).start()
        self.root.after(5000, self._refresh_stats_loop)  # refresh every 5 seconds

    # ---------------- Power controls ----------------
    def _confirm_shutdown(self):
        if messagebox.askyesno("Confirm", "Shut down the PC now?"):
            self._append_chat("Jarvis", shutdown_pc())

    def _confirm_restart(self):
        if messagebox.askyesno("Confirm", "Restart the PC now?"):
            self._append_chat("Jarvis", restart_pc())


if __name__ == "__main__":
    root = tk.Tk()
    app = JarvisDashboard(root)
    root.mainloop()