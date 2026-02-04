import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import requests

# --- 1. NOTIFICACIÓN A TELEGRAM CON ESTADO ---
def notificar_estado(cliente, estado, cuota):
    token = "8553805048:AAFNtIznh3boHALXYxcMDFmFnnQkyTX4ado"
    chat_id = "1703425585"
    emoji = "✅" if "Buen" in estado else "🚨"
    mensaje = (
        f"{emoji} *ACTUALIZACIÓN DE PAGO*\n\n"
        f"👤 *Cliente:* {cliente}\n"
        f"🔢 *Cuota:* {cuota}\n"
        f"📊 *Estado:* {estado}\n"
        f"📅 *Fecha:* {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, data={"chat_id": chat_id, "text": mensaje, "parse_mode": "Markdown"})
    except: pass

# --- 2. CONFIGURACIÓN ---
st.title("🛡️ Gestión de Cartera y Calificación Lesthy_bot")

if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = []

# --- 3. ENTRADA DE DATOS ---
col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Nombre del cliente")
    monto = st.number_input("Monto (COP)", min_value=0, step=10000)
    interes = st.number_input("Interés (%)", value=10.0)
with col2:
    cuotas = st.number_input("Cuotas", min_value=1, value=1)
    movilidad = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
    f_cobro = st.date_input("Fecha Primer Cobro")

# --- 4. VISTA PREVIA Y CALIFICACIÓN DINÁMICA ---
if monto > 0:
    total_p = monto * (1 + (interes / 100))
    v_cuota = total_p / cuotas
    hoy = datetime.now().date()
    
    st.markdown("---")
    st.subheader("👀 Bitácora de Pagos y Reputación")

    dias_map = {"Diario": 1, "Semanal": 7, "Quincenal": 15, "Mensual": 30}
    reputacion_final = "Buen Cliente"
    calendario_info = []

    for i in range(int(cuotas)):
        fecha_v = f_cobro + timedelta(days=dias_map[movilidad] * i)
        f_str = fecha_v.strftime('%d/%m/%Y')
        
        # Lógica de Calificación
        col_check, col_status = st.columns([2, 1])
        with col_check:
            pago_realizado = st.checkbox(f"Cuota {i+1}: {f_str} (${v_cuota:,.0f})".replace(",","."), key=f"c_{i}")
        
        with col_status:
            if pago_realizado:
                st.success("🟢 Pagado a tiempo")
            elif hoy > fecha_v:
                st.error("🔴 MOROSO")
                reputacion_final = "Cliente Moroso"
            else:
                st.warning("⏳ Pendiente")

        calendario_info.append(f"{f_str} ({'PAGADO' if pago_realizado else 'PENDIENTE'})")

    # --- 5. GUARDADO CON REPUTACIÓN ---
    if st.button("💾 Finalizar y Guardar en Excel"):
        nuevo = {
            "Cliente": nombre,
            "Total COP": f"${total_p:,.0f}".replace(",","."),
            "Reputación": reputacion_final,
            "Frecuencia": movilidad,
            "Detalle Pagos": " | ".join(calendario_info)
        }
        st.session_state.db_clientes.append(nuevo)
        notificar_estado(nombre, reputacion_final, "Resumen Final")
        st.success(f"✅ Registro guardado. Calificación: {reputacion_final}")

# --- 6. TABLA GENERAL Y EXCEL ---
if st.session_state.db_clientes:
    st.markdown("---")
    df = pd.DataFrame(st.session_state.db_clientes)
    st.dataframe(df)
    
    # Generar Excel con Reputación
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 Descargar Reporte con Calificaciones", buffer.getvalue(), "Reporte_Clientes.xlsx")
