import time
import threading
import pygetwindow as gw
from pypresence import Presence
import json
import subprocess
import os
import sys
from PIL import Image  # for pystray icon
import pystray        # system tray

# Discord client ID
client_id = "1275126036262031452"
RPC = Presence(client_id)
RPC.connect()

def run_filecheck():
    """Run filecheck.py to ensure JSON files exist and are correctly set up."""
    try:
        subprocess.run(['python', 'filecheck.py'], check=True)
        print("Filecheck completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running filecheck.py: {e}")

# Run filecheck before proceeding
run_filecheck()

# Load overrides and default settings from JSON files
def load_json(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Failed to load {filename}: {e}")
        return {}

def refresh_files():
    global overrides, sorted_overrides, default_settings, interval
    overrides = load_json('overrides.json')
    sorted_overrides = sorted(overrides.items(), key=lambda item: len(item[0]), reverse=True)
    default_settings = load_json('default.json').get('default', {})
    interval = int(default_settings.get('interval', 15))  # Default to 15 seconds if not specified
    print("Files refreshed")

overrides = load_json('overrides.json')
sorted_overrides = sorted(overrides.items(), key=lambda item: len(item[0]), reverse=True)
default_settings = load_json('default.json').get('default', {})
interval = int(default_settings.get('interval', 15))  # Default to 15 seconds if not specified

def get_active_window_title():
    window = gw.getActiveWindow()
    return window.title if window else "No active window"

def format_message(template, window_title, elapsed_str, total_elapsed_str, media_info=None):
    """Replace placeholders in template"""
    return (template.replace("appname", window_title)
                    .replace("timestamp", elapsed_str)
                    .replace("totaltimestamp", total_elapsed_str))

# tracking start times
start_time = time.time()  # script-wide start time
app_start_times = {}      # per-app start times {app_name: timestamp}

# state tracking
active_game = None  # currently locked game override

# ------------------ override logic -------------------
def match_override(window_title):
    """Find matching override based on title + match_mode logic."""
    for app_name, message in sorted_overrides:
        match_mode = message.get('match_mode', 'unimportant').lower()
        if match_mode == "exact":
            if window_title.lower() != app_name.lower():
                continue
        else:
            if app_name.lower() not in window_title.lower():
                continue
        return app_name, message
    return None, None

def process_override(app_name, message, window_title):
    """Build messages and handle timestamps for a matched override."""
    # detect media override and block it on Windows
    if message.get("override_mode") == "media":
        print(f"Media override detected ({app_name}) – unsupported on Windows. Showing warning RPC.")
        return "Unsupported", "This action is unsupported in Windows releases.", 'rpc_icon'

    if app_name not in app_start_times:
        app_start_times[app_name] = time.time()

    app_elapsed_time = time.time() - app_start_times[app_name]
    app_elapsed_str = f"{int(app_elapsed_time // 60)}m {int(app_elapsed_time % 60)}s"

    total_elapsed_time = time.time() - start_time
    total_elapsed_str = f"{int(total_elapsed_time // 60)}m {int(total_elapsed_time % 60)}s"

    state_message = format_message(message['state'], window_title, app_elapsed_str, total_elapsed_str)
    details_message = format_message(message['details'], window_title, app_elapsed_str, total_elapsed_str)
    logo = message.get('logo', 'rpc_icon')
    return state_message, details_message, logo

def determine_override(active_window_title):
    global active_game

    # 1. game mode
    if active_game:
        app_name, message = active_game
        open_titles = [w.title for w in gw.getAllWindows() if w.title]
        still_running = any(app_name.lower() in t.lower() for t in open_titles)
        if still_running:
            return process_override(app_name, message, active_window_title)
        else:
            print(f"Game {app_name} closed, clearing active game")
            active_game = None

    # 2. check focused window for game override
    app_name, message = match_override(active_window_title)
    if app_name and message.get("override_mode") == "game":
        active_game = (app_name, message)
        print(f"Game detected and locked: {app_name}")
        return process_override(app_name, message, active_window_title)

    # 3. media override – unsupported on Windows
    if app_name and message.get("override_mode") == "media":
        return process_override(app_name, message, active_window_title)

    # 4. none/default
    if app_name and message.get("override_mode", "none") == "none":
        return process_override(app_name, message, active_window_title)

    return None, None, 'rpc_icon'

# ------------------ main loop -------------------
def truncate_text(text, max_length=60):
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text

rpc_enabled = True

def update_rpc():
    global interval, rpc_enabled
    while True:
        total_elapsed_time = time.time() - start_time
        total_elapsed_str = f"{int(total_elapsed_time // 60)}m {int(total_elapsed_time % 60)}s"

        if rpc_enabled:
            active_window_title = get_active_window_title()
            print(f"Detected window: {active_window_title}")

            state, details, logo = determine_override(active_window_title)

            if state and details:
                state_message = truncate_text(state)
                details_message = truncate_text(details)
            else:
                state_message = format_message(default_settings.get('state', ''), active_window_title, total_elapsed_str, total_elapsed_str)
                details_message = format_message(default_settings.get('details', ''), active_window_title, total_elapsed_str, total_elapsed_str)
                logo = 'rpc_icon'
                state_message = truncate_text(state_message)
                details_message = truncate_text(details_message)

            print(f"Updating RPC with state: '{state_message}', details: '{details_message}', and logo: '{logo}'")
            RPC.update(
                state=state_message,
                details=details_message,
                large_image=logo,
                large_text="0.6.1"
            )
        else:
            fallback_state = truncate_text(f"{total_elapsed_str} - Current window cannot be detected!")
            fallback_details = truncate_text("Currently using:")
            RPC.update(
                state=fallback_state,
                details=fallback_details
            )

        time.sleep(interval)

# ------------------ tray -------------------
def toggle_rpc_action(icon, item):
    global rpc_enabled
    rpc_enabled = not rpc_enabled
    print(f"RPC is now {'Enabled' if rpc_enabled else 'Disabled'}")

def refresh_files_action(icon, item):
    refresh_files()

def exit_action(icon, item):
    print("Exiting...")
    icon.stop()
    sys.exit(0)

def create_tray():
    icon_path = os.path.join(os.path.dirname(__file__), "discord_icon.png")
    image = Image.open(icon_path)
    menu = pystray.Menu(
        pystray.MenuItem("Toggle RPC", toggle_rpc_action),
        pystray.MenuItem("Refresh files", refresh_files_action),
        pystray.MenuItem("Exit", exit_action)
    )
    icon = pystray.Icon("DiscordRPC", image, "Discord RPC", menu)
    icon.run()

tray_thread = threading.Thread(target=create_tray, daemon=True)
tray_thread.start()

update_rpc()


