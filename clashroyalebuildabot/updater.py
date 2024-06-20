import os
import requests
import zipfile
from subprocess import check_output

class Updater:
    GITHUB_REPO = "Pbatch/ClashRoyaleBuildABot"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"
    
    def _get_current_sha(self):
        return check_output(["git", "rev-parse", "HEAD"]).strip().decode()

    def _get_latest_sha(self):
        response = requests.get(f"{self.API_URL}/commits/main")
        response.raise_for_status()
        return response.json()["sha"]

    def _get_changed_files(self, old_sha, new_sha):
        url = f"{self.API_URL}/compare/{old_sha}...{new_sha}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return [file['filename'] for file in data['files']]

    def _download_and_replace_files(self, files):
        for file_info in files:
            file_path = file_info['filename']
            if file_info['status'] == 'removed':
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Removed {file_path}")
            else:
                url = f"https://raw.githubusercontent.com/{self.GITHUB_REPO}/main/{file_path}"
                response = requests.get(url)
                if response.status_code == 200:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    print(f"Updated {file_path}")
                else:
                    print(f"Failed to download {file_path}")

    def check_for_update(self):
        print("Checking for updates...")
        current_sha = self._get_current_sha()
        latest_sha = self._get_latest_sha()

        if current_sha == latest_sha:
            print("You are already using the latest version.")
            return

        print("A new update is available.")
        if input("Do you want to update? (Y/N): ").lower() == 'y':
            changed_files = self._get_changed_files(current_sha, latest_sha)
            self._download_and_replace_files(changed_files)
            print("Update successful!")
        else:
            print("Update cancelled.")
