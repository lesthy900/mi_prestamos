import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# --- 1. INICIALIZAR BASE DE DATOS TEMPORAL ---
if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = []

# --- 2. INTERFAZ DE REGISTRO ---
st.title("🏦 Administrador de Cartera Lesthy_bot")

with st.form("registro_con_archivo"):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Cliente")
        monto = st.number_input("Monto Prestado (COP)", min_value=0, step=10000)
        interes = st.number_input("Interés (%)", min_value=0.0, value=10.0)
    with col2:
        cuotas = st.number_input("Cuotas", min_value=1, value=1)
        frecuencia = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
        f_prestamo = st.date_input("Fecha Préstamo", value=datetime.now())

    btn_guardar = st.form_submit_button("💾 Guardar Cliente y Generar Archivo")

# --- 3. LÓGICA DE GUARDADO Y TABLA ---
if btn_guardar and monto > 0:
    total = monto * (1 + (interes / 100))
    # Guardar en la base de datos interna
    nuevo_registro = {
        "Cliente": nombre,
        "Fecha Préstamo": f_prestamo.strftime('%d/%m/%Y'),
        "Monto Base": f"${monto:,.0f}".replace(",", "."),
        "Interés (%)": f"{interes}%",
        "Total a Cobrar": f"${total:,.0f}".replace(",", "."),
        "Cuotas": cuotas,
        "Movilidad": frecuencia
    }
    st.session_state.db_clientes.append(nuevo_registro)
    st.success(f"✅ Cliente {nombre} guardado en el sistema.")

# --- 4. CUADRO APARTE DE CLIENTES Y DESCARGA ---
if st.session_state.db_clientes:
    st.subheader("📋 Cuadro General de Clientes Registrados")
    df_final = pd.DataFrame(st.session_state.db_clientes)
    
    # Mostrar la tabla en la app
    st.dataframe(df_final, use_container_width=True)

    # Crear el archivo Excel en memoria para descargar
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, sheet_name='Cobranzas')
    
    st.download_button(
        label="📥 Descargar Reporte de Clientes (Excel)",
        data=buffer.getvalue(),
        file_name=f"Reporte_Cobros_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.ms-excel"
    )
