"""
JARVIS - your local, private AI assistant.

Run:  python main.py

Two modes:
- TEXT mode (default): type your requests, get text replies.
- VOICE mode: say "voice mode" (or type it) to switch — from then on it
  keeps listening and speaking, turn after turn, like a real
  conversation, until you say "text mode" (or another stop keyword) to
  switch back to typing.
"""

import sys
import config
from llm import ask_llm, ask_code, ask_math_explanation
from math_tools import solve_math
from files_tool import organize_folder, find_duplicates, find_and_delete, create_folder, create_file
from system_tool import shutdown_pc, restart_pc, sleep_pc, security_scan, open_app, install_app, uninstall_app, find_and_open_file, find_and_open_folder
from device_tool import battery_status, cpu_status, ram_status, storage_status, network_speed, gpu_status, full_system_report
from security_tool import defender_status, run_quick_scan, firewall_status, recent_threats, full_security_report
from weather_tool import get_weather
from country_tool import country_info
from location_tool import get_location
from audio_tool import mute_speakers, unmute_speakers, mic_on, mic_off, set_volume
from news_tool import news_briefing
from music_tool import play_music
from bluetooth_tool import open_bluetooth_settings, list_bluetooth_devices, toggle_bluetooth
from screen_tool import snap_left, snap_right, split_screen
from rag_tool import index_knowledge_folder, remember, recall
from chat_log_tool import log_exchange, get_recent_history, search_history, clear_history, prune_old_history

VOICE_SWITCH_ON = ("voice mode", "start voice", "switch to voice", "talk to me")
VOICE_SWITCH_OFF = ("text mode", "stop listening", "switch to text", "stop voice")


def say(text: str, spoken: bool = False):
    """Output text, and speak it too if we're currently in voice mode."""
    print(f"\nJarvis: {text}\n")
    if spoken:
        from voice import speak
        speak(text)


def is_blocked(text: str) -> bool:
    lowered = text.lower()
    return any(bad in lowered for bad in config.BLOCKED_KEYWORDS)


def route_command(text: str) -> str:
    lowered = text.lower()

    if is_blocked(text):
        return "I'm not going to run that — it looks destructive. If this was a mistake, rephrase it."

    # --- System control ---
    if "shut down" in lowered or "shutdown" in lowered:
        return shutdown_pc()
    if "restart" in lowered or "reboot" in lowered:
        return restart_pc()
    if "sleep" in lowered:
        return sleep_pc()
    if "battery" in lowered or "charging" in lowered or "discharging" in lowered:
        return battery_status()
    if "network speed" in lowered or "internet speed" in lowered or "download speed" in lowered or "upload speed" in lowered:
        return network_speed()
    if "gpu" in lowered or "graphics card" in lowered:
        return gpu_status()
    if "ram" in lowered or "memory" in lowered and "remember" not in lowered:
        return ram_status()
    if "storage" in lowered or "disk space" in lowered or " rom" in lowered:
        return storage_status()
    if "full system" in lowered or "system report" in lowered or "system specs" in lowered:
        return full_system_report()
    if "system status" in lowered or "how's my pc" in lowered or lowered.strip() == "cpu":
        return cpu_status()
    if "antivirus" in lowered or "defender" in lowered:
        return defender_status()
    if "virus scan" in lowered or "scan for viruses" in lowered or "run a scan" in lowered:
        return run_quick_scan()
    if "firewall" in lowered:
        return firewall_status()
    if "recent threats" in lowered or "any viruses" in lowered or "threat detect" in lowered:
        return recent_threats()
    if "security report" in lowered or "full security" in lowered:
        return full_security_report()
    if "security" in lowered or "anything suspicious" in lowered:
        return security_scan()
    if lowered.startswith("open "):
        target = text[5:].strip()
        # "open file X" / "open document X" -> search for an actual file
        if lowered.startswith("open file ") or lowered.startswith("open document "):
            file_query = target.split(" ", 1)[1] if " " in target else target
            return find_and_open_file(file_query)
        # "open folder X" -> search for an actual folder
        if lowered.startswith("open folder "):
            folder_query = target.split(" ", 1)[1] if " " in target else target
            return find_and_open_folder(folder_query)
        # otherwise treat it as an application
        return open_app(target)
    if lowered.startswith("install "):
        app_name = text[8:].strip()
        confirm = input(f"Jarvis: You want me to install '{app_name}'? Type 'yes' to confirm: ").strip().lower()
        if confirm == "yes":
            return install_app(app_name)
        return "Cancelled — didn't install anything."
    if lowered.startswith("uninstall ") or (lowered.startswith("remove ") and ("app" in lowered or "program" in lowered)):
        app_name = text.split(" ", 1)[1].strip()
        for prefix in ("app ", "program ", "the app ", "the program "):
            if app_name.lower().startswith(prefix):
                app_name = app_name[len(prefix):].strip()
        confirm = input(f"Jarvis: You want me to PERMANENTLY uninstall '{app_name}'? Type 'yes' to confirm: ").strip().lower()
        if confirm == "yes":
            return uninstall_app(app_name)
        return "Cancelled — didn't remove anything."

    # --- Files ---
    if (lowered.startswith("create folder ") or lowered.startswith("make folder ") or
        lowered.startswith("create a folder ") or lowered.startswith("make a folder ")):
        name = text.split(" ", 1)[1].strip()
        for prefix in ("folder ", "a folder ", "called ", "named "):
            if name.lower().startswith(prefix):
                name = name[len(prefix):].strip()
        return create_folder(name)
    if (lowered.startswith("create file ") or lowered.startswith("make file ") or
        lowered.startswith("create a file ") or lowered.startswith("make a file ")):
        name = text.split(" ", 1)[1].strip()
        for prefix in ("file ", "a file ", "called ", "named "):
            if name.lower().startswith(prefix):
                name = name[len(prefix):].strip()
        return create_file(name)
    if "organize" in lowered and ("file" in lowered or "download" in lowered or "folder" in lowered):
        return organize_folder()
    if "duplicate" in lowered:
        dupes = find_duplicates()
        return f"Found {len(dupes)} possible duplicate(s)." if dupes else "No duplicates found."
    if lowered.startswith("delete ") or (lowered.startswith("remove ") and "app" not in lowered and "program" not in lowered):
        target = text.split(" ", 1)[1].strip()
        for prefix in ("file ", "folder ", "document "):
            if target.lower().startswith(prefix):
                target = target[len(prefix):].strip()
        confirm = input(f"Jarvis: Move '{target}' to the Recycle Bin? Type 'yes' to confirm: ").strip().lower()
        if confirm == "yes":
            return find_and_delete(target)
        return "Cancelled — didn't delete anything."

    # --- Bluetooth ---
    if "bluetooth" in lowered:
        if "device" in lowered or "list" in lowered or "paired" in lowered:
            return list_bluetooth_devices()
        if "turn on" in lowered or "enable" in lowered:
            return toggle_bluetooth(turn_on=True)
        if "turn off" in lowered or "disable" in lowered:
            return toggle_bluetooth(turn_on=False)
        # default: just open the settings panel, most reliable option
        return open_bluetooth_settings()

    # --- Chat History ---
    if lowered in ("clear chat history", "delete chat history", "clear history"):
        confirm = input("Jarvis: Move chat history to the Recycle Bin? Type 'yes' to confirm: ").strip().lower()
        if confirm == "yes":
            return clear_history()
        return "Cancelled — history kept."
    if lowered in ("show chat history", "show history", "chat history", "what did we talk about"):
        return get_recent_history()
    if lowered.startswith("search history for ") or lowered.startswith("when did we talk about "):
        query = text.split(" for ", 1)[-1] if " for " in lowered else text.split("about ", 1)[-1]
        return search_history(query.strip())

    # --- RAG Memory ---
    if lowered in ("index my notes", "index knowledge", "index my knowledge"):
        return index_knowledge_folder()
    if lowered.startswith("remember "):
        fact = text[9:].strip()
        return remember(fact)
    if lowered.startswith("recall ") or lowered.startswith("what do you know about ") or lowered.startswith("do you remember"):
        return recall(text)

    # --- Screen splitting ---
    if lowered.startswith("split ") or lowered.startswith("split screen") or "snap" in lowered:
        if "left" in lowered and "and" not in lowered:
            return snap_left()
        if "right" in lowered and "and" not in lowered:
            return snap_right()
        if " and " in lowered:
            # e.g. "split screen with chrome and notepad" OR "split chrome and edge"
            after_split = text.lower().replace("split screen", "").replace("split", "", 1)
            after_split = after_split.replace("with", "").strip()
            if " and " in after_split:
                app1, app2 = after_split.split(" and ", 1)
                return split_screen(app1.strip(), app2.strip())
        return "Tell me two apps, like: 'split chrome and notepad'."

    # --- Music ---
    if lowered.startswith("play "):
        song_query = text[5:].strip()
        prefer = "auto"
        if "youtube" in lowered:
            prefer = "youtube"
            song_query = song_query.lower().replace("on youtube music", "").replace("on youtube", "").replace("youtube music", "").replace("youtube", "").strip()
        elif "spotify" in lowered:
            prefer = "spotify"
            song_query = song_query.lower().replace("on spotify", "").replace("spotify", "").strip()
        elif "local" in lowered or "my music" in lowered:
            prefer = "local"
            song_query = song_query.lower().replace("from my music", "").replace("locally", "").strip()
        return play_music(song_query, prefer=prefer)

    # --- Location ---
    if "where am i" in lowered or "my location" in lowered or "current location" in lowered or "location tracker" in lowered:
        return get_location()

    # --- Audio control ---
    if "microphone" in lowered or lowered.strip() in ("mic on", "mic off"):
        if "off" in lowered or "mute" in lowered or "disable" in lowered:
            return mic_off()
        if "on" in lowered or "unmute" in lowered or "enable" in lowered:
            return mic_on()
    if lowered.strip().startswith("volume "):
        try:
            percent = int("".join(c for c in lowered if c.isdigit()))
            return set_volume(percent)
        except ValueError:
            return "Tell me a volume percentage, like 'volume 50'."
    if "unmute" in lowered:
        return unmute_speakers()
    if "mute" in lowered:
        return mute_speakers()

    # --- Country facts (real data, not LLM guessing) ---
    if lowered.startswith("country ") or "capital of" in lowered or "population of" in lowered:
        for prefix in ("country ", "what is the capital of ", "what's the capital of ",
                        "capital of ", "what is the population of ", "population of "):
            if lowered.startswith(prefix):
                country_name = text[len(prefix):].strip().rstrip("?")
                return country_info(country_name)
        return "Which country? Try: 'country Japan' or 'capital of France'."

    # --- Weather ---
    if "weather" in lowered:
        city = None
        if " in " in lowered:
            city = text.lower().split(" in ", 1)[-1].strip()
        elif " for " in lowered:
            city = text.lower().split(" for ", 1)[-1].strip()
        return get_weather(city)

    # --- News ---
    if "news" in lowered:
        topic = "tech" if "tech" in lowered else "sports" if "sport" in lowered else "top"
        return news_briefing(topic)  # use_ai_wrapper=False by default (accurate, no invented details)

    # --- Math ---
    if any(w in lowered for w in ["solve", "calculate", "what is", "derivative", "integral"]) and \
       any(c.isdigit() for c in text):
        result = solve_math(text)
        if result:
            return ask_math_explanation(text, result)
        # fall through to general LLM if sympy couldn't parse it

    # --- Code ---
    if any(w in lowered for w in ["code", "script", "function", "python", "javascript", "debug", "bug"]):
        return ask_code(text)

    # --- Exit ---
    if lowered in ("exit", "quit", "goodbye", "bye"):
        say("Goodbye, sir.")
        sys.exit(0)

    # --- Default: general chat ---
    return ask_llm(text)


def main():
    mode = "text"  # starts in text mode; "voice mode" switches persistently

    # Auto-clean chat history older than 30 days, silently, before anything else
    prune_result = prune_old_history(days=30)
    if prune_result:
        print(f"[history] {prune_result}")

    say("JARVIS online. What can I do for you?")

    while True:
        try:
            if mode == "voice":
                from voice import listen
                print("(listening...)")
                user_text = listen()
                if not user_text:
                    continue
                print(f"You said: {user_text}")
            else:
                user_text = input("You: ").strip()
                if not user_text:
                    continue

            lowered = user_text.lower()

            # --- Mode switching (checked before normal routing) ---
            if mode == "text" and lowered in VOICE_SWITCH_ON:
                mode = "voice"
                say("Switching to voice mode. Say 'text mode' anytime to go back to typing.", spoken=True)
                continue
            if mode == "voice" and lowered in VOICE_SWITCH_OFF:
                mode = "text"
                say("Switching to text mode.", spoken=False)
                continue

            response = route_command(user_text)
            log_exchange(user_text, response)
            say(response, spoken=(mode == "voice"))

        except KeyboardInterrupt:
            say("Shutting down. Goodbye.", spoken=(mode == "voice"))
            break


if __name__ == "__main__":
    main()