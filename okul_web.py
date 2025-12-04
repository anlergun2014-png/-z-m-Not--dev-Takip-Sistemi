import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Ayarlar ---
SAYFA_BASLIGI = "🏫 Çözüm Not Sistemi - KTT/Ödev"
SHEET_ADI = "Çözüm Not Verileri" # Google Drive'daki dosya adınızla AYNI OLMALI

# Listeler
DERSLER_LISTESI = ["TYT Matematik", "Türkçe", "Fizik", "Biyoloji", "Kimya", "AYT Matematik"]
SINAV_TURLERI = ["1. KTT Sonuçları", "2. KTT Sonuçları", "3. KTT Sonuçları"]

st.set_page_config(page_title=SAYFA_BASLIGI, layout="wide")

# --- Google Sheets Bağlantı Fonksiyonu ---
# Bu fonksiyon bağlantıyı önbelleğe alır (cache), böylece her seferinde tekrar bağlanmaz hızlanır.
@st.cache_resource
def get_connection():
    # Secrets dosyasından bilgileri al
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client

def veri_yukle():
    client = get_connection()
    try:
        sheet = client.open(SHEET_ADI).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        # Eğer boş gelirse veya sütunlar eksikse düzelt
        if df.empty:
             return pd.DataFrame(columns=["Ders", "Sınav", "Ad", "Soyad", "Not", "Ödev"])
        return df
    except Exception as e:
        st.error(f"Google Sheets'e bağlanırken hata oluştu: {e}")
        return pd.DataFrame(columns=["Ders", "Sınav", "Ad", "Soyad", "Not", "Ödev"])

def veri_ekle(yeni_veri_listesi):
    client = get_connection()
    sheet = client.open(SHEET_ADI).sheet1
    # Listeyi sona ekle
    sheet.append_row(yeni_veri_listesi)

def veri_sil(index):
    client = get_connection()
    sheet = client.open(SHEET_ADI).sheet1
    # Google Sheets'te satırlar 1'den başlar, 1. satır başlıktır.
    # DataFrame indexi 0 ise Sheets'te 2. satırdır.
    row_to_delete = index + 2 
    sheet.delete_rows(row_to_delete)

# --- Yan Menü (Veri Girişi) ---
st.sidebar.header("➕ Sınav/KTT Girişi")

# Veri Yükle (Her işlemde güncel veriyi çek)
df = veri_yukle()

with st.sidebar.form("ekleme_formu", clear_on_submit=True):
    secilen_ders = st.selectbox("Ders", DERSLER_LISTESI)
    secilen_sinav = st.selectbox("Sınav Türü", SINAV_TURLERI)
    
    ad = st.text_input("Öğrenci Adı")
    soyad = st.text_input("Öğrenci Soyadı")
    notu = st.number_input("Puan", min_value=0, max_value=100, step=1)
    odev = st.selectbox("Ödev", ["Yaptı ✅", "Yapmadı ❌", "Eksik ⚠️"])
    
    ekle_btn = st.form_submit_button("Sonucu Buluta Kaydet ☁️")

# Kayıt İşlemi
if ekle_btn:
    if ad and soyad:
        # Google Sheets'e liste olarak gönderiyoruz
        veri_ekle([secilen_ders, secilen_sinav, ad, soyad, notu, odev])
        st.sidebar.success(f"✅ {ad} {soyad} Google Sheets'e kaydedildi!")
        st.rerun()
    else:
        st.sidebar.error("⚠️ İsim alanları boş bırakılamaz.")

# --- SİLME PANELİ ---
st.sidebar.divider()
st.sidebar.header("🗑️ Kayıt Sil")

if not df.empty:
    silinecek_listesi = [
        f"{i} | {row['Ad']} {row['Soyad']} - {row['Ders']} ({row['Sınav']})" 
        for i, row in df.iterrows()
    ]
    secilen_silinecek = st.sidebar.selectbox("Silinecek Kayıt:", silinecek_listesi)
    
    if st.sidebar.button("Seçili Kaydı Buluttan SİL"):
        silinecek_index = int(secilen_silinecek.split(" | ")[0])
        veri_sil(silinecek_index)
        st.sidebar.success("Kayıt Google Sheets'ten silindi!")
        st.rerun()
else:
    st.sidebar.info("Listede kayıt yok.")

# --- Ana Sayfa ---
st.title(SAYFA_BASLIGI)
st.caption("Veriler doğrudan Google Drive'daki 'Okul Verileri' tablosundan çekilmektedir.")

# --- FİLTRELEME ---
st.subheader("🔍 Sonuçları İncele")
col1, col2 = st.columns(2)
filtre_ders = col1.selectbox("Ders:", ["TÜM DERSLER"] + DERSLER_LISTESI)
filtre_sinav = col2.selectbox("Sınav:", ["TÜM SINAVLAR"] + SINAV_TURLERI)

gosterilecek_df = df.copy()

if filtre_ders != "TÜM DERSLER":
    gosterilecek_df = gosterilecek_df[gosterilecek_df["Ders"] == filtre_ders]
if filtre_sinav != "TÜM SINAVLAR":
    gosterilecek_df = gosterilecek_df[gosterilecek_df["Sınav"] == filtre_sinav]

# --- GÖSTERİM ---
if not gosterilecek_df.empty:
    tab1, tab2 = st.tabs(["📋 Liste", "📈 Analiz"])
    
    with tab1:
        st.dataframe(gosterilecek_df, use_container_width=True)
    
    with tab2:
        if filtre_ders != "TÜM DERSLER":
            gosterilecek_df["Tam Ad"] = gosterilecek_df["Ad"] + " " + gosterilecek_df["Soyad"]
            try:
                pivot = gosterilecek_df.pivot_table(index="Tam Ad", columns="Sınav", values="Not", aggfunc='first')
                st.dataframe(pivot, use_container_width=True)
            except:
                st.warning("Analiz için yeterli veri yok.")
        else:
            st.warning("Analiz için bir ders seçmelisiniz.")
else:
    st.info("Veri bulunamadı.")