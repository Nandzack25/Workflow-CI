# Panduan Sistem Monitoring dan Logging

Panduan ini berisi langkah-langkah untuk menjalankan serving model, monitoring dengan Prometheus, visualisasi dengan Grafana, serta pembuatan Alerting Rules (untuk memenuhi Kriteria 4 dari Basic hingga Advanced).

---

## 1. Persiapan Dependensi
Instal dependensi Python yang dibutuhkan untuk Exporter dan Traffic Simulator:
```bash
pip install flask prometheus-client requests psutil pandas
```

---

## 2. Langkah-Langkah Menjalankan Sistem

### Langkah A: Serving Model MLflow
Pastikan model hasil retraining Anda sudah ada di tracking server (mlruns). Jalankan perintah berikut untuk melakukan serving model di port `8080`:
```bash
# Ganti <RUN_ID> dengan RUN_ID model teraktif Anda (dapat dilihat di mlruns atau run_id.txt)
mlflow models serve -m "runs:/<RUN_ID>/random_forest_model" -p 8080 --env-manager=local
```
*Setelah berjalan, ambil tangkapan layar terminal serving ini untuk disimpan sebagai **`1.bukti_serving`**.*

### Langkah B: Jalankan Prometheus Exporter Proxy
Jalankan script `3.prometheus_exporter.py` untuk memulai Flask server di port `8000`. Server ini bertindak sebagai jembatan yang meneruskan request inferensi ke model serve (port `8080`) sekaligus merekam 12 metrik sistem dan machine learning.
```bash
python 3.prometheus_exporter.py
```

### Langkah C: Jalankan Traffic Simulator (Inference)
Jalankan script `7.inference.py` untuk mengirim data inferensi acak secara terus-menerus ke proxy endpoint setiap 1 detik. Ini akan menghasilkan lalu lintas data (traffic) untuk memperbarui metrik secara real-time.
```bash
python 7.inference.py
```

### Langkah D: Jalankan Prometheus
Pastikan Anda sudah menginstal Prometheus di komputer Anda (atau jalankan via Docker). 
1. Jalankan Prometheus dengan menggunakan file konfigurasi `2.prometheus.yml`:
   ```bash
   prometheus --config.file=2.prometheus.yml
   ```
2. Buka browser dan akses `http://localhost:9090`.
3. Buka tab **Status > Targets** dan pastikan target `mlflow-model` berstatus **UP**.
4. Cari metrik seperti `ml_requests_total` di search bar Prometheus untuk melihat data terkumpul.
5. *Ambil tangkapan layar grafik Prometheus Anda, lalu simpan ke folder **`4.bukti monitoring Prometheus`** dengan nama seperti `1.monitoring_requests_total`, `2.monitoring_predicted_score_mean`, dll.*

### Langkah E: Jalankan Grafana & Impor Dashboard
1. Jalankan Grafana (biasanya di `http://localhost:3000`).
2. Tambahkan Data Source baru: **Prometheus** dengan URL `http://localhost:9090` (atau `http://host.docker.internal:9090` jika Grafana berjalan di dalam Docker).
3. Pilih menu **Dashboards > New > Import**.
4. Upload file **`grafana_dashboard.json`** yang telah disediakan di folder ini.
5. **PENTING (Syarat Penilaian)**: Ganti nama Dashboard dengan format **`[Username Dicoding Anda] - Student Performance Monitoring`** agar nama akun Dicoding Anda masuk ke dalam tangkapan layar.
6. *Simpan tangkapan layar panel-panel dashboard Grafana ke folder **`5.bukti monitoring Grafana`** dengan nama seperti `1.monitoring_requests`, `2.monitoring_predicted_score`, dll.*

---

## 3. Konfigurasi Alerting Grafana (Advanced - Minimal 3 Alert)
Untuk mencapai level **Advanced**, Anda perlu membuat 3 aturan peringatan (Alerting Rules) di Grafana:

### Alert 1: High Error Rate
* **Tujuan**: Memicu peringatan jika terjadi error pada model/sistem.
* **Query**: `sum(rate(ml_prediction_errors_total[1m])) > 0`
* **Ketentuan**: Evaluasi setiap 1 menit. Jika nilai di atas 0, kirim alert.

### Alert 2: High Request Latency
* **Tujuan**: Memicu peringatan jika waktu respon inferensi melambat.
* **Query**: `rate(ml_request_latency_seconds_sum[1m]) / rate(ml_request_latency_seconds_count[1m]) > 0.5`
* **Ketentuan**: Jika rata-rata latency di atas 0.5 detik dalam 1 menit, kirim alert.

### Alert 3: Low Average Predicted Score
* **Tujuan**: Memicu peringatan jika kualitas/rata-rata nilai siswa yang diprediksi menurun secara drastis (misal di bawah nilai kelulusan 50).
* **Query**: `ml_predicted_score_mean < 50`
* **Ketentuan**: Jika nilai rata-rata prediksi di bawah 50, kirim alert.

### Cara Mengambil Bukti Alerting:
1. Tangkap layar halaman detail konfigurasi untuk masing-masing aturan alert di Grafana UI. Simpan di folder **`6.bukti alerting Grafana`** dengan nama seperti **`1.rules_error_rate`**, **`3.rules_latency`**, dan **`5.rules_low_score`**.
2. Trigger alert tersebut agar menyala (misal matikan sementara model serve untuk memicu Error Rate Alert). Hubungkan Grafana ke notifikasi channel (seperti Discord, Slack, atau Email). Tangkap layar notifikasi yang masuk, lalu simpan di folder **`6.bukti alerting Grafana`** dengan nama **`2.notifikasi_error_rate`**, **`4.notifikasi_latency`**, dan **`6.notifikasi_low_score`**.

---

## 4. Struktur Output yang Harus Dikumpulkan
Pastikan repositori Anda terstruktur seperti ini sebelum dikumpulkan:
```
Monitoring dan Logging
├── 1.bukti_serving.png (atau .jpg)
├── 2.prometheus.yml
├── 3.prometheus_exporter.py
├── 4.bukti monitoring Prometheus (folder)
    └── 1.monitoring_requests_total.png
    └── 2.monitoring_predicted_score_mean.png
    └── ... (minimal 3 metrik berbeda)
├── 5.bukti monitoring Grafana (folder)
    └── 1.monitoring_requests_total.png
    └── 2.monitoring_predicted_score_mean.png
    └── ... (minimal 10 metrik berbeda untuk Advanced)
├── 6.bukti alerting Grafana (folder)
    └── 1.rules_error_rate.png
    └── 2.notifikasi_error_rate.png
    └── 3.rules_latency.png
    └── 4.notifikasi_latency.png
    └── 5.rules_low_score.png
    └── 6.notifikasi_low_score.png
├── 7.inference.py
```
