#!/usr/bin/env python3
"""Jana RPH mingguan Pendidikan Islam (format Jawi, logo KPM, 1 RPH = 1 muka surat A4) -> PDF.

Guna:  python3 jana_rph_mingguan.py --alat <folder _alat> --pelan pelan.json --keluar <folder output> [--uji]
Folder _alat mesti ada: dskp.json, kpm_logo.png, konfigurasi.json, kemajuan.json
--uji : jana PDF tetapi JANGAN kemas kini kemajuan.json
Perlu: Python 3, playwright (python) dengan Chromium, fon FreeSerif (atau fon Jawi lain) dipasang.
"""
import json, re, random, datetime as D, base64, html, argparse, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("--alat", required=True); ap.add_argument("--pelan", required=True); ap.add_argument("--keluar", required=True)
ap.add_argument("--uji", action="store_true")
A = ap.parse_args()
J = lambda n: os.path.join(A.alat, n)
DSKP = json.load(open(J("dskp.json"), encoding="utf-8"))
for x in DSKP:
    for s in x["sk"]:
        s[0] = re.sub(r"(مروموس) \1", r"\1", s[0])
KONF = json.load(open(J("konfigurasi.json"), encoding="utf-8"))
KEM = json.load(open(J("kemajuan.json"), encoding="utf-8"))
PELAN = json.load(open(A.pelan, encoding="utf-8"))
random.seed(PELAN.get("benih", int(D.date.today().strftime("%Y%m%d"))))

BIDANG = {"quran": "القرءان", "hadis": "حديث", "akidah": "عقيدة", "ibadah": "عبادة / فقه", "sirah": "سيرة دان تمدون إسلام", "akhlak": "اخلاق إسلامية"}
HARI_J = ["اثنين", "ثلاث", "رابو", "خميس", "جمعة", "سبتو", "احد"]
HARI_R = ["Isnin", "Selasa", "Rabu", "Khamis", "Jumaat", "Sabtu", "Ahad"]

def tsort(t):
    h, m = map(int, t.replace(":", ".").split("."))
    return (h + 12 if h < 7 else h) * 60 + m

def gilir(kelas):
    """Senarai SP mengikut susunan DSKP untuk tingkatan dalam konfigurasi (kitaran berulang)."""
    out = []
    for t in KONF["gilir_dskp"][kelas]:
        for x in DSKP:
            if x["t"] != t: continue
            for k, sps in x["sk"]:
                for p in sps:
                    out.append(dict(g=x["g"], tj=x["tj"], sk=k, sp=p))
    return out

def cari_sp(kelas, kod):
    """Indeks SP dalam gilir kelas. kod = '3.7.1' (nombor SP) atau '3.7' (SP pertama dalam SK) atau sebahagian teks."""
    q = gilir(kelas); kod = str(kod).strip()
    for i, it in enumerate(q):
        if re.match(r"\s*" + re.escape(kod) + r"(?![\d.])", it["sp"]): return i
    for i, it in enumerate(q):
        if re.match(r"\s*" + re.escape(kod) + r"(?![\d.])", it["sk"]): return i
    for i, it in enumerate(q):
        if kod and kod in it["sp"]: return i
    raise SystemExit(f"SP/SK '{kod}' tidak dijumpai dalam DSKP Tingkatan {KONF['gilir_dskp'][kelas]} untuk kelas {kelas}")

def minggu_label(d):
    if PELAN.get("minggu"): return PELAN["minggu"]
    w = None
    for s, m in sorted(KONF.get("takwim", {}).items()):
        if s <= d.isoformat(): w = m
    return w or "—"

# ---- templates (same Jawi wording as the app)
def strip_no(p): return re.sub(r'^\s*\d+(\.\d+)*\.?\s*', '', p).strip()
def sp_no(p):
    m = re.match(r'^\s*(\d+(\.\d+)+)', p); return m.group(1) if m else ''
def ringkas(p):
    t = re.sub(r'\s*سچارا برادب دان استقامة\.?\s*$', '', strip_no(p))
    c = t.find(':')
    if c > 15: t = t[:c]
    w = t.split()
    if len(w) > 14: t = ' '.join(w[:14]) + ' …'
    return re.sub(r'[.\s،,:]+$', '', t)
VERB = [
 (["ممباچ", "مباچ"], "سچارا تلقي مشافهه برسام ݢورو، دايكوتي باچاءن سچارا كلس، كومڤولن دان ايندۏيدو"),
 (["مڠحفظ", "حفظ"], "سچارا برڤاسڠن، كمودين تسميع كڤد ݢورو"),
 (["مڽاتاكن", "مڽبوت", "مڠنل"], "ملالوءي سسي سؤال جواب دان اكتيۏيتي Think-Pair-Share"),
 (["منرڠكن", "منرڠ", "مڠموكاكن", "مڠورايكن", "مڽنارايكن", "ممبيذاكن"], "دالم كومڤولن مڠݢوناكن ڤتا i-Think، كمودين ممبنتڠكن حاصيل ڤربينچڠن"),
 (["منجلسكن", "منجلس"], "ملالوءي ڤربينچڠن كومڤولن دان اكتيۏيتي Gallery Walk"),
 (["مڠهورايكن"], "دڠن مڠحاصيلكن ڤتا ميندا سچارا بركومڤولن"),
 (["مروموسكن", "مروموس"], "دالم بنتوق ڤتا ڤوكوق دان ممبنتڠكنڽ د هادڤن كلس"),
 (["مڠهوبوڠ"], "ملالوءي چونتوه سيتواسي دالم كهيدوڤن سهارين يڠ دبينچڠكن برسام ݢورو"),
 (["ملقسان", "ملاكوكن", "منونجوقكن", "مڠعملكن", "منونايكن"], "ملالوءي ديمونستراسي ݢورو، دايكوتي عملي اوليه موريد سچارا بركومڤولن"),
 (["مننتوكن", "مڠلسكن"], "ملالوءي لاتيهن مڠنل ڤستي دالم تيک دان كد ايمبسن"),
 (["برعزم", "براوسها", "منجاءوهي", "منانمكن", "مڠحياتي", "سڠݢوڤ", "ميقيني", "ملازيمي", "منجاݢ", "مڽاكيني", "مڽمڤورناكن", "منچونتوهي", "ممبينا",
   "مڠحرمتي", "برتڠݢوڠجواب", "منيڠݢلكن", "برايتيݢريتي", "ممولاكن", "ممستيكن", "برڤݢڠ", "برشوكور", "ڤكا", "منچينتاءي", "مموڤوق", "مڠهرݢاي",
   "برحكمه", "مڠلقكن", "مڠيمارهكن", "ممنفعتكن", "ممڤرباءيقي", "ممڤرباڽقكن", "مڽانتوني", "برصلاوة", "استقامة", "مڠوكاكن", "منديديق", "ممباڠون",
   "بيجقسان", "رضا", "سنتياس"], "ملالوءي ريفليكسي كنديري دان ايقرار برسام د اخير سسي"),
]
def kaedah(p):
    w = strip_no(p)
    for keys, k in VERB:
        if any(w.startswith(x) for x in keys): return k
    return "ملالوءي ڤربينچڠن كومڤولن"
def kaedah_ulang(p):
    w = strip_no(p)
    if any(w.startswith(x) for x in ["ممباچ", "مڠحفظ", "حفظ"]): return "ملالوءي باچاءن برتلقي دان تسميع برسام راكن"
    if any(w.startswith(x) for x in ["ملقسان", "ملاكوكن", "منونايكن"]): return "ملالوءي سسي سؤال جواب دان تونجوق چارا ريڠكس"
    return random.choice(["ملالوءي ڤتا i-Think دان سسي سؤال جواب", "ملالوءي اكتيۏيتي Round Robin دالم كومڤولن", "ملالوءي نوتا ريڠكس دان كويز ڤنتس"])
INDUKSI = {
 "quran": "ݢورو ممڤردڠركن باچاءن {t} اوليه قاري، كمودين موريد مڽبوت سمولا ڤركاتاءن يڠ دڠر.",
 "hadis": "ݢورو ممڤاڤركن سيتواسي بركاءيتن تاجوق {t} دان برسؤال جواب دڠن موريد تنتڠ ڤڠالمن مريك.",
 "akidah": "ݢورو ممڤاڤركن ݢمبر كجادين عالم دان برسؤال جواب تنتڠ ككواساءن الله سبلوم ممڤركنلكن تاجوق {t}.",
 "ibadah": "ݢورو برسؤال جواب دڠن موريد تنتڠ ڤڠالمن مريك بركاءيتن {t}.",
 "sirah": "ݢورو منايڠكن ۏيديو ڤينديق اتاو ڤتا لوكاسي بركاءيتن {t}، دان موريد مڽاتاكن اڤ يڠ دليهت.",
 "akhlak": "ݢورو ممڤاڤركن سيتواسي اتاو كيس بركاءيتن {t}، دان موريد مڽواراكن ڤندڠن مريك.",
}
PENUTUP = "موريد مروموسكن ايسي ڤلاجرن دڠن بيمبيڠن ݢورو دان مڽاتاكن نيلاي يڠ دڤروليهي. ݢورو ممبري لاتيهن ڤڠوكوهن."
LATIHAN = "موريد ملڠكڤكن لمبارن كرجا بركاءيتن ايسي ڤلاجرن."

def refleksi(a, n, sps):
    pc = round(a / n * 100); c = n - a
    names = [ringkas(p) for p in sps]
    sp = names[0] if len(names) == 1 else '، '.join(names[:-1]) + ' دان ' + names[-1]
    t = f"{a} درڤد {n} موريد ({pc}%) داڤت {sp}."
    if c == 0: t += " سموا موريد منچاڤاي اوبجيكتيف. اكتيۏيتي ڤڠاياءن دبريكن اونتوق مڠوكوهكن ڤمهمن."
    elif pc >= 80: t += f" اكتيۏيتي ڤڠاياءن دبريكن كڤد موريد يڠ منچاڤاي اوبجيكتيف. {c} موريد يڠ بلوم منچاڤاي اوبجيكتيف دبري بيمبيڠن دان لاتيهن تمبهن."
    elif pc >= 50: t += f" {c} موريد يڠ بلوم منچاڤاي اوبجيكتيف اكن دبري لاتيهن ڤموليهن ڤد ڤدڤچ بريكوتڽ."
    else: t += " كباڽقكن موريد بلوم منچاڤاي اوبجيكتيف. ڤدڤچ اكن دأولڠ ڤد سسي بريكوتڽ دڠن ڤندكتن يڠ لبيه موده دان بيمبيڠن رافت."
    return t, pc


def uniq(seq):
    out = []
    for s in seq:
        if s not in out: out.append(s)
    return out

def rph_khas(kelas, d, mula, tamat, nota, info):
    rows = info + [("كوريكولوم", None), ("ڤدڤچ تيدق دجالنكن", [nota]),
                   ("چاتتن", ["ستندرد ڤمبلاجرن يڠ درانچڠ اكن دسمبوڠ ڤد ڤدڤچ بريكوتڽ."])]
    return dict(rows=rows)

def rph_biasa(kelas, items, ulang, info):
    ting = str(KONF["tingkatan"][kelas])
    sps = [it["sp"] for it in items]
    tj = uniq([("اولڠكاجي: " if ulang else "") + it["tj"] for it in items])
    sks = uniq([it["sk"] for it in items]); bid = uniq([BIDANG[it["g"]] for it in items])
    obj = ["ڤد اخير ڤڠاجرن دان ڤمبلاجرن، موريد داڤت:"] + [f"{k + 1}. {strip_no(p)}" for k, p in enumerate(sps)]
    exam = KONF.get("peperiksaan", {}).get(ting, "UASA" if ting in "123" else "SPM")
    if ulang:
        ind = f"ݢورو مڠيمبس كمبالي تاجوق {items[0]['tj']} ملالوءي سؤال جواب ڤنتس دان مڽاتاكن فوكوس اولڠكاجي هاري اين."
        steps = [f"موريد مڠولڠكاجي {ringkas(p)} {kaedah_ulang(p)}." for p in sps]
        steps.append(f"موريد منجواب سوءالن اولڠكاجي برفورمت {exam} دان ممبينچڠكن جواڤن برسام ݢورو.")
        pen = f"موريد مروموسكن ايسي ڤنتيڠ يڠ دأولڠكاجي. ݢورو ممبري لاتيهن تمبهن سباݢاي ڤرسدياءن {exam}."
    else:
        ind = INDUKSI[items[0]["g"]].format(t=items[0]["tj"])
        steps = [f"موريد {ringkas(p)} {kaedah(p)}." for p in sps] + [LATIHAN]
        pen = PENUTUP
    n = int(KONF["bil_murid"][kelas]); a = min(n, max(1, round(n * random.uniform(0.72, 0.95))))
    rf, pc = refleksi(a, n, sps)
    rows = info + [("كوريكولوم", None), ("بيدڠ", [" / ".join(bid)]), ("تاجوق", tj), ("ستندرد كندوڠن", sks), ("ستندرد ڤمبلاجرن", sps),
                   ("اوبجيكتيف ڤمبلاجرن", obj), ("اكتيۏيتي ڤدڤچ", None), ("ڤرمولاءن", [ind]),
                   ("اكتيۏيتي اوتام", [f"{k + 1}. {s}" for k, s in enumerate(steps)]), ("ڤنوتوڤ", [pen]),
                   ("ريفليكسي", None), ("ڤنچاڤاين", [f"{a} درڤد {n} موريد ({pc}%) منچاڤاي اوبجيكتيف"]), ("چاتتن", [rf])]
    return dict(rows=rows)

# ---------- susun sesi minggu ini ----------
tarikh = [D.date.fromisoformat(t) for t in PELAN["tarikh"]]
khas = {}
for k in PELAN.get("khas", []):
    for t in ([k["tarikh"]] if isinstance(k["tarikh"], str) else k["tarikh"]):
        khas.setdefault(t, []).append(k)
sesi = []
for d in sorted(tarikh):
    for kelas, mula, tamat in sorted(KONF["jadual"].get(HARI_R[d.weekday()], []), key=lambda r: tsort(r[1])):
        sesi.append((d, kelas, mula, tamat))

RPH = []; laporan = []
kem_baru = json.loads(json.dumps(KEM))
for kelas in sorted({s[1] for s in sesi}):
    pk = PELAN.get("kelas", {}).get(kelas, {"mod": "teruskan"})
    mod = pk.get("mod", "teruskan")
    st = kem_baru.setdefault(kelas, {"mula": 0, "saiz": 3, "langkah": "sambung3", "ulangkaji": False})
    q = gilir(kelas); L = len(q)
    if mod != "teruskan":
        st["ulangkaji"] = bool(pk.get("ulangkaji", False))
    ulang = st.get("ulangkaji", False)
    pertama = True
    for d, k2, mula, tamat in [s for s in sesi if s[1] == kelas]:
        info = [("معلومت كلس", None), ("تاريخ / هاري", [f"{d.strftime('%d-%m-%Y')} · {HARI_J[d.weekday()]}"]), ("ميڠݢو", [minggu_label(d)]),
                ("كلس / بيل. موريد", [f"{kelas} · {KONF['bil_murid'][kelas]} اورڠ"]), ("ماس", [f"{mula} – {tamat}"])]
        kk = [k for k in khas.get(d.isoformat(), []) if k.get("kelas", "semua") == "semua" or kelas in k.get("kelas", [])]
        if kk:
            r = rph_khas(kelas, d, mula, tamat, kk[0]["nota"], info); r.update(d=d, kelas=kelas, mula=mula); RPH.append(r)
            laporan.append(f"{d} {kelas}: {kk[0]['nota']}"); continue
        if mod == "isi_semua":
            slot = pk["slot"].get(d.isoformat())
            if not slot: raise SystemExit(f"Pelan isi_semua: tiada SP untuk {kelas} pada {d}")
            idx = [cari_sp(kelas, s) for s in slot]
            start, size = idx[0], len(idx); items = [q[i % L] for i in idx]
            st.update(mula=start, saiz=size, langkah="sambung3")
        else:
            if mod == "isi_hari_pertama" and pertama:
                sm = pk["sp_mula"]; sm = sm if isinstance(sm, list) else [sm]
                start = cari_sp(kelas, sm[0]); size = int(pk.get("saiz", 3))
                st.update(langkah="anjak1")
            else:
                if pertama and mod == "teruskan" and st.get("baharu"):
                    start = st["mula"]
                else:
                    start = st["mula"] + (1 if st.get("langkah") == "anjak1" else st.get("saiz", 3))
                size = 3
            items = [q[(start + j) % L] for j in range(size)]
            st.update(mula=start % L, saiz=size); st.pop("baharu", None)
        st.update(rph_terakhir=d.isoformat(), sp_terakhir=[sp_no(it["sp"]) or strip_no(it["sp"])[:25] for it in items])
        pertama = False
        r = rph_biasa(kelas, items, ulang, info); r.update(d=d, kelas=kelas, mula=mula); RPH.append(r)
        laporan.append(f"{d} {kelas}: " + ", ".join(sp_no(it["sp"]) or strip_no(it["sp"])[:20] for it in items))

RPH.sort(key=lambda r: (r["d"], tsort(r["mula"])))
CSS = """
@page{size:A4;margin:11mm 12mm}
*{box-sizing:border-box}
body{margin:0;font-family:"FreeSerif",serif;color:#111}
.pg{page-break-after:always;break-after:page;direction:rtl}
.pg:last-child{page-break-after:auto}
.logo{display:block;margin:0 auto 2mm;height:17mm}
h1{margin:0;text-align:center;font-size:15pt;font-weight:700}
.sub{text-align:center;font-size:10.5pt;color:#444;margin:0.5mm 0 2.5mm}
table{width:100%;border-collapse:collapse;table-layout:fixed}
td{border:0.6pt solid #7a8a82;padding:0.6mm 1.6mm;vertical-align:top;font-size:11.5pt;line-height:1.38}
td.k{background:#f1f5f2;font-weight:700;font-size:10pt;line-height:1.25}
tr.h td{background:#dce8e1;font-weight:700;font-size:11pt}
.ltr{direction:ltr;unicode-bidi:isolate;font-family:"Liberation Sans",Arial,sans-serif;font-size:9.5pt}
.ln{display:block}
"""
def cell(lines):
    out = []
    for l in lines:
        t = html.escape(l)
        t = re.sub(r'([A-Za-z0-9][A-Za-z0-9 .,:\-–()%/]*[A-Za-z0-9.)%]|[A-Za-z0-9])', r'<span class="ltr">\1</span>', t)
        out.append(f'<span class="ln">{t}</span>')
    return ''.join(out)

LOGO = base64.b64encode(open(J("kpm_logo.png"), "rb").read()).decode()
def page(r):
    ting = KONF["tingkatan"][r["kelas"]]
    rows = "".join(f'<tr class="h"><td colspan="2">{html.escape(k)}</td></tr>' if v is None else f'<tr><td class="k">{html.escape(k)}</td><td>{cell(v)}</td></tr>' for k, v in r["rows"])
    return (f'<section class="pg"><img class="logo" src="data:image/png;base64,{LOGO}" alt=""><h1>رنچڠن ڤڠاجرن هارين</h1>'
            f'<div class="sub">ڤنديديقن إسلام · تيڠكتن <span class="ltr">{ting}</span></div>'
            f'<table><colgroup><col style="width:13%"><col style="width:87%"></colgroup>{rows}</table></section>')
doc = f'<!doctype html><html lang="ms"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(page(r) for r in RPH)}</body></html>'

os.makedirs(A.keluar, exist_ok=True)
d0, d1 = min(tarikh), max(tarikh)
nama = PELAN.get("nama_fail") or f"RPH PI {minggu_label(d0)} ({d0.strftime('%d.%m')} - {d1.strftime('%d.%m.%Y')})"
pdf_path = os.path.join(A.keluar, nama + ".pdf")
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(); p = b.new_page(viewport={"width": 703, "height": 1000}); p.emulate_media(media="print")
    p.set_content(doc, wait_until="load")
    p.evaluate("""()=>{const mm=document.createElement('div');mm.style.height='100mm';document.body.appendChild(mm);const px=mm.getBoundingClientRect().height/100;mm.remove();
      for(const s of document.querySelectorAll('.pg')){for(let k=0;k<4;k++){const h=s.getBoundingClientRect().height/px;const z=parseFloat(s.style.zoom||1);if(h<=270)break;s.style.zoom=(z*270/h*0.99).toFixed(3)}}}""")
    p.pdf(path=pdf_path, format="A4", print_background=True, prefer_css_page_size=True)
    b.close()

if not A.uji:
    json.dump(kem_baru, open(J("kemajuan.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({"pdf": pdf_path, "bil_rph": len(RPH), "kemajuan_dikemas_kini": not A.uji, "ringkasan": laporan}, ensure_ascii=False, indent=1))
