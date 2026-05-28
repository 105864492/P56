# scripts/download_data.py
import urllib.request
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.config import RAW_DIR, DBLP_GZ

DBLP_URL = "https://dblp.org/xml/dblp.xml.gz"

def download():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if DBLP_GZ.exists():
        print(f"Already exists: {DBLP_GZ}")
        return

    print(f"Downloading from {DBLP_URL} ...")
    print("This is ~1GB, might take a while depending on your connection.\n")

    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = downloaded / total_size * 100
        mb_done = downloaded / 1_000_000
        mb_total = total_size / 1_000_000
        print(f"\r  {percent:.1f}%  ({mb_done:.1f} / {mb_total:.1f} MB)", end="", flush=True)

    urllib.request.urlretrieve(DBLP_URL, DBLP_GZ, reporthook=progress)
    print(f"\nDone. Saved to {DBLP_GZ}")

if __name__ == "__main__":
    download()