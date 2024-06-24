import os
import tempfile

from adb_shell.adb_device import AdbDeviceTcp
from PIL import Image
import yaml


# Load configuration from config.yaml
def load_config(config_path=r'config.yaml'):
    with open(config_path, 'r', encoding='utf-8') as file:  # Specify encoding here
        config = yaml.safe_load(file)
    return config

# Initialize ADB connection
def init_adb_connection(host, port):
    device = AdbDeviceTcp(host, port, default_transport_timeout_s=9.0)
    device.connect()
    return device

# Get emulator resolution
def get_emulator_resolution(device):
    result = device.shell('wm size')
    return result.strip()

# Get emulator density
def get_emulator_density(device):
    result = device.shell('wm density')
    return result.strip()

# Take a screenshot
def take_screenshot(device):
    screenshot_path = '/sdcard/screen.png'
    device.shell(f'screencap -p {screenshot_path}')
    return screenshot_path

# Pull the screenshot to a temporary file
def pull_screenshot(device, remote_path):
    local_fd, local_path = tempfile.mkstemp(suffix='.png')
    os.close(local_fd)  # Close the file descriptor immediately
    device.pull(remote_path, local_path)
    return local_path

# Open the screenshot
def open_screenshot(local_path):
    img = Image.open(local_path)
    img.show()

# Delete the remote and local screenshot files
def delete_screenshot(device, remote_path, local_path):
    device.shell(f'rm {remote_path}')
    os.remove(local_path)

# Check emulator properties
def check_emulator_properties():
    config = load_config()
    adb_config = config['adb']
    
    device = init_adb_connection(adb_config['ip'], adb_config['port'])

    resolution = get_emulator_resolution(device)
    density = get_emulator_density(device)

    resolution_correct = "720x1280" in resolution
    density_correct = "240" in density

    if resolution_correct and density_correct:
        print("The emulator has the correct resolution (720x1280) and density (240 dpi).")
        
        screenshot_path = take_screenshot(device)
        local_screenshot_path = pull_screenshot(device, screenshot_path)
        open_screenshot(local_screenshot_path)
        
        delete_screenshot(device, screenshot_path, local_screenshot_path)
        
        print("ClashRoyaleBuildABot can now be started with `python main.py`.")
    else:
        print("The emulator does not have the correct properties.")
        if not resolution_correct:
            print(f"Current resolution: {resolution}")
        if not density_correct:
            print(f"Current density: {density}")

if __name__ == "__main__":
    check_emulator_properties()
