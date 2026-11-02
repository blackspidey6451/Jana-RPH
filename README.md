# Jana RPH

Alat penjana RPH mingguan Pendidikan Islam (Tingkatan 1–5), format Jawi dengan logo KPM, satu RPH satu muka surat A4 (PDF).

| Fail | Isi |
|---|---|
| `jana_rph_mingguan.py` | Enjin penjana (Python 3 + Playwright Chromium, fon Jawi FreeSerif) |
| `dskp.json` | DSKP Pendidikan Islam KSSM T1–T5 (ejaan Jawi disemak) |
| `kpm_logo.png` | Logo header RPH |
| `konfigurasi.json` | Jadual kelas, bilangan murid, tingkatan, takwim minggu |
| `kemajuan.json` | SP terakhir setiap kelas (dikemas kini setiap kali RPH dijana) |

Guna:

```bash
python3 jana_rph_mingguan.py --alat . --pelan pelan.json --keluar output
```

Mod pelan: `teruskan` (sambung dari minggu lepas), `isi_semua` (SP setiap sesi), `isi_hari_pertama` (SP hari pertama, hari berikutnya anjak satu SP). Tambah `--uji` untuk pratonton tanpa mengemas kini `kemajuan.json`.
