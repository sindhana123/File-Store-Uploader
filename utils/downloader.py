import os
import time
import shutil
import asyncio
import logging
import datetime as dt
import aiohttp
from utils.mega_download import download_mega_file, get_mega_file_info

logger = logging.getLogger(__name__)

DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

DOWNLOAD_MAX_RETRIES = 3
DOWNLOAD_RETRY_BACKOFF = 3

async def download_url_with_progress(url: str, output_path: str, progress_callback=None):
    last_error = None
    
    # -- Mega.nz --
    if "mega.nz" in url or "mega.co.nz" in url:
        for attempt in range(1, DOWNLOAD_MAX_RETRIES + 1):
            try:
                info = await get_mega_file_info(url)
                await download_mega_file(url, output_path, progress_callback=progress_callback)
                return output_path
            except asyncio.CancelledError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Mega attempt {attempt} failed: {e}")
                await asyncio.sleep(DOWNLOAD_RETRY_BACKOFF * attempt)
        raise RuntimeError(f"Mega.nz download failed after {DOWNLOAD_MAX_RETRIES} attempts: {last_error}")

    # -- Google Drive --
    if "drive.google.com" in url:
        is_folder = "/folders/" in url or "/drive/folders/" in url
        for attempt in range(1, DOWNLOAD_MAX_RETRIES + 1):
            try:
                tmp_gdrive_dir = output_path + "_gdrive_tmp"
                os.makedirs(tmp_gdrive_dir, exist_ok=True)
                
                gdown_cmd = ["gdown"]
                if is_folder: gdown_cmd.append("--folder")
                gdown_cmd.append(url)
                
                proc = await asyncio.create_subprocess_exec(
                    *gdown_cmd, cwd=tmp_gdrive_dir, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                _, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    if is_folder:
                        contents = os.listdir(tmp_gdrive_dir)
                        real_folder_name = next((i for i in contents if os.path.isdir(os.path.join(tmp_gdrive_dir, i))), None)
                        parent_dir = os.path.dirname(output_path)
                        moved_count = 0
                        for root, _, files in os.walk(tmp_gdrive_dir):
                            for name in files:
                                src = os.path.join(root, name)
                                dst = os.path.join(parent_dir, name)
                                base, ext = os.path.splitext(name)
                                c = 1
                                while os.path.exists(dst):
                                    dst = os.path.join(parent_dir, f"{base}_{c}{ext}")
                                    c += 1
                                shutil.move(src, dst)
                                moved_count += 1
                        shutil.rmtree(tmp_gdrive_dir, ignore_errors=True)
                        if moved_count > 0: return parent_dir
                    else:
                        files = os.listdir(tmp_gdrive_dir)
                        if files:
                            true_name = files[0]
                            shutil.move(os.path.join(tmp_gdrive_dir, true_name), output_path)
                            shutil.rmtree(tmp_gdrive_dir, ignore_errors=True)
                            return output_path
                            
                shutil.rmtree(tmp_gdrive_dir, ignore_errors=True)
                err_text = stderr.decode('utf-8', errors='ignore')
                raise RuntimeError(f"gdown code {proc.returncode}: {err_text}")
                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"GDrive attempt {attempt} failed: {e}")
                await asyncio.sleep(DOWNLOAD_RETRY_BACKOFF * attempt)
        raise RuntimeError(f"Google Drive downlod failed: {last_error}")

    # -- HTTP --
    for attempt in range(1, DOWNLOAD_MAX_RETRIES + 1):
        try:
            timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=60)
            async with aiohttp.ClientSession(headers=DOWNLOAD_HEADERS) as session:
                async with session.get(url, timeout=timeout, allow_redirects=True) as resp:
                    if resp.status >= 500 or resp.status in (403, 429):
                        raise RuntimeError(f"Failed with status {resp.status}")
                    if resp.status >= 400:
                        raise RuntimeError(f"Failed with status {resp.status}")

                    total = int(resp.headers.get("Content-Length", 0) or 0)
                    downloaded = 0
                    with open(output_path, "wb") as handle:
                        async for chunk in resp.content.iter_chunked(1024 * 64):
                            if not chunk: continue
                            handle.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                await progress_callback(downloaded, total)
                    if progress_callback:
                        await progress_callback(downloaded, total)
                    return output_path
        except asyncio.CancelledError:
            raise
        except Exception as e:
            last_error = e
            if attempt < DOWNLOAD_MAX_RETRIES:
                await asyncio.sleep(DOWNLOAD_RETRY_BACKOFF * attempt)
                
    raise RuntimeError(f"Download failed: {last_error}")
