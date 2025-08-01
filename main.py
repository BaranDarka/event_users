import os
import json
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import streamlit as st

# --- initialize firebase (unchanged) ---
load_dotenv()
firebase_creds = json.loads(os.environ["FIREBASE_CREDS_JSON"])
cred = credentials.Certificate(firebase_creds)
import firebase_admin as _firebase_admin_internal
if not _firebase_admin_internal._apps:
    firebase_app = firebase_admin.initialize_app(cred)
else:
    firebase_app = _firebase_admin_internal.get_app()
db = firestore.client()

st.set_page_config(page_title="Event Kayıt", layout="centered")
st.title("Event Kayıt Formu")

# --- session state for dynamic guests ---
if 'guest_count' not in st.session_state:
    st.session_state.guest_count = 0
if 'misafir_durumu_onceki' not in st.session_state:
    st.session_state.misafir_durumu_onceki = "Hayır"

# --- main user fields ---
isim_soyisim = st.text_input("İsim Soyisim *")
yas         = st.number_input("Yaşınız *", min_value=1, max_value=120, step=1, key="yas")

st.write("Telefon Numarası *")
col1, col2 = st.columns([0.2, 0.8])
with col1:
    ulke_kodu = st.text_input("Ülke Kodu", value="+90", label_visibility="collapsed")
with col2:
    telefon_numarasi = st.text_input("", max_chars=10, placeholder="5XX XXX XX XX", label_visibility="collapsed")

darka_uye   = st.radio("Darka Spor Kulübü Üyesi misiniz? *", ("Evet", "Hayır"), horizontal=True)
misafir_var_mi = st.radio("Misafir/Çocuklarınızla mı katılıyorsunuz? *", ("Evet", "Hayır"), horizontal=True, index=1)

# --- reset guests if switched back to “Hayır” ---
if misafir_var_mi == "Hayır" and st.session_state.misafir_durumu_onceki == "Evet":
    # remove all guest-related keys
    for i in range(st.session_state.guest_count):
        for suffix in ("isim", "yas"):
            key = f"guest_{i}_{suffix}"
            if key in st.session_state:
                del st.session_state[key]
    st.session_state.guest_count = 0

st.session_state.misafir_durumu_onceki = misafir_var_mi

# --- guest section: always render if “Evet” ---
guest_list = []
if misafir_var_mi == "Evet":
    st.subheader("Misafir/Çocuk Bilgileri")
    btn_col1, btn_col2, _ = st.columns([0.15, 0.15, 0.7])
    with btn_col1:
        if st.button("➕ Ekle", use_container_width=True):
            st.session_state.guest_count += 1
    with btn_col2:
        if st.button("➖ Sil", use_container_width=True, disabled=st.session_state.guest_count == 0):
            idx = st.session_state.guest_count - 1
            # clear that guest’s state
            for suffix in ("isim", "yas"):
                key = f"guest_{idx}_{suffix}"
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.guest_count = idx

    # now render inputs for each guest
    for i in range(st.session_state.guest_count):
        c1, c2 = st.columns([0.6, 0.4])
        with c1:
            st.text_input(f"Misafir {i+1} İsim Soyisim", key=f"guest_{i}_isim")
        with c2:
            st.number_input(f"Misafir {i+1} Yaş", min_value=0, max_value=120, step=1, key=f"guest_{i}_yas")

# --- submit ---
st.markdown("---")
if st.button("Kaydı Tamamla"):
    # basic validation
    if not isim_soyisim or not telefon_numarasi or not yas:
        st.error("Lütfen tüm zorunlu alanları doldurun.")
    elif len(telefon_numarasi) != 10 or not telefon_numarasi.isdigit():
        st.error("Lütfen geçerli bir telefon numarası girin.")
    else:
        # build guest_list from state
        if misafir_var_mi == "Evet":
            for i in range(st.session_state.guest_count):
                name = st.session_state.get(f"guest_{i}_isim", "").strip()
                age  = st.session_state.get(f"guest_{i}_yas", 0)
                if name:
                    guest_list.append({"isim": name.lower(), "yas": age})

        # final payload
        registration_data = {
            "isim_soyisim":    isim_soyisim.lower(),
            "yas":             yas,
            "telefon_numarasi": f"{ulke_kodu}{telefon_numarasi}",
            "darka_uyesi":     darka_uye.lower(),
            "misafir_durumu":  misafir_var_mi.lower(),
            "misafirler":      guest_list
        }
        # add timestamp & send
        registration_data["submit_timestamp"] = datetime.datetime.utcnow().isoformat()
        db.collection("event_participants").add(registration_data)

        st.success("Kaydınız başarıyla tamamlandı!")
        st.balloons()
        st.json(registration_data)
