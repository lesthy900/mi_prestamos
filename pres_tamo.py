import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. FUNCIÓN DE ALERTA A TELEGRAM ---
def enviar_alerta_cobro(cliente, cuota_n, total_cuotas, monto, frecuencia):
    token = "8553805048:AAFNtIznh3boHALXYxcMDFmFnnQkyTX4ado"
    chat_id = "1703425585"
    
    mensaje = (
        f"💰 *ALERTA DE COBRO: TIEMPO JUSTO*\n\n"
        f"👤 *Cliente:* {cliente}\n"
        f"🔢 *Cuota:* {cuota_n} de {total_cuotas}\n"
        f"🔄 *Frecuencia:* {frecuencia}\n"
        f"💵 *Monto a Cobrar:* ${monto:,.2f}\n\n"
        f"⚡ _Acción: Realizar el cobro hoy._"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, data={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})
    except: pass

# --- 2. INTERFAZ DE USUARIO ---
st.title("📋 Gestión de Cobranzas Lesthy_bot")

with st.form("registro_cobro_avanzado"):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Cliente")
        monto_base = st.number_input("Capital Prestado (USD)", min_value=0.0)
        interes_p = st.number_input("Interés Total (%)", min_value=0.0, value=10.0)
    with col2:
        num_cuotas = st.number_input("Cantidad de Pagos", min_value=1, value=4)
        frecuencia = st.selectbox("Movilidad de Pago", ["Diario", "Semanal", "Quincenal", "Mensual"])
        fecha_inicio = st.date_input("Fecha del primer cobro")
    
    btn_guardar = st.form_submit_button("Generar Cronograma de Cobros")

# --- 3. LÓGICA DE CÁLCULO Y MOVILIDAD ---
if btn_guardar:
    monto_total = monto_base * (1 + (interes_p / 100))
    cuota_valor = monto_total / num_cuotas
    
    # Definir el salto de días según la movilidad
    dias_salto = {"Diario": 1, "Semanal": 7, "Quincenal": 15, "Mensual": 30}
    salto = dias_salto[frecuencia]
    
    st.metric("Total con Interés", f"${monto_total:,.2f}", f"Cuotas de ${cuota_valor:,.2f}")

    cronograma = []
    for i in range(1, int(num_cuotas) + 1):
        vencimiento = fecha_inicio + timedelta(days=salto * (i-1))
        cronograma.append({
            "N°": i,
            "Fecha de Cobro": vencimiento.strftime('%d/%m/%Y'),
            "Monto": f"${cuota_valor:,.2f}",
            "Estado": "🔔 Alerta Programada"
        })
        
        # Envío inmediato si la cuota coincide con hoy
        if vencimiento == datetime.now().date():
            enviar_alerta_cobro(nombre, i, num_cuotas, cuota_valor, frecuencia)

    st.table(pd.DataFrame(cronograma))
    st.success(f"✅ Se han programado {num_cuotas} cobros con movilidad {frecuencia}.")
