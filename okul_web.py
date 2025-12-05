import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go

# --- Ayarlar ---
SAYFA_BASLIGI = "🏫 Çözüm Not Takip Sistemi - KTT/Ödev"
SHEET_ADI = "Çözüm Not Verileri"

# GİRİŞ BİLGİLERİ (Bunu değiştirebilirsiniz)
KULLANICI_ADI = "cozum"
SIFRE = "12345"

# Listeler
DERSLER_LISTESI = ["TYT Matematik", "Türkçe", "Fizik", "Kimya", "Biyoloji", "AYT Matematik"]
SINAV_TURLERI = ["1. KTT Sonuçları", "2. KTT Sonuçları", "3. KTT Sonuçları"]

st.set_page_config(page_title=SAYFA_BASLIGI, layout="wide")

# --- Oturum Kontrolü (Login) ---
if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False

def giris_ekrani():
    st.markdown("<h1 style='text-align: center;'>🔒 Öğretmen Girişi</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        kadi = st.text_input("Kullanıcı Adı")
        sifre_girilen = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap", type="primary", use_container_width=True):
            if kadi == KULLANICI_ADI and sifre_girilen == SIFRE:
                st.session_state["giris_yapildi"] = True
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")

# --- Google Bağlantısı ---
@st.cache_resource
def get_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        credentials = Credentials.from_service_account_file("okul_anahtar.json", scopes=scopes)
    return gspread.authorize(credentials)

def veri_yukle():
    client = get_connection()
    try:
        sheet = client.open(SHEET_ADI).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if df.empty: return pd.DataFrame(columns=["Ders", "Sınav", "Ad", "Soyad", "Not", "Ödev"])
        return df
    except:
        return pd.DataFrame(columns=["Ders", "Sınav", "Ad", "Soyad", "Not", "Ödev"])

def veri_ekle(liste):
    client = get_connection()
    sheet = client.open(SHEET_ADI).sheet1
    sheet.append_row(liste)

def veri_sil(index):
    client = get_connection()
    sheet = client.open(SHEET_ADI).sheet1
    sheet.delete_rows(index + 2)

def veri_guncelle(index, liste):
    client = get_connection()
    sheet = client.open(SHEET_ADI).sheet1
    row = index + 2
    sheet.update(f"A{row}:F{row}", [liste])

# --- ANA UYGULAMA ---
def ana_uygulama():
    # Çıkış Butonu
    with st.sidebar:
        st.write(f"👤 **{KULLANICI_ADI}** oturumu açık")
        if st.button("Çıkış Yap"):
            st.session_state["giris_yapildi"] = False
            st.rerun()
        st.divider()

    df = veri_yukle()

    # Menü Seçimi
    menu = st.sidebar.radio("Menü", ["📋 Liste & İşlemler", "📊 Öğrenci Karnesi (Analiz)"])

    # ---------------- BÖLÜM 1: LİSTE & İŞLEMLER ----------------
    if menu == "📋 Liste & İşlemler":
        st.title("📋 Kayıt Yönetimi")
        
        tab1, tab2, tab3 = st.tabs(["Yeni Ekle", "Düzenle", "Sil"])
        
        # --- EKLEME ---
        with tab1:
            with st.form("ekle_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                ders = col_a.selectbox("Ders", DERSLER_LISTESI)
                sinav = col_b.selectbox("Sınav", SINAV_TURLERI)
                ad = col_a.text_input("Ad")
                soyad = col_b.text_input("Soyad")
                notu = col_a.number_input("Puan", 0, 100)
                odev = col_b.selectbox("Ödev", ["Yaptı ✅", "Yapmadı ❌", "Eksik ⚠️"])
                if st.form_submit_button("Kaydet"):
                    if ad and soyad:
                        veri_ekle([ders, sinav, ad, soyad, notu, odev])
                        st.success("Kaydedildi!")
                        st.rerun()
                    else:
                        st.error("İsim giriniz.")

        # --- DÜZENLEME ---
        with tab2:
            if not df.empty:
                liste = [f"{i} | {r['Ad']} {r['Soyad']} - {r['Ders']} ({r['Sınav']})" for i, r in df.iterrows()]
                secilen = st.selectbox("Düzenlenecek Kayıt", liste)
                idx = int(secilen.split(" | ")[0])
                r = df.iloc[idx]
                
                with st.form("guncelle_form"):
                    d = st.selectbox("Ders", DERSLER_LISTESI, index=DERSLER_LISTESI.index(r["Ders"]) if r["Ders"] in DERSLER_LISTESI else 0)
                    s = st.selectbox("Sınav", SINAV_TURLERI, index=SINAV_TURLERI.index(r["Sınav"]) if r["Sınav"] in SINAV_TURLERI else 0)
                    a = st.text_input("Ad", value=r["Ad"])
                    so = st.text_input("Soyad", value=r["Soyad"])
                    n = st.number_input("Puan", 0, 100, value=int(r["Not"]))
                    o_opts = ["Tam 🔥", "Eksik ⚠️", "Yok ❌"]
                    o = st.selectbox("Ödev", o_opts, index=o_opts.index(r["Ödev"]) if r["Ödev"] in o_opts else 0)
                    
                    if st.form_submit_button("Güncelle"):
                        veri_guncelle(idx, [d, s, a, so, n, o])
                        st.success("Güncellendi!")
                        st.rerun()
            else:
                st.info("Veri yok.")

        # --- SİLME ---
        with tab3:
            if not df.empty:
                liste_sil = [f"{i} | {r['Ad']} {r['Soyad']} - {r['Not']}" for i, r in df.iterrows()]
                secilen_sil = st.selectbox("Silinecek Kayıt", liste_sil)
                if st.button("Sil", type="primary"):
                    veri_sil(int(secilen_sil.split(" | ")[0]))
                    st.success("Silindi!")
                    st.rerun()

        st.divider()
        st.dataframe(df, use_container_width=True)

    # ---------------- BÖLÜM 2: ÖĞRENCİ KARNESİ (ANALİZ) ----------------
    elif menu == "📊 Öğrenci Karnesi (Analiz)":
        st.title("📊 Öğrenci Gelişim Analizi")
        
        if not df.empty:
            # Öğrenci listesini oluştur (Benzersiz isimler)
            df["Tam Ad"] = df["Ad"] + " " + df["Soyad"]
            ogrenciler = df["Tam Ad"].unique()
            secilen_ogr = st.selectbox("Analiz edilecek öğrenciyi seçin:", ogrenciler)
            
            # Seçilen öğrencinin verilerini filtrele
            ogr_df = df[df["Tam Ad"] == secilen_ogr]
            
            # İstatistikler
            ort = ogr_df["Not"].mean()
            sinif_ort = df["Not"].mean()
            
            # --- 1. Üst Kartlar (Metrics) ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Öğrenci Ortalaması", f"{ort:.1f}", delta=f"{ort-sinif_ort:.1f} Sınıf Ort. Farkı")
            col2.metric("Sınıf Ortalaması", f"{sinif_ort:.1f}")
            col3.metric("Toplam Sınav Sayısı", len(ogr_df))
            
            st.divider()
            
            # --- 2. Hız Göstergesi (Gauge Chart) ---
            col_g1, col_g2 = st.columns([1, 2])
            
            with col_g1:
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = ort,
                    title = {'text': "Başarı Puanı"},
                    gauge = {'axis': {'range': [0, 100]},
                             'bar': {'color': "#4CAF50" if ort>=50 else "#F44336"},
                             'steps': [
                                 {'range': [0, 50], 'color': "lightgray"},
                                 {'range': [50, 85], 'color': "#fff3cd"},
                                 {'range': [85, 100], 'color': "#d4edda"}]}))
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            # --- 3. Ders Bazlı Gelişim (Bar Chart) ---
            with col_g2:
                # Sınav türüne göre sıralama
                fig_bar = px.bar(ogr_df, x="Ders", y="Not", color="Sınav", 
                                 title="Derslere Göre Sınav Sonuçları", barmode="group",
                                 text_auto=True)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # --- 4. Zaman Çizelgesi (Line Chart) ---
            st.subheader("📈 Sınav Gelişim Grafiği")
            # Sadece sınav isimlerine göre basit bir çizgi grafik
            fig_line = px.line(ogr_df, x="Sınav", y="Not", color="Ders", markers=True,
                               title="Sınavlar Arası Değişim")
            st.plotly_chart(fig_line, use_container_width=True)

        else:
            st.info("Analiz yapılacak veri bulunamadı.")

# --- UYGULAMA BAŞLATICI ---
if st.session_state["giris_yapildi"]:
    ana_uygulama()
else:
    giris_ekrani()