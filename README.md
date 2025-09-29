# WindowRPC
WindowRPC is a Python-based tool that automatically updates your Discord status with your currently focused window as Rich Presence. It offers flexible options such as custom statuses per application, allowing you to tailor your Discord presence to your preferences.

## Supported Platforms
Windows(this branch)(*OUTDATED! kde-linux HAS MORE FEATURES. THIS BRANCH NEEDS TO BE UPDATED*)

[Linux(KDE Plasma Wayland)](https://github.com/ios7jbpro/WindowRPC/tree/kde-linux)

## Features
- Automatically updates Discord Rich Presence based on the currently active window.
- Customize your status for specific applications.

## Installation
To get started with WindowRPC:

### Clone the Repository
Clone this repository to your local machine:

```
git clone https://github.com/yourusername/WindowRPC.git
cd WindowRPC
```

### Install Dependencies
Ensure you have Python installed, then install the required dependencies using pip:

```
pip install pygetwindow pypresence pystray
```

### Create a Discord Application
Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application. The application name will be what's shown as the application name in the rich presence. Note the Application ID.

### Configure the Script
Open discordrpc.py in a text editor, and replace the placeholder Application ID (the value of the `client_id` variable) with your own.

### Run the Script
Start the script using the command line:

```
python discordrpc.py
```

...or, use run.bat

## Usage
Once the script is running, your Discord status will automatically update based on the active window. You can customize specific application statuses by modifying the script.

## Contributors
- ios7jbpro
- kurtbahartr
- ChatGPT(i have problems i know)
- This project was intended to be AI-generated only. However, simple contributions that remain easy for AI to parse and understand are welcome. Please submit issues or pull requests that align with this guideline.

## Issues and Support
For any issues or questions, please open a ticket in the Issues tab.
