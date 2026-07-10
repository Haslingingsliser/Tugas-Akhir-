# Analisis Eksposur Papan Iklan (Billboard Exposure Analysis) 

Repositori ini berisi kode untuk penelitian **Tugas Akhir** yang berfokus pada analisis eksposur papan iklan menggunakan visi komputer (Computer Vision). Sistem ini mendeteksi dan melacak objek (kendaraan dan pejalan kaki) yang melewati area paparan iklan, lalu menghitung total audiens secara otomatis.

## Identitas Penulis

- **Nama:** Abdurrahman Haidar Azfa
- **NIM:** 1227070003
- **Program Studi:** Teknik Elektro
- **Universitas:** UIN Sunan Gunung Djati

## Deskripsi Proyek

Proyek ini menggunakan model **YOLO (You Only Look Once)** untuk deteksi objek secara *real-time* atau melalui file video, yang dikombinasikan dengan algoritma pelacakan (*object tracking*) untuk memastikan tidak ada objek yang dihitung ganda.

Hasil perhitungan audiens (Kendaraan Roda 2, Kendaraan Roda 4, Kendaraan Besar, dan Pejalan Kaki) kemudian diekspor dan direkap secara otomatis ke **Google Sheets** menggunakan API sebagai log data atau pelaporan analitik berkelanjutan.

## Struktur Repositori

- `Code.py`: Skrip utama (Main script) untuk menjalankan deteksi, pelacakan (tracking), dan rekapitulasi data.

## Fitur Utama

1. **Deteksi Objek Spesifik:** Mengklasifikasikan objek ke dalam 4 kategori utama (Kendaraan Roda 2, Kendaraan Roda 4, Kendaraan Besar, Pejalan Kaki).
2. **Robust Object Tracking:** Mencegah penghitungan ganda (double-counting) pada objek yang sama.
3. **Dua Mode Deteksi:** *Real-Time Detection* (Kamera/OBS) dan *Video Detection*.
4. **Otomatisasi Laporan (Google Sheets Integration):** Menyimpan rekapitulasi jumlah audiens secara otomatis dan *real-time*.

## Persyaratan Sistem (Prerequisites)

Pastikan Anda telah menginstal Python (disarankan versi 3.8 - 3.11). Pustaka (*library*) yang dibutuhkan:

```bash
pip install ultralytics opencv-python gspread google-auth
