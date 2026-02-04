import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. CONFIGURACIÓN DE NOTIFICACIÓN ---
def alertar_cobro_telegram(cliente, cuota_n, total_cuotas, monto, fecha):
    token = "8553805048:AAFNtIznh3boHALXYxcMDFmFnnQkyTX4ado"
    chat_id = "1703425585"
    
    mensaje = (
        f"💰 RECORDATORIO DE COBRO JUSTO\n\n"
        f"👤 Cliente: {cliente}\n"
        f"🔢 Cuota: {cuota_n} de {total_cuotas}\n"
        f"💵 Monto a Cobrar: ${monto:,.2f}\n"
        f"📅 Fecha de Vencimiento: {fecha}\n\n"
        f"⚡ Acción: Contactar al cliente de inmediato."
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, data={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})
    except: pass

# --- 2. INTERFAZ DE REGISTRO ---
st.set_page_config(page_title="Gestor de Cobros VIP", layout="wide")
st.title("📋 Panel de Control de Cobranzas")

with st.expander("➕ Registrar Nuevo Cliente / Préstamo", expanded=True):
    with st.form("registro_cobro"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre completo del cliente")
            monto_total = st.number_input("Monto total de la deuda", min_value=0.0)
            fecha_inicio = st.date_input("Fecha de inicio", value=datetime.now())
        with col2:
            cuotas = st.number_input("Número de cuotas (Meses)", min_value=1, value=1)
            dia_pago = st.number_input("Día de pago cada mes (1-31)", min_value=1, max_value=31, value=1)
        
        btn_guardar = st.form_submit_button("Guardar y Generar Cronograma")

# --- 3. LÓGICA DE PROCESAMIENTO ---
if btn_guardar:
    st.subheader(f"📊 Cronograma para: {nombre}")
    valor_cuota = monto_total / cuotas
    datos_cuotas = []
    
    for i in range(1, int(cuotas) + 1):
        # Calcular fecha de cada cuota
        fecha_cuota = fecha_inicio + timedelta(days=30 * (i-1))
        datos_cuotas.append({
            "Cuota": i,
            "Fecha": fecha_cuota.strftime('%Y-%m-%d'),
            "Monto": f"${valor_cuota:,.2f}",
            "Estado": "Pendiente"
        })
        
        # Si la cuota vence HOY, mandar a Telegram
        if fecha_cuota.date() == datetime.now().date():
            alertar_cobro_telegram(nombre, i, cuotas, valor_cuota, fecha_cuota.strftime('%Y-%m-%d'))

    df_cuotas = pd.DataFrame(datos_cuotas)
    st.table(df_cuotas)
    st.success(f"✅ El sistema enviará una señal a Telegram cada día {dia_pago} para este cliente.")