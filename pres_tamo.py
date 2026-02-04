import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# --- 1. FUNCIÓN DE ALERTA A TELEGRAM (Formato COP) ---
def enviar_alerta_cobro_cop(cliente, cuota_n, total_cuotas, monto, f_emision, f_vencimiento):
    token = "8553805048:AAFNtIznh3boHALXYxcMDFmFnnQkyTX4ado"
    chat_id = "1703425585"
    
    # Formateamos el monto con puntos de miles para Colombia
    monto_formateado = f"${monto:,.0f}".replace(",", ".")
    
    mensaje = (
        f"🇨🇴 *COBRO PENDIENTE (COP)*\n\n"
        f"👤 *Cliente:* {cliente}\n"
        f"📅 *Préstamo:* {f_emision}\n"
        f"🔢 *Cuota:* {cuota_n} de {total_cuotas}\n"
        f"💵 *VALOR A COBRAR:* {monto_formateado}\n\n"
        f"📅 *Vence hoy:* {f_vencimiento}\n"
        f"⚡ _Acción: Realizar el cobro del día._"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, data={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})
    except: pass

# --- 2. INTERFAZ ---
st.title("🛡️ Sistema de Cobranzas Lesthy_bot (COP)")

with st.form("registro_cop"):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Cliente")
        monto_prestado = st.number_input("Capital Prestado (Pesos COP)", min_value=0, step=10000)
        interes_p = st.number_input("Interés Total (%)", min_value=0.0, value=10.0)
        fecha_prestamo = st.date_input("Fecha del préstamo", value=datetime.now())
    with col2:
        num_cuotas = st.number_input("Número de Cuotas", min_value=1, value=4)
        frecuencia = st.selectbox("Movilidad de Pago", ["Diario", "Semanal", "Quincenal", "Mensual"])
        fecha_primer_pago = st.date_input("Fecha del primer cobro")
    
    btn_registro = st.form_submit_button("Registrar y Calcular")

# --- 3. LÓGICA CON CORRECCIÓN DE ERROR Y FORMATO ---
if btn_registro:
    intereses_generados = monto_prestado * (interes_p / 100)
    total_a_pagar = monto_prestado + intereses_generados
    
    # Validación para evitar ZeroDivisionError
    if total_a_pagar > 0:
        cuota_valor = total_a_pagar / num_cuotas

        st.subheader("📊 Análisis de Retorno de Inversión")
        
        col_a, col_b, col_c = st.columns(3)
        # Formato de moneda colombiana
        col_a.metric("Capital", f"${monto_prestado:,.0f}".replace(",", "."))
        col_b.metric("Intereses", f"${intereses_generados:,.0f}".replace(",", "."), delta=f"{interes_p}%")
        col_c.metric("TOTAL COP", f"${total_a_pagar:,.0f}".replace(",", "."))

        # Barra visual protegida contra error
        progreso_capital = (monto_prestado / total_a_pagar)
        st.progress(progreso_capital)
        st.caption(f"🔵 Capital: {(progreso_capital*100):.1f}% | 🟢 Ganancia: {(100 - progreso_capital*100):.1f}%")

        # Cronograma
        dias_map = {"Diario": 1, "Semanal": 7, "Quincenal": 15, "Mensual": 30}
        salto = dias_map[frecuencia]
        
        cronograma = []
        for i in range(1, int(num_cuotas) + 1):
            vencimiento = fecha_primer_pago + timedelta(days=salto * (i-1))
            cronograma.append({
                "Cuota": i,
                "Fecha": vencimiento.strftime('%d/%m/%Y'),
                "Monto COP": f"${cuota_valor:,.0f}".replace(",", ".")
            })
            
            # Alerta hoy
            if vencimiento == datetime.now().date():
                enviar_alerta_cobro_cop(nombre, i, num_cuotas, cuota_valor, fecha_prestamo.strftime('%d/%m/%Y'), vencimiento.strftime('%d/%m/%Y'))

        st.table(pd.DataFrame(cronograma))
    else:
        st.error("❌ El monto debe ser mayor a 0 para realizar los cálculos.")
