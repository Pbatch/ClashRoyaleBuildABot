import os
import shutil
import subprocess
import zipfile
import time

from loguru import logger
import requests

class Updater:
    GITHUB_REPO = "Pbatch/ClashRoyaleBuildABot"
    DOWNLOAD_PATH = "update.zip"
    EXTRACT_PATH = "."
    IGNORE_DIRS = ["debug", ".git"]

    @staticmethod
    def _get_current_sha():
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        sha = result.stdout.strip()
        return sha

    def _get_latest_sha(self):
        url = f"https://api.github.com/repos/{self.GITHUB_REPO}/commits/main"
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        sha = response.json()["sha"]
        return sha

    def _download_update(self, commit_sha):
        url = f"https://github.com/{self.GITHUB_REPO}/archive/{commit_sha}.zip"
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        with open(self.DOWNLOAD_PATH, "wb") as file:
            file.write(response.content)

    def _extract_update(self):
        with zipfile.ZipFile(self.DOWNLOAD_PATH, "r") as zip_ref:
            zip_ref.extractall(self.EXTRACT_PATH)

    def _replace_old_version(self, commit_sha):
        new_folder_name = f"{self.GITHUB_REPO.rsplit('/', maxsplit=1)[-1]}-{commit_sha}"
        new_folder_path = os.path.join(self.EXTRACT_PATH, new_folder_name)

        if not os.path.exists(new_folder_path):
            return

        logger.info(f"Replacing old version with new version: {new_folder_name}")
        for item in os.listdir(self.EXTRACT_PATH):
            if item in {new_folder_name} | set(self.IGNORE_DIRS):
                continue
            item_path = os.path.join(self.EXTRACT_PATH, item)
            shutil.rmtree(item_path, ignore_errors=True)

        for item in os.listdir(new_folder_path):
            src_path = os.path.join(new_folder_path, item)
            dst_path = os.path.join(self.EXTRACT_PATH, item)
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
            else:
                if os.path.exists(dst_path):
                    os.remove(dst_path)
                shutil.copy2(src_path, dst_path)

        shutil.rmtree(new_folder_path)

    def check_for_update(self):
        logger.info("Checking for updates...")

        current_sha = self._get_current_sha()
        logger.info(f"Current commit SHA: {current_sha}")

        latest_sha = self._get_latest_sha()
        logger.info(f"Latest commit SHA: {latest_sha}")

        if current_sha == latest_sha:
            logger.info("You are already using the latest version.")
            return

        user_input = input(
            "A new update is available. Do you want to update? (Y/N): "
        )
        if user_input.lower() == "y":
            logger.info("Downloading update...")
            self._download_update(latest_sha)

            logger.info(f"Extracting update from {self.DOWNLOAD_PATH}...")
            self._extract_update()

            logger.info("Replacing old version with new version...")
            self._replace_old_version(latest_sha)
            if os.path.exists(self.DOWNLOAD_PATH):
                os.remove(self.DOWNLOAD_PATH)
            logger.info("Update successful!")
        else:
            logger.info("Update cancelled.")
