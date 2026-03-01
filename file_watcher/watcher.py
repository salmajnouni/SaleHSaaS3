"""
SaleH SaaS - File Watcher Service
يراقب مجلد /data/incoming ويرفع الملفات الجديدة تلقائياً إلى Data Pipeline API
"""

import os
import time
import shutil
import logging
import requests
from pathlib import Path
from datetime import datetime

# ─── إعداد السجلات ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SaleH-Watcher] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("saleh_watcher")

# ─── الإعدادات ────────────────────────────────────────────────────────────────
INCOMING_DIR   = Path(os.getenv("INCOMING_DIR",   "/data/incoming"))
PROCESSED_DIR  = Path(os.getenv("PROCESSED_DIR",  "/data/processed"))
FAILED_DIR     = Path(os.getenv("FAILED_DIR",     "/data/failed"))
PIPELINE_URL   = os.getenv("PIPELINE_URL",        "http://salehsaas_pipeline:8001/process-file/")
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL",   "10"))   # ثواني بين كل فحص
SUPPORTED_EXTS = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".xlsx", ".pptx"}

# ─── إنشاء المجلدات إن لم تكن موجودة ─────────────────────────────────────────
for d in [INCOMING_DIR, PROCESSED_DIR, FAILED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

log.info("=" * 60)
log.info("SaleH Brain - File Watcher Service started")
log.info(f"Watching: {INCOMING_DIR}")
log.info(f"Pipeline: {PIPELINE_URL}")
log.info(f"Poll interval: {POLL_INTERVAL}s")
log.info("=" * 60)


def upload_file(filepath: Path) -> bool:
    """ترفع الملف إلى Data Pipeline API وتعيد True عند النجاح"""
    try:
        with open(filepath, "rb") as f:
            response = requests.post(
                PIPELINE_URL,
                files={"file": (filepath.name, f, "application/octet-stream")},
                timeout=300   # 5 دقائق للملفات الكبيرة
            )
        if response.status_code == 200:
            result = response.json()
            log.info(
                f"[OK] {filepath.name} → "
                f"{result.get('chunks_stored', '?')} chunks stored, "
                f"collection: {result.get('collection', '?')}"
            )
            return True
        else:
            log.error(f"[FAIL] {filepath.name} → HTTP {response.status_code}: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        log.error(f"[FAIL] Cannot connect to Pipeline API at {PIPELINE_URL}")
        return False
    except Exception as e:
        log.error(f"[FAIL] {filepath.name} → {e}")
        return False


def move_file(src: Path, dest_dir: Path) -> None:
    """ينقل الملف مع إضافة timestamp لتجنب التعارض"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"{timestamp}_{src.name}"
    shutil.move(str(src), str(dest))
    log.info(f"Moved: {src.name} → {dest_dir.name}/{dest.name}")


def check_pipeline_health() -> bool:
    """يتحقق من أن Pipeline API تعمل"""
    try:
        r = requests.get(PIPELINE_URL.replace("/process-file/", "/health"), timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def watch_loop():
    """الحلقة الرئيسية لمراقبة المجلد"""
    consecutive_failures = 0

    while True:
        try:
            # جمع الملفات المدعومة في مجلد incoming
            files = [
                f for f in INCOMING_DIR.iterdir()
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
            ]

            if files:
                log.info(f"Found {len(files)} file(s) to process...")

                for filepath in files:
                    # تحقق أن الملف لم يعد يُكتب (انتظر ثانيتين وتحقق من الحجم)
                    size_before = filepath.stat().st_size
                    time.sleep(2)
                    if not filepath.exists():
                        continue
                    size_after = filepath.stat().st_size
                    if size_before != size_after:
                        log.info(f"Skipping {filepath.name} - still being written...")
                        continue

                    log.info(f"Processing: {filepath.name} ({size_after:,} bytes)")

                    success = upload_file(filepath)

                    if success:
                        move_file(filepath, PROCESSED_DIR)
                        consecutive_failures = 0
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= 3:
                            log.warning(f"Moving {filepath.name} to failed/ after 3 attempts")
                            move_file(filepath, FAILED_DIR)
                            consecutive_failures = 0
                        else:
                            log.info(f"Will retry {filepath.name} next cycle...")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            log.info("Watcher stopped by user.")
            break
        except Exception as e:
            log.error(f"Unexpected error in watch loop: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    # انتظر حتى تصبح Pipeline API جاهزة
    log.info("Waiting for Pipeline API to be ready...")
    for attempt in range(30):
        if check_pipeline_health():
            log.info("Pipeline API is ready!")
            break
        log.info(f"Attempt {attempt + 1}/30 - Pipeline not ready yet, waiting 10s...")
        time.sleep(10)
    else:
        log.warning("Pipeline API not responding after 5 minutes, starting anyway...")

    watch_loop()
