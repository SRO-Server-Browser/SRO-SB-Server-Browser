import os
import json
import hashlib
import asyncio
import aiohttp
import tempfile
import shutil
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime
import time
import sys

class DownloadManager:
    def __init__(self, github_base_url, download_dir, parent=None):
        self.GITHUB_BASE_URL = github_base_url.rstrip('/') + '/'
        self.DOWNLOAD_DIR = os.path.abspath(download_dir)
        print(f"[DEBUG] DOWNLOAD_DIR set to: {self.DOWNLOAD_DIR}")
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        self.total_progress = 0.0
        self.parent = parent
        self.files = []

    async def fetch_manifest(self, session, filename):
        url = f"{self.GITHUB_BASE_URL}{filename}.manifest.json"
        print(f"[DEBUG] Fetching manifest: {url}")
        try:
            async with session.get(url, timeout=10) as resp:
                self.print_rate_limit_info(resp.headers)
                
                if resp.status == 200:
                    try:
                        return json.loads(await resp.text())
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] JSON decode error for {filename}: {e}")
                        if self.parent:
                            self.parent.console_box_insert(f"[ERROR] JSON decode error for {filename}: {e}\n")
                else:
                    print(f"[ERROR] Manifest fetch failed: {filename}, status: {resp.status}")
                    if self.parent:
                        self.parent.console_box_insert(f"[ERROR] Manifest fetch failed: {filename}, status: {resp.status}\n")
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            print(f"[ERROR] Network error fetching manifest: {filename}: {type(e).__name__}")
            if self.parent:
                self.parent.console_box_insert(f"[ERROR] Network error fetching manifest: {filename}: {type(e).__name__}\n")
        return None

    def print_rate_limit_info(self, headers):
        limit = headers.get("X-RateLimit-Limit", "unknown")
        remaining = headers.get("X-RateLimit-Remaining", "unknown")
        reset = headers.get("X-RateLimit-Reset", "unknown")
        print(f"[DEBUG] Rate limit: {remaining}/{limit}, reset at {reset}")

        if remaining != "unknown" and int(remaining) < 5:
            reset_time = int(reset)
            wait_seconds = reset_time - int(datetime.now().timestamp()) + 1
            if wait_seconds > 0:
                print(f"[WARNING] Rate limit low, waiting {wait_seconds} seconds")
                if self.parent:
                    self.parent.console_box_insert(f"[WARNING] Rate limit low, waiting {wait_seconds} seconds\n")
                time.sleep(wait_seconds)

    def local_hash(self, filepath):
        if not os.path.exists(filepath):
            return None
        h = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                h.update(chunk)
        return h.hexdigest()

    def get_local_part_hashes(self, filepath, part_size):
        if not os.path.exists(filepath):
            return []
        hashes = []
        with open(filepath, "rb") as f:
            index = 0
            while True:
                chunk = f.read(part_size)
                if not chunk:
                    break
                hashes.append({
                    "index": index,
                    "hash": hashlib.md5(chunk).hexdigest()
                })
                index += 1
        print(f"[DEBUG] Total local parts: {len(hashes)}")
        return hashes

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.RequestException)
    )
    def download_part(self, part_filename, target_path):
        url = f"{self.GITHUB_BASE_URL}{part_filename}"
        print(f"[!] Downloading: {part_filename}")
        if self.parent:
            self.parent.console_box_insert(f"[!] Downloading: {part_filename}\n")

        response = requests.get(url, stream=True, timeout=30)
        self.print_rate_limit_info(response.headers)

        if response.status_code in (200, 206):
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            start_time = time.time()

            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        inner_progress = (downloaded / total_size) * 100 if total_size > 0 else 0.0
                        elapsed_time = time.time() - start_time
                        speed = (downloaded / 1024) / elapsed_time if elapsed_time > 0 else 0.0
                        if self.parent:
                            self.parent.update_progress(self.total_progress, inner_progress, speed)
                        print(f"[process] {self.total_progress:.2f}% / {inner_progress:.2f}% / Speed: {speed:.2f} KB/s")
                        #if self.parent:
                        #    self.parent.console_box_insert(f"[process] {self.total_progress:.2f}% / {inner_progress:.2f}%\n")

            print(f"[+] Downloaded: {part_filename}")
            if self.parent:
                self.parent.console_box_insert(f"[+] Downloaded: {part_filename}\n")
        else:
            print(f"[X] Error {response.status_code}: {part_filename}")
            if self.parent:
                self.parent.console_box_insert(f"[X] Error {response.status_code}: {part_filename}\n")
            raise requests.RequestException(f"Status {response.status_code}")

        time.sleep(2)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((PermissionError, OSError))
    )
    def safe_remove(self, file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"[+] Removed file: {file_path}")
            if self.parent:
                self.parent.console_box_insert(f"[+] Removed file: {file_path}\n")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((PermissionError, OSError))
    )
    def safe_move(self, src_path, dst_path):
        shutil.move(src_path, dst_path)
        print(f"[+] Moved file: {src_path} -> {dst_path}")
        if self.parent:
            self.parent.console_box_insert(f"[+] Moved file: {src_path} -> {dst_path}\n")

    async def process_file(self, session, manifest_name):
        manifest = await self.fetch_manifest(session, manifest_name)
        if not manifest:
            print(f"[ERROR] Skipping {manifest_name} due to manifest error")
            if self.parent:
                self.parent.console_box_insert(f"[ERROR] Skipping {manifest_name} due to manifest error\n")
            return

        output_file_path = os.path.join(self.DOWNLOAD_DIR, manifest["file"])

        if self.handle_single_part_file(manifest, output_file_path):
            return

        local_hashes = self.get_local_part_hashes(output_file_path, manifest["part_size"])
        temp_files = self.download_missing_parts(manifest, local_hashes)
        
        if temp_files:
            self.merge_parts(manifest, output_file_path, temp_files)
            print(f"[!] Updated: {manifest['file']} ➜ {output_file_path}")
            if self.parent:
                self.parent.console_box_insert(f"[!] Updated: {manifest['file']} ➜ {output_file_path}\n")
        else:
            print(f"[!] No changes needed: {manifest['file']}")
            if self.parent:
                self.parent.console_box_insert(f"[!] No changes needed: {manifest['file']}\n")

        self.total_progress += 100.0 / (len(self.files) - 1) if len(self.files) > 1 else 100.0
        if self.parent:
            self.parent.update_progress(self.total_progress, 0.0)
        print(f"[process] {self.total_progress:.2f}% / {0:.2f}%")
        if self.parent:
            self.parent.console_box_insert(f"[process] {self.total_progress:.2f}% / {0:.2f}%\n")

    def handle_single_part_file(self, manifest, output_path):
        if len(manifest["parts"]) == 1 and manifest["file"] == manifest["parts"][0]["filename"]:
            if self.local_hash(output_path) == manifest["parts"][0]["hash"]:
                print(f"[=] Skipped (hash matches): {manifest['file']}")
                if self.parent:
                    self.parent.console_box_insert(f"[=] Skipped (hash matches): {manifest['file']}\n")
                return True
                
            self.download_part(manifest["file"], output_path)
            print(f"[!] Downloaded: {manifest['file']} ➜ {output_path}")
            if self.parent:
                self.parent.console_box_insert(f"[!] Downloaded: {manifest['file']} ➜ {output_path}\n")
            return True
        return False

    def download_missing_parts(self, manifest, local_hashes):
        temp_files = {}
        for part in manifest["parts"]:
            filename = part["filename"]
            expected_hash = part["hash"]
            
            try:
                part_index = int(filename.split(".part")[-1]) - 1
            except ValueError:
                print(f"[X] Invalid part filename: {filename}")
                if self.parent:
                    self.parent.console_box_insert(f"[X] Invalid part filename: {filename}\n")
                continue

            if self.is_part_needed(local_hashes, part_index, expected_hash):
                temp_path = self.create_temp_file()
                self.download_part(filename, temp_path)
                temp_files[filename] = temp_path
        return temp_files

    def is_part_needed(self, local_hashes, part_index, expected_hash):
        local_part_hash = next(
            (h["hash"] for h in local_hashes if h["index"] == part_index),
            None
        )
        return local_part_hash != expected_hash

    def create_temp_file(self):
        temp_file = tempfile.NamedTemporaryFile(delete=False, dir=self.DOWNLOAD_DIR)
        temp_path = temp_file.name
        temp_file.close()
        return temp_path

    def merge_parts(self, manifest, output_path, temp_files):
        tmp_path = output_path + ".tmp"
        self.create_backup(output_path, tmp_path)
        
        with open(tmp_path, "r+b") as output_file:
            for part in manifest["parts"]:
                if temp_path := temp_files.get(part["filename"]):
                    self.write_part_to_file(part, temp_path, output_file, manifest["part_size"])

        self.validate_and_finalize(manifest, output_path, tmp_path, temp_files)

    def create_backup(self, output_path, tmp_path):
        if os.path.exists(output_path):
            shutil.copyfile(output_path, tmp_path)
        else:
            open(tmp_path, "wb").close()

    def write_part_to_file(self, part, temp_path, output_file, part_size):
        try:
            part_index = int(part["filename"].split(".part")[-1]) - 1
        except ValueError:
            return
            
        if os.path.exists(temp_path):
            with open(temp_path, "rb") as pf:
                output_file.seek(part_index * part_size)
                output_file.write(pf.read())

    def validate_and_finalize(self, manifest, output_path, tmp_path, temp_files):
        final_size = os.path.getsize(tmp_path)
        if final_size != manifest["original_size"]:
            print(f"[ERROR] Size mismatch: expected {manifest['original_size']}, got {final_size}")
            if self.parent:
                self.parent.console_box_insert(f"[ERROR] Size mismatch: expected {manifest['original_size']}, got {final_size}\n")
            return

        for temp_path in temp_files.values():
            try:
                self.safe_remove(temp_path)
            except (PermissionError, OSError) as e:
                print(f"[ERROR] Failed to remove temp file: {e}")
                if self.parent:
                    self.parent.console_box_insert(f"[ERROR] Failed to remove temp file: {e}\n")

        try:
            self.safe_move(tmp_path, output_path)
        except (PermissionError, OSError) as e:
            print(f"[ERROR] Failed to finalize file: {e}")
            if self.parent:
                self.parent.console_box_insert(f"[ERROR] Failed to finalize file: {e}\n")

    def get_manifest_files(self):
        repo = self.GITHUB_BASE_URL.split("/")[-3]
        print(f"[DEBUG] Repository name: {repo}")
        api_url = f"https://api.github.com/repos/kantrveysel/{repo}/contents/"
        print(f"[DEBUG] API URL: {api_url}")
        try:
            response = requests.get(api_url, timeout=10)
            print(f"[DEBUG] API response status: {response.status_code}")
            if response.status_code == 200:
                files = [f['name'] for f in response.json() if f['name'].endswith('.manifest.json')]
                print(f"[DEBUG] Found manifest files: {files}")
                return files
            else:
                print(f"[ERROR] API request failed: {response.status_code} - {response.text}")
                if self.parent:
                    self.parent.console_box_insert(f"[ERROR] API request failed: {response.status_code} - {response.text}\n")
                return []
        except requests.RequestException as e:
            print(f"[ERROR] API request exception: {str(e)}")
            if self.parent:
                self.parent.console_box_insert(f"[ERROR] API request exception: {str(e)}\n")
            return []

    def get_files_to_sync(self):
        self.files = [manifest.replace('.manifest.json', '') for manifest in self.get_manifest_files()]
        print(f"[DEBUG] Files to sync: {self.files}")
        return self.files