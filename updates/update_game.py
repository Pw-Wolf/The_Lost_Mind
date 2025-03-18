import os
import re
import zipfile

import requests

import updates.constant
import core.exceptions as exceptions

new_version = None

game_exe = "The_Lost_Mind.exe"

game_folder = "data"


def download_game(end="zip"):
    download_link = f"https://github.com/Pw-Wolf/The_Lost_Mind/releases/download/{new_version}/The_Lost_Mind_{new_version}.{end}"
    save_path = os.path.join(os.getcwd(), "Update.{end}")
    r = requests.get(download_link)
    if r.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(r.content)
    elif r.status_code == 404 and end == "zip":
        download_game("7z")
    else:
        raise exceptions.DownloadError()


def check_updates():
    url = "https://github.com/Pw-Wolf/The_Lost_Mind/releases/latest"
    r = requests.get(url)
    global new_version
    new_version = float(re.search(r'tag/(\d+(\.\d+)+)', r.url).group(1))
    print(new_version)
    if new_version > updates.constant.VERSION:
        return True
    return False


def manipultion_files():
    with zipfile.ZipFile('Update.zip', 'r') as zip_ref:
        zip_ref.extractall()
    os.remove("Update.zip")
    os.rename(f"The_Lost_Mind_{new_version}", "update")
    raise exceptions.launchUpdate()


if __name__ == "__main__":
    check_updates()
    print(new_version)
