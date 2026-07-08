"""
Tugas Akhir - Analisis Eksposur Papan Iklan
YOLO + ByteTrack + Rekap ke Google Sheet
"""

import os
import time
from typing import Dict, List, Optional

import cv2
from ultralytics import YOLO

# ===================== CONFIG =====================
MODEL_PATH = r"D:\Fix_TA\runs\detect\train4\weights\best.pt"
OUT_DIR = r"D:\Fix_TA\HasilDeteksi_TRACK_MIN"

# Disesuaikan dengan hasil training dan inferensi CCTV
CONF_THRES = 0.15
IOU_THRES = 0.45
IMG_SIZE = 512

FRAME_STRIDE = 1
PRINT_PROGRESS_EVERY_N_FRAMES = 500

SHOW_PREVIEW = True
PREVIEW_WINDOW_NAME = "Tugas Akhir Analisis Eksposur Papan Iklan"
PREVIEW_WAIT_MS = 1

WRITE_OUTPUT_VIDEO = False
OBS_CAM_INDEX = 2

VIDEO_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".m4v", ".webm", ".mpeg", ".mpg", ".3gp"
}

# Mapping kelas hasil model ke kelas akhir yang dipakai untuk counting
CLASS_MAPPING = {
    "Sepeda": "Kendaraan Roda 2",
    "Kendaraan Roda 2": "Kendaraan Roda 2",
    "Kendaraan Roda 4": "Kendaraan Roda 4",
    "Kendaraan Besar": "Kendaraan Besar",
    "Pejalan Kaki": "Pejalan Kaki",
}

VALID_CLASSES = {
    "Kendaraan Roda 2",
    "Kendaraan Roda 4",
    "Kendaraan Besar",
    "Pejalan Kaki",
}

# ===== COUNT RULE =====
MIN_SEEN_FRAMES_TO_COUNT = 15
MAX_MISSED_SEC = 3.0
# ======================

# ========== GOOGLE SHEETS (SUMMARY ONLY) ==========
ENABLE_GOOGLE_SHEETS = True

SERVICE_ACCOUNT_JSON = r"D:\Fix_TA\tugas-akhir-484802-f094056b0f19.json"
SPREADSHEET_ID = "1Qe7RfVu3k-vb0HVIb1BXMUcilZJx-T0rR21yhHmn1Iw"
SHEET_NAME = "LOG_DETEKSI"
# ================================================


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def print_banner():
    print("[Tugas Akhir]")
    print("Model Analisis Eksposur Papan Iklan")
    print("")


def choose_mode() -> str:
    print("Pilihan:")
    print("1. Real Time Detection [Gunakan OBS]")
    print("2. Video Detection")
    print("")
    while True:
        choice = input("Masukkan pilihan (1/2): ").strip()
        if choice in ("1", "2"):
            return choice
        print("Hanya menerima input 1/2\n")


def ask_video_input_path() -> str:
    print("\n[Video Detection]")
    print("Masukan Path Directory Video / atau file video langsung")
    return input("Path: ").strip().strip('"')


def ask_lokasi(default_value: str = "") -> str:
    if default_value:
        s = input(f"Masukkan nama Lokasi (Enter untuk pakai default '{default_value}'): ").strip()
        return s if s else default_value
    return input("Masukkan nama Lokasi: ").strip()


def list_videos_from_path(path: str) -> List[str]:
    if os.path.isfile(path):
        return [path]
    if os.path.isdir(path):
        videos = []
        for root, _, files in os.walk(path):
            for fn in files:
                ext = os.path.splitext(fn)[1].lower()
                if ext in VIDEO_EXTS:
                    videos.append(os.path.join(root, fn))
        videos.sort()
        return videos
    raise FileNotFoundError(f"Path tidak ditemukan: {path}")


class GoogleSheetSummaryWriter:
    """
    Rekap FIXED ke kolom A-E:
    A=Lokasi, B=Roda_2, C=Roda_4, D=Kendaraan_Besar, E=Pejalan Kaki
    """

    def __init__(self):
        self.ws = None

    def connect(self):
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_JSON, scopes=scopes)
        gc = gspread.authorize(creds)

        sh = gc.open_by_key(SPREADSHEET_ID)

        try:
            all_titles = [w.title for w in sh.worksheets()]
            print("[GSHEET] All worksheets:", all_titles)
        except Exception:
            pass

        self.ws = sh.worksheet(SHEET_NAME)
        print(f"[GSHEET] Connected. Worksheet={repr(self.ws.title)}")

    @staticmethod
    def _norm(s: str) -> str:
        return (s or "").strip().lower()

    def _find_row_by_lokasi(self, lokasi: str) -> Optional[int]:
        if self.ws is None:
            return None

        lokasi_vals = self.ws.col_values(1)
        target = self._norm(lokasi)

        for i, v in enumerate(lokasi_vals, start=1):
            if i == 1:
                continue
            if self._norm(v) == target and target != "":
                return i
        return None

    def _find_first_empty_row_in_A(self) -> int:
        if self.ws is None:
            return 2

        lokasi_vals = self.ws.col_values(1)
        if len(lokasi_vals) < 2:
            return 2

        for row in range(2, len(lokasi_vals) + 1):
            if self._norm(lokasi_vals[row - 1]) == "":
                return row

        return len(lokasi_vals) + 1

    def upsert_summary(self, lokasi: str, r2: int, r4: int, besar: int, pejalan: int):
        if self.ws is None:
            return

        lokasi_clean = (lokasi or "").strip()
        values = [lokasi_clean, int(r2), int(r4), int(besar), int(pejalan)]

        target_row = self._find_row_by_lokasi(lokasi_clean)

        if target_row is None:
            target_row = self._find_first_empty_row_in_A()
            rng = f"A{target_row}:E{target_row}"
            self.ws.update(rng, [values], value_input_option="RAW")
            print(f"[GSHEET] INSERT row={target_row} -> {values}")
            return

        rng = f"A{target_row}:E{target_row}"
        self.ws.update(rng, [values], value_input_option="RAW")
        print(f"[GSHEET] UPDATE row={target_row} -> {values}")


def process_capture(
    cap: cv2.VideoCapture,
    model: YOLO,
    out_video_path: str,
    source_name: str,
    lokasi: str,
) -> Dict[str, int]:
    if not cap.isOpened():
        raise RuntimeError(f"Capture tidak bisa dibuka: {source_name}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if w <= 0 or h <= 0:
        w, h = 1280, 720

    writer = None
    if WRITE_OUTPUT_VIDEO:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(out_video_path, fourcc, fps, (w, h))
        if not writer.isOpened():
            raise RuntimeError("VideoWriter tidak bisa dibuka.")

    print(f"\n[Status] Source={source_name}")
    print(f"Lokasi={lokasi}")
    print(f"Fps={fps:.2f}, Frames={total_frames if total_frames > 0 else 'LIVE'}, Resolusi={w}x{h}")
    print("Classes:", model.names, "\n")

    seen_ids_by_cat = {k: set() for k in VALID_CLASSES}
    counted_ids_by_cat = {k: set() for k in VALID_CLASSES}

    track_age: Dict[int, int] = {}
    last_seen_time: Dict[int, float] = {}
    last_cat_by_id: Dict[int, str] = {}

    frame_idx = 0
    processed_idx = 0
    paused = False

    if SHOW_PREVIEW:
        cv2.namedWindow(PREVIEW_WINDOW_NAME, cv2.WINDOW_NORMAL)

    start_time = time.time()
    MAX_RUN_SEC = 300 if total_frames <= 0 else None  # live max 5 menit

    while True:
        if MAX_RUN_SEC is not None and (time.time() - start_time > MAX_RUN_SEC):
            print("Stop karena waktu habis")
            break

        if paused and SHOW_PREVIEW:
            key = cv2.waitKey(30) & 0xFF
            if key == ord("p"):
                paused = False
                print("Lanjutkan")
            elif key == ord("q"):
                print("Exit")
                break
            continue

        ok, frame = cap.read()
        if not ok:
            break

        frame_idx += 1
        if FRAME_STRIDE > 1 and (frame_idx % FRAME_STRIDE != 0):
            continue

        processed_idx += 1
        t_s = time.time() - start_time

        results = model.track(
            source=frame,
            conf=CONF_THRES,
            iou=IOU_THRES,
            imgsz=IMG_SIZE,
            persist=True,
            tracker="bytetrack_TA.yaml",
            verbose=False,
            device=0
        )

        r = results[0]
        annotated = r.plot()

        if r.boxes is not None and r.boxes.id is not None and len(r.boxes) > 0:
            ids = r.boxes.id.cpu().numpy().astype(int)
            clss = r.boxes.cls.cpu().numpy().astype(int)

            for track_id, cls_id in zip(ids, clss):
                raw_cat = str(model.names.get(int(cls_id), cls_id))

                if raw_cat not in CLASS_MAPPING:
                    continue

                cat = CLASS_MAPPING[raw_cat]

                if cat not in VALID_CLASSES:
                    continue

                prev_cat = last_cat_by_id.get(track_id)
                if prev_cat is not None and prev_cat != cat:
                    cat = prev_cat

                last_cat_by_id[track_id] = cat

                last_t = last_seen_time.get(track_id)
                if last_t is not None and (t_s - last_t) > MAX_MISSED_SEC:
                    track_age[track_id] = 0

                last_seen_time[track_id] = t_s
                track_age[track_id] = track_age.get(track_id, 0) + 1

                if track_age[track_id] < MIN_SEEN_FRAMES_TO_COUNT:
                    continue

                if track_id in counted_ids_by_cat[cat]:
                    continue

                counted_ids_by_cat[cat].add(track_id)
                seen_ids_by_cat[cat].add(track_id)

        if processed_idx % 60 == 0:
            expire = []
            for tid, lt in list(last_seen_time.items()):
                if (t_s - lt) > (MAX_MISSED_SEC * 3.0):
                    expire.append(tid)
            for tid in expire:
                last_seen_time.pop(tid, None)
                track_age.pop(tid, None)
                last_cat_by_id.pop(tid, None)

        unique_r2 = len(seen_ids_by_cat["Kendaraan Roda 2"])
        unique_r4 = len(seen_ids_by_cat["Kendaraan Roda 4"])
        unique_b = len(seen_ids_by_cat["Kendaraan Besar"])
        unique_p = len(seen_ids_by_cat["Pejalan Kaki"])
        total_unique_all = unique_r2 + unique_r4 + unique_b + unique_p

        overlay1 = f"Total={total_unique_all} | R2:{unique_r2} R4:{unique_r4} Besar:{unique_b} | Pejalan:{unique_p}"
        overlay2 = f"T={t_s:.2f}s Frame={frame_idx} (p=pause, q=quit)"

        (text_w, text_h), _ = cv2.getTextSize(overlay1, cv2.FONT_HERSHEY_SIMPLEX, 0.85, 2)
        cv2.rectangle(annotated, (10, 5), (10 + text_w + 10, 35), (0, 0, 0), -1)
        
        cv2.putText(annotated, overlay1, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)

        (text_w2, text_h2), _ = cv2.getTextSize(overlay2, cv2.FONT_HERSHEY_SIMPLEX, 0.70, 2)
        cv2.rectangle(annotated, (10, 40), (10 + text_w2 + 10, 75), (0, 0, 0), -1)
        
        cv2.putText(annotated, overlay2, (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.70, (255, 255, 255), 2, cv2.LINE_AA)

        if SHOW_PREVIEW:
            cv2.imshow(PREVIEW_WINDOW_NAME, annotated)
            key = cv2.waitKey(PREVIEW_WAIT_MS) & 0xFF
            if key == ord("q"):
                print("Exit = q")
                break
            elif key == ord("p"):
                paused = True
                print("Pause = P")

        if writer is not None:
            writer.write(annotated)

        if PRINT_PROGRESS_EVERY_N_FRAMES > 0 and (processed_idx % PRINT_PROGRESS_EVERY_N_FRAMES == 0):
            if total_frames > 0:
                progress = (frame_idx / max(1, total_frames)) * 100.0
                print(f"Progress: {progress:6.2f}% | Frame={frame_idx}/{total_frames} | Total={total_unique_all}")
            else:
                print(f"Live: Frame={frame_idx} | Total={total_unique_all}")

    cap.release()
    if writer is not None:
        writer.release()
    if SHOW_PREVIEW:
        cv2.destroyAllWindows()

    return {
        "Kendaraan Roda 2": len(seen_ids_by_cat["Kendaraan Roda 2"]),
        "Kendaraan Roda 4": len(seen_ids_by_cat["Kendaraan Roda 4"]),
        "Kendaraan Besar": len(seen_ids_by_cat["Kendaraan Besar"]),
        "Pejalan Kaki": len(seen_ids_by_cat["Pejalan Kaki"]),
    }


def main():
    print_banner()
    ensure_dir(OUT_DIR)

    model = YOLO(MODEL_PATH)

    sheet: Optional[GoogleSheetSummaryWriter] = None
    if ENABLE_GOOGLE_SHEETS:
        try:
            sheet = GoogleSheetSummaryWriter()
            sheet.connect()
        except Exception as e:
            print(f"[WARN] Google Sheets tidak bisa dipakai: {e}")
            sheet = None

    mode = choose_mode()

    if mode == "1":
        lokasi = ask_lokasi(default_value="OBS_Lokasi_1")
        cap = cv2.VideoCapture(OBS_CAM_INDEX, cv2.CAP_DSHOW)
        out_video_path = os.path.join(OUT_DIR, "OBS_bytetrack_min.mp4")

        counts = process_capture(
            cap=cap,
            model=model,
            out_video_path=out_video_path,
            source_name=f"OBS_CAM_INDEX={OBS_CAM_INDEX}",
            lokasi=lokasi,
        )

        print("[Result]", counts)
        if sheet is not None:
            sheet.upsert_summary(
                lokasi=lokasi,
                r2=counts["Kendaraan Roda 2"],
                r4=counts["Kendaraan Roda 4"],
                besar=counts["Kendaraan Besar"],
                pejalan=counts["Pejalan Kaki"],
            )

    else:
        input_path = ask_video_input_path()
        videos = list_videos_from_path(input_path)
        if not videos:
            print("Video not found.")
            return

        print(f"\nDitemukan {len(videos)} video.")
        for i, vp in enumerate(videos, 1):
            print(f"{i}. {vp}")
        print("")

        for vp in videos:
            base = os.path.splitext(os.path.basename(vp))[0]
            lokasi = ask_lokasi(default_value=base)

            cap = cv2.VideoCapture(vp)
            out_video_path = os.path.join(OUT_DIR, f"{base}_bytetrack_min.mp4")

            counts = process_capture(
                cap=cap,
                model=model,
                out_video_path=out_video_path,
                source_name=vp,
                lokasi=lokasi,
            )

            print("[Result]", lokasi, counts)

            if sheet is not None:
                sheet.upsert_summary(
                    lokasi=lokasi,
                    r2=counts["Kendaraan Roda 2"],
                    r4=counts["Kendaraan Roda 4"],
                    besar=counts["Kendaraan Besar"],
                    pejalan=counts["Pejalan Kaki"],
                )


if __name__ == "__main__":
    main()
