import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import requests

# --- CONFIGURACIÓN TELEGRAM ---
def notificar_telegram(mensaje):
    token = "8553805048:AAFNtIznh3boHALXYxcMDFmFnnQkyTX4ado"
    chat_id = "1703425585"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, data={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})
    except: pass

# --- BASE DE DATOS ---
if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = []

st.title("🛡️ Gestión de Cartera Lesthy_bot")

# --- REGISTRO ---
with st.form("registro_pro"):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Cliente")
        monto = st.number_input("Monto (COP)", min_value=0, step=10000)
        interes = st.number_input("Interés (%)", value=10.0)
    with col2:
        cuotas = st.number_input("Cuotas", min_value=1, value=4)
        movilidad = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
        f_inicio = st.date_input("Fecha Primer Cobro")

    if st.form_submit_button("💾 Guardar y Generar Calendario"):
        if monto > 0:
            total = monto * (1 + (interes/100))
            dias = {"Diario": 1, "Semanal": 7, "Quincenal": 15, "Mensual": 30}
            
            # Generar fechas automáticamente para Excel y Sistema
            fechas_cobro = [(f_inicio + timedelta(days=dias[movilidad] * i)).strftime('%d/%m/%Y') for i in range(int(cuotas))]
            
            nuevo = {
                "Cliente": nombre,
                "Monto Base": f"${monto:,.0f}".replace(",", "."),
                "Total con Interés": f"${total:,.0f}".replace(",", "."),
                "Movilidad": movilidad,
                "Fechas de Cobro": ", ".join(fechas_cobro)
            }
            st.session_state.db_clientes.append(nuevo)
            st.success("✅ Cliente guardado y calendario generado.")

# --- CUADRO Y EXCEL ---
if st.session_state.db_clientes:
    st.subheader("📋 Cuadro General")
    df = pd.DataFrame(st.session_state.db_clientes)
    st.dataframe(df)

    # Botón de Excel (Ahora sin error)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    
    st.download_button("📥 Descargar Excel", buffer.getvalue(), "Cobros_Lesthy.xlsx")

    # BOTÓN DE BORRADO CON AVISO A TELEGRAM
    if st.button("🗑️ Borrar toda la información"):
        st.session_state.db_clientes = []
        notificar_telegram("⚠️ *AVISO:* La base de datos de clientes ha sido borrada por el usuario.")
        st.rerun()
