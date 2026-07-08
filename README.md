Analisis Eksposur Papan Iklan (Billboard Exposure Analysis) 
Repositori ini berisi kode sumber dan struktur direktori dataset untuk penelitian Tugas Akhir yang berfokus pada analisis eksposur papan iklan menggunakan visi komputer (Computer Vision). Sistem ini mendeteksi dan melacak objek (kendaraan dan pejalan kaki) yang melewati area paparan iklan, lalu menghitung total audiens secara otomatis.

🎓 Identitas Penulis
Nama: Abdurrahman Haidar Azfa

NIM: 1227070003

Program Studi: Teknik Elektro

Universitas: UIN Sunan Gunung Djati

📌 Deskripsi Proyek
Proyek ini menggunakan model YOLO (You Only Look Once) untuk deteksi objek secara real-time atau melalui file video, yang dikombinasikan dengan algoritma pelacakan (object tracking) untuk memastikan tidak ada objek yang dihitung ganda.

Hasil perhitungan audiens (Kendaraan Roda 2, Kendaraan Roda 4, Kendaraan Besar, dan Pejalan Kaki) kemudian diekspor dan direkap secara otomatis ke Google Sheets menggunakan API sebagai log data atau pelaporan analitik berkelanjutan.

🗂️ Struktur Repositori
Code.py: Skrip utama (Main script) untuk menjalankan deteksi, pelacakan (tracking), dan rekapitulasi data.

dataset/: Direktori untuk menyimpan dataset gambar/video Anda. (Catatan: Isi direktori ini dikosongkan pada repositori publik. Silakan letakkan file dataset Anda sendiri di sini).

✨ Fitur Utama
Deteksi Objek Spesifik: Mengklasifikasikan objek ke dalam 4 kategori utama (Kendaraan Roda 2, Kendaraan Roda 4, Kendaraan Besar, Pejalan Kaki).

Robust Object Tracking: Mencegah penghitungan ganda (double-counting) pada objek yang sama.

Dua Mode Deteksi: Real-Time Detection (Kamera/OBS) dan Video Detection.

Otomatisasi Laporan (Google Sheets Integration): Menyimpan rekapitulasi jumlah audiens secara otomatis dan real-time.

⚙️ Persyaratan Sistem (Prerequisites)
Pastikan Anda telah menginstal Python (disarankan versi 3.8 - 3.11). Pustaka (library) yang dibutuhkan:

Bash
pip install ultralytics opencv-python gspread google-auth
🚀 Konfigurasi & Cara Penggunaan
Sebelum menjalankan program, Anda wajib menyesuaikan beberapa pengaturan pada bagian # ===================== CONFIG ===================== di dalam file Code.py sesuai dengan lingkungan (environment) Anda sendiri.

1. Konfigurasi Model & Direktori Output
Python
# Ubah dengan path tempat Anda menyimpan model YOLO terbaik Anda (.pt)
MODEL_PATH = r"[ISI_DENGAN_PATH_MODEL_BEST.PT_ANDA]" 

# Ubah dengan path direktori tempat hasil video/log akan disimpan
OUT_DIR = r"[ISI_DENGAN_PATH_DIREKTORI_OUTPUT_ANDA]"
2. Pengaturan Batas Deteksi (Threshold)
Sesuaikan sensitivitas model berdasarkan kondisi rekaman atau CCTV Anda:

Python
CONF_THRES = 0.15  # Rentang Rekomendasi: 0.10 s/d 0.50 (Makin kecil makin sensitif)
IOU_THRES = 0.45   # Rentang Rekomendasi: 0.30 s/d 0.70 (Toleransi overlap box)
IMG_SIZE = 512     # Resolusi input model (Contoh: 320, 512, atau 640)
3. Pengaturan Pelacak (Tracker) & Device
Python
# Tentukan file konfigurasi tracker yang digunakan oleh Ultralytics
TRACKER_CONFIG = "[ISI_DENGAN_NAMA_FILE_TRACKER_ANDA]"  # Contoh: "bytetrack.yaml" atau "botsort.yaml"

# Tentukan device keras untuk menjalankan inferensi model
DEVICE_RUN = "[ISI_DENGAN_DEVICE_ANDA]"                 # Contoh: 0 atau "cuda" (GPU), atau "cpu"
4. Kamera / Jalur Input Real-Time
Python
# Tentukan indeks perangkat video cam/virtual cam yang terpasang
OBS_CAM_INDEX = [ISI_DENGAN_INDEX_KAMERA_ANDA]          # Contoh: 0, 1, atau 2
5. Integrasi Google Sheets API
Jika ENABLE_GOOGLE_SHEETS = True, siapkan kredensial akun layanan (Service Account) dari Google Cloud Console:

Python
# Masukkan path menuju file .json kredensial Service Account Anda
SERVICE_ACCOUNT_JSON = r"[ISI_DENGAN_PATH_FILE_JSON_ANDA]"

# Masukkan ID Spreadsheet (bisa diambil dari URL Google Sheets Anda)
SPREADSHEET_ID = "[ISI_DENGAN_ID_SPREADSHEET_ANDA]"

# Masukkan nama Sheet/Tab di dalam Spreadsheet Anda
SHEET_NAME = "[ISI_DENGAN_NAMA_SHEET_ANDA]"
⚠️ PENTING: Demi keamanan data pribadi, jangan pernah mengunggah file .json kredensial atau mencantumkan ID Spreadsheet asli Anda ke repositori publik GitHub. Masukkan file kredensial tersebut ke dalam .gitignore.

6. Menjalankan Program
Setelah semua nilai konfigurasi disesuaikan, jalankan skrip melalui terminal atau command prompt:

Bash
python Code.py
Ikuti instruksi menu di layar untuk memilih Mode Deteksi dan memasukkan nama lokasi papan iklan yang sedang dianalisis.
