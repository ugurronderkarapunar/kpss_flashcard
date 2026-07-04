import webview
import json
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.units import mm

DATA_FILE = "flashcards.json"

class FlashcardAPI:
    def __init__(self):
        self.cards = self._load()

    def _load(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cards, f, ensure_ascii=False, indent=2)

    def get_cards(self):
        """JS tarafından çağrılır, tüm kartları döndürür."""
        return self.cards

    def save_cards(self, cards_json):
        """JS tarafından çağrılır, kartları JSON string olarak alır ve kaydeder."""
        self.cards = json.loads(cards_json)
        self._save()

    def export_pdf(self, ders):
        """
        Seçili derse ait kartları PDF olarak kaydeder.
        Dosya adı: KPSS_Kartlar_{ders}.pdf
        """
        if ders == "Tümü":
            filtered = self.cards
        else:
            filtered = [c for c in self.cards if c.get("ders") == ders]

        if not filtered:
            return f"'{ders}' dersi için hiç kart bulunamadı."

        dosya_adi = f"KPSS_Kartlar_{ders}.pdf"
        doc = SimpleDocTemplate(
            dosya_adi,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )
        styles = getSampleStyleSheet()
        normal = styles["Normal"]
        title_style = styles["Title"]
        heading_style = styles["Heading2"]

        story = []
        story.append(Paragraph(f"KPSS Yanlış Cevapları – {ders}", title_style))
        story.append(Spacer(1, 10 * mm))

        for i, card in enumerate(filtered, 1):
            story.append(Paragraph(f"{i}. Kart", heading_style))
            if card.get("soru"):
                story.append(Paragraph(f"<b>Soru:</b> {card['soru']}", normal))
            story.append(Paragraph(
                f"<b>Yanlış cevabın:</b> <font color='red'>{card['yanlis']}</font>", normal))
            story.append(Paragraph(
                f"<b>Doğru cevap:</b> <font color='green'>{card['dogru']}</font>", normal))
            if card.get("harita") and card.get("ipucu"):
                story.append(Paragraph(f"<b>Harita ipucu:</b> {card['ipucu']}", normal))
            story.append(Paragraph(
                f"Kutu: {card.get('box',1)}/5 | Sonraki tekrar: {card.get('nextReview','-')}",
                normal))
            story.append(Spacer(1, 5 * mm))

        doc.build(story)
        return f"✅ PDF oluşturuldu: {dosya_adi}"


# ----------------------------------------------------------------------
# Arayüz HTML’i (orijinal kodun, pywebview ve PDF butonlarıyla güncellenmiş hali)
# ----------------------------------------------------------------------
HTML = r"""
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Kart Kutusu · KPSS Yanlış Cevap Sistemi</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

:root{
  --bg:#14120F; --panel:#1E1B16; --panel2:#26221B; --line:#3A3428;
  --paper:#F5EEDC; --ink:#2B2416; --muted:#8B8676; --muted-lt:#B9B29C;
  --tarih:#B5651D; --cografya:#2F7D5A; --vatandaslik:#35538C; --danger:#C0392B;
  --tarih-bg:#3A2A18; --cografya-bg:#183226; --vatandaslik-bg:#182338;
}
*{box-sizing:border-box;}
body{
  margin:0; background:var(--bg); color:var(--muted-lt);
  font-family:'Inter',sans-serif; min-height:100vh;
}
.wrap{max-width:960px;margin:0 auto;padding:28px 20px 60px;}

.hero{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:22px;flex-wrap:wrap;gap:10px;}
.hero h1{font-family:'Fraunces',serif;font-weight:700;font-size:1.7rem;color:var(--paper);margin:0;letter-spacing:-0.3px;}
.hero .stamp{font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:var(--muted);border:1px solid var(--line);padding:4px 10px;border-radius:20px;}

.tabs{display:flex;gap:6px;margin-bottom:22px;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:0;}
.tab{
  font-family:'Inter',sans-serif;font-weight:600;font-size:0.82rem;color:var(--muted);
  background:none;border:none;padding:10px 16px;cursor:pointer;border-radius:8px 8px 0 0;
  position:relative;top:1px;
}
.tab.active{color:var(--paper);background:var(--panel);border:1px solid var(--line);border-bottom:1px solid var(--panel);}
.tab .badge{display:inline-block;margin-left:6px;background:var(--danger);color:#fff;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;padding:1px 6px;border-radius:10px;}

.panel{background:var(--panel);border:1px solid var(--line);border-radius:0 10px 10px 10px;padding:24px;}
.section-title{font-family:'Fraunces',serif;font-size:1.15rem;color:var(--paper);margin:0 0 4px;}
.section-sub{font-size:0.85rem;color:var(--muted);margin:0 0 20px;}

label{display:block;font-size:0.75rem;font-weight:600;letter-spacing:0.04em;text-transform:uppercase;color:var(--muted);margin:14px 0 6px;}
input[type=text], textarea, select{
  width:100%;background:var(--panel2);border:1px solid var(--line);color:var(--paper);
  border-radius:8px;padding:10px 12px;font-family:'Inter',sans-serif;font-size:0.92rem;
}
textarea{min-height:64px;resize:vertical;}
input:focus, textarea:focus, select:focus{outline:2px solid var(--muted);}

.ders-picker{display:flex;gap:8px;margin-top:6px;}
.ders-btn{flex:1;padding:12px 10px;border-radius:8px;border:1.5px solid var(--line);background:var(--panel2);
  color:var(--muted-lt);font-weight:600;font-size:0.85rem;cursor:pointer;text-align:center;}
.ders-btn[data-d="Tarih"].sel{background:var(--tarih-bg);border-color:var(--tarih);color:#F0C89A;}
.ders-btn[data-d="Coğrafya"].sel{background:var(--cografya-bg);border-color:var(--cografya);color:#A9E4C6;}
.ders-btn[data-d="Vatandaşlık"].sel{background:var(--vatandaslik-bg);border-color:var(--vatandaslik);color:#AEC3EC;}

.harita-box{margin-top:14px;padding:14px;border:1px dashed var(--cografya);border-radius:8px;background:rgba(47,125,90,0.08);display:none;}
.harita-box.show{display:block;}
.check-row{display:flex;align-items:center;gap:8px;margin-top:4px;}
.check-row input{width:auto;}

.btn{font-family:'Inter',sans-serif;font-weight:700;font-size:0.85rem;padding:11px 20px;border-radius:8px;
  border:none;cursor:pointer;}
.btn-primary{background:var(--paper);color:var(--ink);}
.btn-primary:hover{background:#fff;}
.btn-ghost{background:none;border:1px solid var(--line);color:var(--muted-lt);}
.btn-danger{background:var(--danger);color:#fff;}
.btn-ok{background:var(--cografya);color:#062;}
.btn-row{display:flex;gap:10px;margin-top:18px;}

.warn-banner{margin-top:14px;padding:12px 14px;border-radius:8px;background:rgba(192,57,43,0.15);
  border-left:4px solid var(--danger);color:#F5C6C0;font-size:0.85rem;display:none;}
.warn-banner.show{display:block;}
.ok-banner{margin-top:14px;padding:10px 14px;border-radius:8px;background:rgba(47,125,90,0.15);
  border-left:4px solid var(--cografya);color:#C9F0DA;font-size:0.85rem;display:none;}
.ok-banner.show{display:block;}

/* Filtre çubuğu */
.filter-row{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px;align-items:center;}
.filter-row select, .filter-row input{width:auto;}
.pill-toggle{display:flex;gap:6px;background:var(--panel2);padding:4px;border-radius:20px;border:1px solid var(--line);}
.pill-toggle button{border:none;background:none;color:var(--muted);padding:6px 14px;border-radius:16px;font-size:0.78rem;font-weight:600;cursor:pointer;}
.pill-toggle button.active{background:var(--paper);color:var(--ink);}

/* Flashcard */
.queue-info{font-family:'IBM Plex Mono',monospace;font-size:0.8rem;color:var(--muted);margin-bottom:16px;}
.card-stage{display:flex;justify-content:center;padding:10px 0 6px;}
.flashcard{
  width:100%;max-width:520px;background:var(--paper);color:var(--ink);border-radius:4px 14px 14px 4px;
  padding:30px 28px 26px;position:relative;box-shadow:0 14px 30px rgba(0,0,0,0.45);
  transition:transform 0.15s ease; min-height:180px;
}
.flashcard:hover{transform:rotate(-0.4deg);}
.flashcard::before{ /* tab */
  content:"";position:absolute;top:-10px;left:24px;width:64px;height:16px;border-radius:6px 6px 0 0;
}
.flashcard.Tarih::before{background:var(--tarih);}
.flashcard.Coğrafya::before{background:var(--cografya);}
.flashcard.Vatandaşlık::before{background:var(--vatandaslik);}
.card-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;}
.ders-tag{font-family:'IBM Plex Mono',monospace;font-size:0.72rem;font-weight:600;letter-spacing:0.05em;
  text-transform:uppercase;padding:3px 9px;border-radius:12px;color:#fff;}
.ders-tag.Tarih{background:var(--tarih);}
.ders-tag.Coğrafya{background:var(--cografya);}
.ders-tag.Vatandaşlık{background:var(--vatandaslik);}
.box-stamp{font-family:'IBM Plex Mono',monospace;font-size:0.68rem;color:#8a8264;border:1px solid #d8cfa9;
  border-radius:4px;padding:2px 7px;transform:rotate(3deg);}
.card-q{font-family:'Fraunces',serif;font-size:1.15rem;line-height:1.4;margin:6px 0 4px;}
.card-hint{font-size:0.8rem;color:#7a7358;margin-top:6px;}
.reveal-zone{margin-top:18px;border-top:1px dashed #cfc4a0;padding-top:16px;display:none;}
.reveal-zone.show{display:block;}
.ans-line{margin:8px 0;font-size:0.95rem;}
.ans-line b{display:block;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.05em;color:#7a7358;margin-bottom:2px;font-weight:700;}
.ans-ok{color:#1F6B45;font-weight:600;}
.ans-bad{color:#A2311F;font-weight:600;text-decoration:line-through;text-decoration-color:#A2311F66;}
.tag-chip{display:inline-block;background:#e7dfc3;color:#4a4326;font-size:0.72rem;padding:2px 9px;border-radius:10px;margin:2px 4px 0 0;}
.card-actions{display:flex;gap:10px;margin-top:20px;}
.card-actions .btn{flex:1;}
.empty-state{text-align:center;padding:50px 20px;color:var(--muted);}
.empty-state .big{font-size:2rem;margin-bottom:10px;}

/* Çakışmalar */
.conflict-item{padding:14px 16px;border-radius:8px;background:rgba(192,57,43,0.1);border:1px solid rgba(192,57,43,0.4);margin-bottom:12px;}
.conflict-item .cwarn{color:#F5C6C0;font-size:0.78rem;font-weight:600;margin-bottom:8px;}
.conflict-pair{display:flex;gap:14px;flex-wrap:wrap;}
.conflict-card{flex:1;min-width:200px;background:var(--panel2);border-radius:6px;padding:10px 12px;font-size:0.85rem;}
.conflict-card .lbl{font-size:0.68rem;text-transform:uppercase;color:var(--muted);margin-bottom:3px;}

/* Tüm kartlar tablo */
.card-row{display:flex;gap:12px;align-items:center;padding:12px 14px;border-radius:8px;background:var(--panel2);margin-bottom:8px;}
.card-row .ders-tag{flex-shrink:0;}
.card-row .info{flex:1;min-width:0;}
.card-row .info .q{font-size:0.88rem;color:var(--paper);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.card-row .info .sub{font-size:0.76rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.card-row .meta{font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:var(--muted);text-align:right;flex-shrink:0;}
.icon-btn{background:none;border:none;color:var(--muted);cursor:pointer;font-size:1rem;padding:4px 8px;}
.icon-btn:hover{color:var(--danger);}

/* Bölge rehberi */
.region-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;}
.region-card{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:16px;}
.region-card h3{font-family:'Fraunces',serif;color:var(--paper);margin:0 0 4px;font-size:1rem;}
.region-card .count{font-family:'IBM Plex Mono',monospace;font-size:0.7rem;color:var(--muted);margin-bottom:10px;}
.region-card .il-list{font-size:0.82rem;line-height:1.7;color:var(--muted-lt);}
.search-il{margin-bottom:18px;}

@media(max-width:600px){
  .wrap{padding:18px 12px 40px;}
  .card-actions{flex-direction:column;}
}
</style>
</head>
<body>
<div class="wrap">

  <div class="hero">
    <h1>🗂️ Kart Kutusu — KPSS Yanlış Cevap Sistemi</h1>
    <div class="stamp" id="totalStamp">0 kart</div>
  </div>

  <div class="tabs">
    <button class="tab active" data-tab="ekle">➕ Kart Ekle</button>
    <button class="tab" data-tab="tekrar">🔁 Tekrar Et <span class="badge" id="dueBadge" style="display:none">0</span></button>
    <button class="tab" data-tab="cakisma">⚠️ Çakışmalar <span class="badge" id="conflictBadge" style="display:none">0</span></button>
    <button class="tab" data-tab="tumu">📚 Tüm Kartlar</button>
    <button class="tab" data-tab="bolge">🗺️ Bölge Rehberi</button>
  </div>

  <!-- PDF Çıkarma Butonları -->
  <div style="margin-bottom:18px; display:flex; gap:10px; flex-wrap:wrap;">
    <button class="btn btn-ghost" onclick="exportPDF('Tarih')">📄 Tarih PDF</button>
    <button class="btn btn-ghost" onclick="exportPDF('Coğrafya')">📄 Coğrafya PDF</button>
    <button class="btn btn-ghost" onclick="exportPDF('Vatandaşlık')">📄 Vatandaşlık PDF</button>
    <button class="btn btn-ghost" onclick="exportPDF('Tümü')">📄 Tüm Kartlar PDF</button>
    <span id="pdfMsg" style="color:var(--paper); font-size:0.85rem; align-self:center;"></span>
  </div>

  <!-- KART EKLE -->
  <div class="panel view" id="view-ekle">
    <div class="section-title">Yeni yanlış kaydı ekle</div>
    <div class="section-sub">Soru bankasından çıkan yanlışını buraya gir, sistem otomatik tekrar programına alsın.</div>

    <label>Ders</label>
    <div class="ders-picker">
      <button class="ders-btn sel" data-d="Tarih">Tarih</button>
      <button class="ders-btn" data-d="Coğrafya">Coğrafya</button>
      <button class="ders-btn" data-d="Vatandaşlık">Vatandaşlık</button>
    </div>

    <label>Soru (opsiyonel — kısa özet yeterli)</label>
    <textarea id="f-soru" placeholder="Örn: Malazgirt Savaşı'nın sonuçlarından biri aşağıdakilerden hangisidir?"></textarea>

    <label>Yanlış cevabım</label>
    <input type="text" id="f-yanlis" placeholder="Kendi verdiğin (yanlış) cevap">

    <label>Doğru cevap</label>
    <input type="text" id="f-dogru" placeholder="Doğrusu ne?">

    <div class="harita-box" id="haritaBox">
      <div class="check-row">
        <input type="checkbox" id="f-harita">
        <label style="margin:0;text-transform:none;font-weight:600;color:var(--paper);font-size:0.85rem;letter-spacing:0;">🗺️ Bu bir Türkiye haritası sorusu</label>
      </div>
      <div id="haritaDetay" style="display:none;">
        <label>İşaretli il/bölge etiketleri (virgülle ayır)</label>
        <input type="text" id="f-iller" placeholder="Örn: Konya, Karaman, Aksaray">
        <label>Harita ipucu — neye göre sorulmuş?</label>
        <textarea id="f-ipucu" placeholder="Örn: Üçü de İç Anadolu, karasal iklim, ikinci ürün tarımı yapılmayan iller"></textarea>
      </div>
    </div>

    <div class="warn-banner" id="addWarnBanner"></div>
    <div class="ok-banner" id="addOkBanner">✅ Kart eklendi ve tekrar programına alındı.</div>

    <div class="btn-row">
      <button class="btn btn-primary" id="btnEkle">Kartı Ekle</button>
      <button class="btn btn-ghost" id="btnTemizle">Formu Temizle</button>
    </div>
  </div>

  <!-- TEKRAR ET -->
  <div class="panel view" id="view-tekrar" style="display:none;">
    <div class="section-title">Tekrar zamanı</div>
    <div class="section-sub">Leitner sistemi: bilmediklerin sık, bildiklerin seyrek karşına çıkar.</div>

    <div class="filter-row">
      <select id="revDers">
        <option value="Tümü">Tüm dersler</option>
        <option value="Tarih">Tarih</option>
        <option value="Coğrafya">Coğrafya</option>
        <option value="Vatandaşlık">Vatandaşlık</option>
      </select>
      <div class="pill-toggle">
        <button class="active" data-mode="due">Sadece bugünkü tekrarlar</button>
        <button data-mode="all">Hepsini göster</button>
      </div>
    </div>

    <div class="queue-info" id="queueInfo"></div>
    <div class="card-stage" id="cardStage"></div>
  </div>

  <!-- ÇAKIŞMALAR -->
  <div class="panel view" id="view-cakisma" style="display:none;">
    <div class="section-title">Karıştırma riski olan cevaplar</div>
    <div class="section-sub">Bir sorunun yanlış cevabın, başka bir sorunun doğru cevabıyla aynı/çok benziyorsa burada görünür.</div>
    <div id="conflictList"></div>
  </div>

  <!-- TÜM KARTLAR -->
  <div class="panel view" id="view-tumu" style="display:none;">
    <div class="section-title">Tüm kartlar</div>
    <div class="filter-row">
      <select id="allDers">
        <option value="Tümü">Tüm dersler</option>
        <option value="Tarih">Tarih</option>
        <option value="Coğrafya">Coğrafya</option>
        <option value="Vatandaşlık">Vatandaşlık</option>
      </select>
      <input type="text" id="allSearch" placeholder="Ara (soru / cevap)..." style="min-width:220px;">
    </div>
    <div id="allList"></div>
  </div>

  <!-- BÖLGE REHBERİ -->
  <div class="panel view" id="view-bolge" style="display:none;">
    <div class="section-title">7 Bölge · 81 İl Referansı</div>
    <div class="section-sub">Haritalı sorularda "bu iller hangi bölgede" mantığını hızlı tekrar için.</div>
    <input type="text" class="search-il" id="ilSearch" placeholder="Bir il yaz, hangi bölgede olduğunu bul... (örn: Kırıkkale)">
    <div id="ilSonuc" style="margin-bottom:16px;font-size:0.88rem;color:var(--paper);"></div>
    <div class="region-grid" id="regionGrid"></div>
  </div>

</div>

<script>
let cards = [];
let selectedDers = 'Tarih';
let reviewQueue = [];
let reviewIdx = 0;

const BOX_INTERVALS = [0, 1, 2, 4, 7, 14]; // box 1..5 -> gün

const BOLGELER = {
  "Marmara": ["İstanbul","Kocaeli","Sakarya","Bilecik","Bursa","Yalova","Çanakkale","Balıkesir","Tekirdağ","Edirne","Kırklareli"],
  "Ege": ["İzmir","Manisa","Aydın","Denizli","Muğla","Afyonkarahisar","Kütahya","Uşak"],
  "Akdeniz": ["Antalya","Isparta","Burdur","Mersin","Adana","Osmaniye","Hatay","Kahramanmaraş"],
  "İç Anadolu": ["Ankara","Konya","Kayseri","Sivas","Yozgat","Kırşehir","Nevşehir","Niğde","Aksaray","Karaman","Kırıkkale","Çankırı","Eskişehir"],
  "Karadeniz": ["Zonguldak","Karabük","Bartın","Bolu","Düzce","Kastamonu","Sinop","Samsun","Çorum","Amasya","Tokat","Ordu","Giresun","Trabzon","Rize","Artvin","Gümüşhane","Bayburt"],
  "Doğu Anadolu": ["Erzurum","Erzincan","Bingöl","Muş","Bitlis","Van","Ağrı","Iğdır","Kars","Ardahan","Elazığ","Tunceli","Malatya","Hakkari"],
  "Güneydoğu Anadolu": ["Gaziantep","Şanlıurfa","Diyarbakır","Mardin","Siirt","Şırnak","Batman","Kilis","Adıyaman"]
};

function todayISO(){ return new Date().toISOString().slice(0,10); }

function trLower(s){
  return (s||"").replace(/İ/g,'i').replace(/I/g,'ı').toLowerCase();
}
function normalize(s){
  return trLower(s).trim().replace(/[.,!?;:'"()\[\]]/g,'').replace(/\s+/g,' ');
}
function levenshtein(a,b){
  const m=a.length,n=b.length;
  if(!m) return n; if(!n) return m;
  const dp=Array.from({length:m+1},(_,i)=>[i,...Array(n).fill(0)]);
  for(let j=0;j<=n;j++) dp[0][j]=j;
  for(let i=1;i<=m;i++){
    for(let j=1;j<=n;j++){
      dp[i][j] = a[i-1]===b[j-1] ? dp[i-1][j-1] : 1+Math.min(dp[i-1][j-1],dp[i-1][j],dp[i][j-1]);
    }
  }
  return dp[m][n];
}
function textsSimilar(a,b){
  const na=normalize(a), nb=normalize(b);
  if(!na || !nb) return false;
  if(na===nb) return true;
  if(na.length>=4 && nb.length>=4 && (na.includes(nb)||nb.includes(na))) return true;
  const maxLen=Math.max(na.length,nb.length);
  if(maxLen>50) return false;
  const dist=levenshtein(na,nb);
  return dist<=Math.max(1,Math.floor(maxLen*0.15));
}

async function loadCards(){
  try{
    cards = await pywebview.api.get_cards();
  }catch(e){ cards = []; }
}
async function saveCards(){
  try{ await pywebview.api.save_cards(JSON.stringify(cards)); }
  catch(e){ console.error('Kaydetme hatası', e); }
}

function uid(){ return 'c_'+Date.now().toString(36)+Math.random().toString(36).slice(2,7); }

function computeConflicts(){
  const conflicts=[];
  for(let i=0;i<cards.length;i++){
    for(let j=0;j<cards.length;j++){
      if(i===j) continue;
      if(textsSimilar(cards[i].yanlis, cards[j].dogru)){
        conflicts.push({a:cards[i], b:cards[j]});
      }
    }
  }
  return conflicts;
}

// ---------- RENDER: HEADER / TABS ----------
function renderHeaderCounts(){
  document.getElementById('totalStamp').textContent = cards.length + ' kart';
  const due = cards.filter(c => !c.nextReview || c.nextReview <= todayISO()).length;
  const dueBadge = document.getElementById('dueBadge');
  if(due>0){ dueBadge.style.display='inline-block'; dueBadge.textContent=due; } else { dueBadge.style.display='none'; }
  const conf = computeConflicts().length;
  const confBadge = document.getElementById('conflictBadge');
  if(conf>0){ confBadge.style.display='inline-block'; confBadge.textContent=conf; } else { confBadge.style.display='none'; }
}

// ---------- TAB SWITCHING ----------
document.querySelectorAll('.tab').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.view').forEach(v=>v.style.display='none');
    const id = 'view-'+btn.dataset.tab;
    document.getElementById(id).style.display='block';
    if(btn.dataset.tab==='tekrar') startReview();
    if(btn.dataset.tab==='cakisma') renderConflicts();
    if(btn.dataset.tab==='tumu') renderAllCards();
    if(btn.dataset.tab==='bolge') renderRegions();
  });
});

// ---------- KART EKLE ----------
document.querySelectorAll('.ders-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.ders-btn').forEach(b=>b.classList.remove('sel'));
    btn.classList.add('sel');
    selectedDers = btn.dataset.d;
    document.getElementById('haritaBox').classList.toggle('show', selectedDers==='Coğrafya');
  });
});
document.getElementById('f-harita').addEventListener('change', (e)=>{
  document.getElementById('haritaDetay').style.display = e.target.checked ? 'block' : 'none';
});

document.getElementById('btnTemizle').addEventListener('click', clearForm);
function clearForm(){
  document.getElementById('f-soru').value='';
  document.getElementById('f-yanlis').value='';
  document.getElementById('f-dogru').value='';
  document.getElementById('f-harita').checked=false;
  document.getElementById('f-iller').value='';
  document.getElementById('f-ipucu').value='';
  document.getElementById('haritaDetay').style.display='none';
  document.getElementById('addWarnBanner').classList.remove('show');
  document.getElementById('addOkBanner').classList.remove('show');
}

document.getElementById('btnEkle').addEventListener('click', async ()=>{
  const soru = document.getElementById('f-soru').value.trim();
  const yanlis = document.getElementById('f-yanlis').value.trim();
  const dogru = document.getElementById('f-dogru').value.trim();
  const harita = document.getElementById('f-harita').checked;
  const iller = document.getElementById('f-iller').value.split(',').map(s=>s.trim()).filter(Boolean);
  const ipucu = document.getElementById('f-ipucu').value.trim();

  const warnEl = document.getElementById('addWarnBanner');
  const okEl = document.getElementById('addOkBanner');
  warnEl.classList.remove('show'); okEl.classList.remove('show');

  if(!yanlis || !dogru){
    warnEl.textContent = '⚠️ Yanlış cevap ve doğru cevap alanları zorunlu.';
    warnEl.classList.add('show');
    return;
  }

  const newCard = {
    id: uid(), ders: selectedDers, soru, yanlis, dogru,
    harita: selectedDers==='Coğrafya' && harita, iller, ipucu,
    box: 1, nextReview: todayISO(), lastReview: null,
    dogruSayisi: 0, yanlisSayisi: 0, createdAt: todayISO()
  };
  cards.push(newCard);
  await saveCards();

  const relatedConflicts = cards.filter(c => c.id!==newCard.id &&
    (textsSimilar(newCard.yanlis, c.dogru) || textsSimilar(c.yanlis, newCard.dogru)));
  if(relatedConflicts.length>0){
    warnEl.innerHTML = `⚠️ Dikkat! Bu kartın cevabı, ${relatedConflicts.length} başka kartla karışabilir. 
      "⚠️ Çakışmalar" sekmesinden kontrol et.`;
    warnEl.classList.add('show');
  } else {
    okEl.classList.add('show');
  }
  clearForm();
  if(relatedConflicts.length>0){ warnEl.classList.add('show'); }
  renderHeaderCounts();
});

// ---------- TEKRAR ET ----------
document.getElementById('revDers').addEventListener('change', startReview);
document.querySelectorAll('#view-tekrar .pill-toggle button').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('#view-tekrar .pill-toggle button').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    startReview();
  });
});

function startReview(){
  const dersFilter = document.getElementById('revDers').value;
  const mode = document.querySelector('#view-tekrar .pill-toggle button.active').dataset.mode;
  reviewQueue = cards.filter(c=>{
    if(dersFilter!=='Tümü' && c.ders!==dersFilter) return false;
    if(mode==='due') return !c.nextReview || c.nextReview <= todayISO();
    return true;
  });
  reviewQueue.sort((a,b)=> (a.nextReview||'').localeCompare(b.nextReview||''));
  reviewIdx = 0;
  renderReviewCard();
}

function renderReviewCard(){
  const stage = document.getElementById('cardStage');
  const info = document.getElementById('queueInfo');
  info.textContent = reviewQueue.length ? `Kart ${reviewIdx+1} / ${reviewQueue.length}` : '';
  if(reviewQueue.length===0){
    stage.innerHTML = `<div class="empty-state"><div class="big">🎉</div>Şu an tekrar edilecek kart yok.<br>"Hepsini göster" ile serbest tekrar yapabilirsin.</div>`;
    return;
  }
  if(reviewIdx >= reviewQueue.length){
    stage.innerHTML = `<div class="empty-state"><div class="big">✅</div>Bu turu bitirdin.</div>`;
    renderHeaderCounts();
    return;
  }
  const c = reviewQueue[reviewIdx];
  const front = c.soru ? c.soru : `❌ Bu soruda "${c.yanlis}" cevabını vermiştin. Doğrusu neydi?`;
  let harItaHtml = '';
  if(c.harita){
    harItaHtml = `<div class="card-hint">🗺️ Harita sorusu${c.iller.length? ': '+c.iller.map(i=>`<span class="tag-chip">${escapeHtml(i)}</span>`).join(''):''}</div>`;
  }
  stage.innerHTML = `
    <div class="flashcard ${c.ders}">
      <div class="card-top">
        <span class="ders-tag ${c.ders}">${c.ders}</span>
        <span class="box-stamp">KUTU ${c.box}/5</span>
      </div>
      <div class="card-q">${escapeHtml(front)}</div>
      ${harItaHtml}
      <div class="reveal-zone" id="revealZone">
        <div class="ans-line"><b>Doğru cevap</b><span class="ans-ok">✅ ${escapeHtml(c.dogru)}</span></div>
        <div class="ans-line"><b>Senin yanlış cevabın</b><span class="ans-bad">${escapeHtml(c.yanlis)}</span></div>
        ${c.harita && c.ipucu ? `<div class="ans-line"><b>Harita ipucu</b>${escapeHtml(c.ipucu)}</div>` : ''}
      </div>
      <div class="card-actions" id="cardActions">
        <button class="btn btn-ghost" id="btnReveal" style="flex:1;">Cevabı Göster</button>
      </div>
    </div>
  `;
  document.getElementById('btnReveal').addEventListener('click', ()=>{
    document.getElementById('revealZone').classList.add('show');
    document.getElementById('cardActions').innerHTML = `
      <button class="btn btn-danger" id="btnKaristi">😵 Yine Karıştırdım</button>
      <button class="btn btn-ok" id="btnBiliyorum">✅ Artık Biliyorum</button>
    `;
    document.getElementById('btnKaristi').addEventListener('click', ()=>markReview(c, false));
    document.getElementById('btnBiliyorum').addEventListener('click', ()=>markReview(c, true));
  });
}

async function markReview(card, remembered){
  const idx = cards.findIndex(c=>c.id===card.id);
  if(idx===-1) return;
  const c = cards[idx];
  const today = todayISO();
  if(remembered){
    c.box = Math.min(5, c.box+1);
    c.dogruSayisi = (c.dogruSayisi||0)+1;
  } else {
    c.box = 1;
    c.yanlisSayisi = (c.yanlisSayisi||0)+1;
  }
  const days = BOX_INTERVALS[c.box];
  const next = new Date();
  next.setDate(next.getDate()+days);
  c.nextReview = next.toISOString().slice(0,10);
  c.lastReview = today;
  await saveCards();
  reviewIdx++;
  renderReviewCard();
  renderHeaderCounts();
}

function escapeHtml(s){
  return (s||"").replace(/[&<>"']/g, m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

// ---------- ÇAKIŞMALAR ----------
function renderConflicts(){
  const list = document.getElementById('conflictList');
  const conflicts = computeConflicts();
  if(conflicts.length===0){
    list.innerHTML = `<div class="empty-state"><div class="big">✅</div>Şu an çakışan cevap yok.</div>`;
    return;
  }
  list.innerHTML = conflicts.map(({a,b})=>`
    <div class="conflict-item">
      <div class="cwarn">⚠️ "${escapeHtml(a.ders)}" dersindeki bir sorunun YANLIŞ cevabı, "${escapeHtml(b.ders)}" dersindeki başka bir sorunun DOĞRU cevabıyla aynı/çok benzer.</div>
      <div class="conflict-pair">
        <div class="conflict-card">
          <div class="lbl">Yanlış cevap veren soru (${escapeHtml(a.ders)})</div>
          ${a.soru ? escapeHtml(a.soru)+'<br>' : ''}
          <span class="ans-bad">${escapeHtml(a.yanlis)}</span>
        </div>
        <div class="conflict-card">
          <div class="lbl">Doğru cevabı bu olan soru (${escapeHtml(b.ders)})</div>
          ${b.soru ? escapeHtml(b.soru)+'<br>' : ''}
          <span class="ans-ok">${escapeHtml(b.dogru)}</span>
        </div>
      </div>
    </div>
  `).join('');
}

// ---------- TÜM KARTLAR ----------
document.getElementById('allDers').addEventListener('change', renderAllCards);
document.getElementById('allSearch').addEventListener('input', renderAllCards);

function renderAllCards(){
  const dersFilter = document.getElementById('allDers').value;
  const q = document.getElementById('allSearch').value.trim().toLowerCase();
  let list = cards.filter(c=>{
    if(dersFilter!=='Tümü' && c.ders!==dersFilter) return false;
    if(q){
      const hay = `${c.soru} ${c.yanlis} ${c.dogru}`.toLowerCase();
      if(!hay.includes(q)) return false;
    }
    return true;
  });
  list.sort((a,b)=> (a.nextReview||'').localeCompare(b.nextReview||''));
  const el = document.getElementById('allList');
  if(list.length===0){ el.innerHTML = `<div class="empty-state">Kayıt bulunamadı.</div>`; return; }
  el.innerHTML = list.map(c=>`
    <div class="card-row">
      <span class="ders-tag ${c.ders}">${c.ders}</span>
      <div class="info">
        <div class="q">${escapeHtml(c.soru || c.dogru)}</div>
        <div class="sub">❌ ${escapeHtml(c.yanlis)} &nbsp;→&nbsp; ✅ ${escapeHtml(c.dogru)}</div>
      </div>
      <div class="meta">Kutu ${c.box}/5<br>${c.nextReview||'-'}</div>
      <button class="icon-btn" data-id="${c.id}" title="Sil">🗑</button>
    </div>
  `).join('');
  el.querySelectorAll('.icon-btn').forEach(btn=>{
    btn.addEventListener('click', async ()=>{
      cards = cards.filter(c=>c.id!==btn.dataset.id);
      await saveCards();
      renderAllCards();
      renderHeaderCounts();
    });
  });
}

// ---------- BÖLGE REHBERİ ----------
function renderRegions(){
  const grid = document.getElementById('regionGrid');
  grid.innerHTML = Object.entries(BOLGELER).map(([ad, iller])=>`
    <div class="region-card">
      <h3>${ad}</h3>
      <div class="count">${iller.length} il</div>
      <div class="il-list">${iller.join(', ')}</div>
    </div>
  `).join('');
}
document.getElementById('ilSearch').addEventListener('input', (e)=>{
  const q = trLower(e.target.value.trim());
  const sonuc = document.getElementById('ilSonuc');
  if(!q){ sonuc.textContent=''; return; }
  let bulunan = null;
  for(const [bolge, iller] of Object.entries(BOLGELER)){
    const hit = iller.find(il => trLower(il).includes(q));
    if(hit){ bulunan = {bolge, il:hit}; break; }
  }
  sonuc.textContent = bulunan ? `📍 ${bulunan.il} → ${bulunan.bolge} Bölgesi` : '❌ İl bulunamadı, yazımı kontrol et.';
});

// ---------- PDF ÇIKARMA ----------
async function exportPDF(ders) {
  const msgDiv = document.getElementById('pdfMsg');
  msgDiv.textContent = "PDF oluşturuluyor...";
  try {
    let result = await pywebview.api.export_pdf(ders);
    msgDiv.textContent = result;
  } catch(e) {
    msgDiv.textContent = "PDF oluşturulamadı: " + e;
  }
}

// ---------- INIT ----------
(async function init(){
  await loadCards();
  renderHeaderCounts();
  renderRegions();
})();
</script>
</body>
</html>
"""

if __name__ == '__main__':
    api = FlashcardAPI()
    window = webview.create_window('KPSS Flashcard', html=HTML, js_api=api)
    webview.start()
