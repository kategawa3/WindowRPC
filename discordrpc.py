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

def format_message(template, window_title, elapsed_str):
    """ Replace placeholders in the template with actual values """
    return template.replace("appname", window_title).replace("timestamp", elapsed_str)

def check_exe_override(window_title):
    for app_name, message in sorted_overrides:
        # fallback: if no match_mode, treat as "unimportant"
        match_mode = message.get('match_mode', 'unimportant').lower()

        if match_mode == "exact":
            if window_title.lower() == app_name.lower():
                print(f"[EXACT match] Override found for {window_title}: {message}")
            else:
                continue  # skip, must match exactly
        else:  # unimportant = substring search
            if app_name.lower() not in window_title.lower():
                continue
            print(f"[SUBSTRING match] Override found for {window_title}: {message}")

        # at this point, we have a match
        elapsed_time = time.time() - start_time
        elapsed_str = f"{int(elapsed_time // 60)}m {int(elapsed_time % 60)}s"
        state_message = format_message(message['state'], window_title, elapsed_str)
        details_message = format_message(message['details'], window_title, elapsed_str)
        logo = message.get('logo', 'rpc_icon')
        return state_message, details_message, logo

    # no override matched
    return None, None, 'rpc_icon'


def truncate_text(text, max_length=60):
    """Ensure the text is no longer than max_length characters, adding '...' if truncated."""
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text

rpc_enabled = True
start_time = time.time()

def update_rpc():
    global interval, rpc_enabled
    while True:
        elapsed_time = time.time() - start_time
        elapsed_str = f"{int(elapsed_time // 60)}m {int(elapsed_time % 60)}s"
        
        if rpc_enabled:
            active_window_title = get_active_window_title()
            print(f"Detected window: {active_window_title}")
            
            state, details, logo = check_exe_override(active_window_title)
            
            if state and details:
                state_message = format_message(state, active_window_title, elapsed_str)
                details_message = format_message(details, active_window_title, elapsed_str)
            else:
                state_message = format_message(default_settings.get('state', ''), active_window_title, elapsed_str)
                details_message = format_message(default_settings.get('details', ''), active_window_title, elapsed_str)
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
            fallback_state = truncate_text(f"{elapsed_str} - Current window cannot be detected!")
            fallback_details = truncate_text("Currently using:")

            RPC.update(
                state=fallback_state,
                details=fallback_details
            )
        
        time.sleep(interval)

# --- System tray logic ---
def toggle_rpc_action(icon, item):
    global rpc_enabled
    rpc_enabled = not rpc_enabled
    status = "Enabled" if rpc_enabled else "Disabled"
    print(f"RPC is now {status}")

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

# Start tray in background thread
tray_thread = threading.Thread(target=create_tray, daemon=True)
tray_thread.start()

# Run the RPC update loop
update_rpc()
