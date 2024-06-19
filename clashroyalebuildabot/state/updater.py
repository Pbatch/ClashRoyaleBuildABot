import requests
import os
import zipfile
import shutil
from loguru import logger

GITHUB_REPO = "Pbatch/ClashRoyaleBuildABot"
LOCAL_VERSION = "3b1fb24a35f664fcab4ada324ea4ee4a84084742"
DOWNLOAD_PATH = "update.zip"
EXTRACT_PATH = "."

def get_latest_commit():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["sha"]

def download_update(commit_sha):
    url = f"https://github.com/{GITHUB_REPO}/archive/{commit_sha}.zip"
    response = requests.get(url)
    response.raise_for_status()
    with open(DOWNLOAD_PATH, "wb") as file:
        file.write(response.content)

def extract_update():
    with zipfile.ZipFile(DOWNLOAD_PATH, "r") as zip_ref:
        zip_ref.extractall(EXTRACT_PATH)

def replace_old_version(commit_sha):
    new_folder_name = f"{GITHUB_REPO.split('/')[-1]}-{commit_sha}"
    new_folder_path = os.path.join(EXTRACT_PATH, new_folder_name)

    if os.path.exists(new_folder_path):
        logger.info(f"Replacing old version with new version: {new_folder_name}")
        for item in os.listdir(EXTRACT_PATH):
            item_path = os.path.join(EXTRACT_PATH, item)
            if item != new_folder_name and item != "bot.log":
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

        for item in os.listdir(new_folder_path):
            shutil.move(os.path.join(new_folder_path, item), EXTRACT_PATH)

        shutil.rmtree(new_folder_path)

def update_local_version(new_version):
    global LOCAL_VERSION
    LOCAL_VERSION = new_version
    with open(__file__, "r") as file:
        lines = file.readlines()
    with open(__file__, "w") as file:
        for line in lines:
            if line.startswith("LOCAL_VERSION"):
                file.write(f'LOCAL_VERSION = "{new_version}"\n')
            else:
                file.write(line)

def check_for_update():
    logger.info("Checking for updates...")
    latest_commit_sha = get_latest_commit()
    logger.info(f"Local version: {LOCAL_VERSION}")
    logger.info(f"Latest commit SHA: {latest_commit_sha}")

    if LOCAL_VERSION != latest_commit_sha:
        user_input = input(f"A new update is available. Do you want to update? (Y/N): ")
        if user_input.lower() == 'y':
            logger.info("Downloading update...")
            download_update(latest_commit_sha)
            logger.info(f"Extracting update from {DOWNLOAD_PATH}...")
            extract_update()
            logger.info("Replacing old version with new version...")
            replace_old_version(latest_commit_sha)
            update_local_version(latest_commit_sha)
            if os.path.exists(DOWNLOAD_PATH):
                os.remove(DOWNLOAD_PATH)
            logger.info("Update successful!")
        else:
            logger.info("Update canceled.")
    else:
        logger.info("You are already using the latest version.")
