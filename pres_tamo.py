import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. FUNCIÓN DE ALERTA ---
def enviar_alerta_cobro_full(cliente, cuota_n, total_cuotas, monto, f_emision, f_vencimiento):
    token = "8553805048:AAFNtIznh3boHALXYxcMDFmFnnQkyTX4ado"
    chat_id = "1703425585"
    mensaje = (
        f"💰 *ALERTA DE COBRO PROGRAMADO*\n\n"
        f"👤 *Cliente:* {cliente}\n"
        f"📅 *Préstamo hecho el:* {f_emision}\n"
        f"🔢 *Cuota:* {cuota_n} de {total_cuotas}\n"
        f"💵 *VALOR CUOTA:* ${monto:,.2f}\n"
        f"📅 *Vence hoy:* {f_vencimiento}\n"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, data={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})
    except: pass

# --- 2. INTERFAZ ---
st.title("🛡️ Sistema de Gestión de Cartera Lesthy_bot")

with st.form("registro_avanzado"):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Cliente")
        monto_prestado = st.number_input("Capital Entregado (USD)", min_value=0.0)
        interes_p = st.number_input("Interés Total (%)", min_value=0.0, value=10.0)
        fecha_prestamo = st.date_input("Fecha del préstamo", value=datetime.now())
    with col2:
        num_cuotas = st.number_input("Número de Cuotas", min_value=1, value=4)
        frecuencia = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
        fecha_primer_pago = st.date_input("Fecha del primer cobro")
    
    btn_registro = st.form_submit_button("Registrar y Ver Totales")

# --- 3. LÓGICA DE BARRA DE TOTALES ---
if btn_registro:
    intereses_generados = monto_prestado * (interes_p / 100)
    total_a_pagar = monto_prestado + intereses_generados
    cuota_valor = total_a_pagar / num_cuotas

    # Visualización de la Barra de Totales
    st.subheader("📊 Análisis de Retorno de Inversión")
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Capital a Recuperar", f"${monto_prestado:,.2f}")
    col_b.metric("Intereses Ganados", f"${intereses_generados:,.2f}", delta=f"{interes_p}%")
    col_c.metric("TOTAL A COBRAR", f"${total_a_pagar:,.2f}")

    # Barra visual de composición del pago
    st.write("**Composición del Cobro Total (Capital vs Interés):**")
    progreso_capital = (monto_prestado / total_a_pagar)
    st.progress(progreso_capital)
    st.caption(f"🔵 El {(progreso_capital*100):.1f}% es Capital | 🟢 El {(100 - progreso_capital*100):.1f}% es pura Ganancia")

    # Cronograma
    dias_map = {"Diario": 1, "Semanal": 7, "Quincenal": 15, "Mensual": 30}
    salto = dias_map[frecuencia]
    
    cronograma = []
    for i in range(1, int(num_cuotas) + 1):
        vencimiento = fecha_primer_pago + timedelta(days=salto * (i-1))
        cronograma.append({
            "Cuota": i,
            "Vencimiento": vencimiento.strftime('%d/%m/%Y'),
            "Monto Cuota": f"${cuota_valor:,.2f}"
        })
        if vencimiento == datetime.now().date():
            enviar_alerta_cobro_full(nombre, i, num_cuotas, cuota_valor, fecha_prestamo.strftime('%d/%m/%Y'), vencimiento.strftime('%d/%m/%Y'))

    st.table(pd.DataFrame(cronograma))
