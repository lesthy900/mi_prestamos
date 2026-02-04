import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import io

# --- 1. BASE DE DATOS (PERSISTENCIA) ---
# Esto evita que los datos se borren al recargar la página
def init_db():
    conn = sqlite3.connect('prestamos.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT, monto REAL, cuotas INTEGER, 
                  reputacion TEXT, detalle_pagos TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- 2. FUNCIONES DE GESTIÓN ---
def guardar_cliente(nombre, monto, cuotas, reputacion, detalle):
    c = conn.cursor()
    c.execute("INSERT INTO clientes (nombre, monto, cuotas, reputacion, detalle_pagos) VALUES (?,?,?,?,?)",
              (nombre, monto, cuotas, reputacion, detalle))
    conn.commit()

def borrar_cliente(id_cliente):
    c = conn.cursor()
    c.execute("DELETE FROM clientes WHERE id=?", (id_cliente,))
    conn.commit()

def borrar_todo():
    c = conn.cursor()
    c.execute("DELETE FROM clientes")
    conn.commit()

# --- 3. INTERFAZ DE USUARIO ---
st.set_page_config(page_title="Cartera Lesthy Pro", layout="wide")
st.title("🛡️ Gestión de Cartera Lesthy_bot (Base de Datos Real)")

# Menú Lateral para Navegación
menu = st.sidebar.selectbox("Acciones", ["Nuevo Préstamo", "Ver Historial / Editar"])

if menu == "Nuevo Préstamo":
    st.subheader("➕ Registrar Nuevo Crédito")
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre del Cliente")
        monto = st.number_input("Monto (COP)", min_value=0, step=10000)
        cuotas = st.number_input("Cuotas", min_value=1, value=1)
    with col2:
        interes = st.number_input("Interés (%)", value=10.0)
        f_cobro = st.date_input("Fecha Inicio")
        movilidad = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])

    if monto > 0:
        total_p = monto * (1 + (interes/100))
        v_cuota = total_p / cuotas
        hoy = datetime.now().date()
        
        reputacion_actual = "Buen Cliente"
        fechas_pago = []
        
        st.write("**Plan de Pagos (Checkboxes):**")
        for i in range(int(cuotas)):
            dias = {"Diario":1, "Semanal":7, "Quincenal":15, "Mensual":30}[movilidad]
            fecha_v = f_cobro + timedelta(days=dias * i)
            pago = st.checkbox(f"Cuota {i+1}: {fecha_v} (${v_cuota:,.0f})", key=f"n_{i}")
            
            estado = "PAGADO" if pago else ("PENDIENTE" if hoy <= fecha_v else "MOROSO")
            if estado == "MOROSO": reputacion_actual = "Cliente Moroso"
            fechas_pago.append(f"{fecha_v}:{estado}")

        if st.button("💾 Guardar Permanente"):
            guardar_cliente(nombre, total_p, cuotas, reputacion_actual, " | ".join(fechas_pago))
            st.success("¡Datos guardados! Ya puedes recargar la página y no se borrarán.")

elif menu == "Ver Historial / Editar":
    st.subheader("📋 Base de Datos de Clientes")
    
    # Cargar datos desde SQLite
    df = pd.read_sql_query("SELECT * FROM clientes", conn)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        # --- SECCIÓN DE EDICIÓN Y BORRADO ---
        st.markdown("---")
        st.write("**Gestión de Registros:**")
        cliente_id = st.number_input("ID del cliente para gestionar", min_value=int(df['id'].min()), max_value=int(df['id'].max()))
        
        c_del, c_edit = st.columns(2)
        with c_del:
            if st.button("🗑️ Borrar este Cliente"):
                borrar_cliente(cliente_id)
                st.warning(f"Cliente {cliente_id} eliminado.")
                st.rerun()
        
        with c_edit:
            if st.button("📝 Editar (Abrir Formulario)"):
                st.info("Función de edición: Puedes cambiar el nombre o monto en la base de datos.")
        
        if st.sidebar.button("🚨 BORRAR TODO EL HISTORIAL"):
            borrar_todo()
            st.rerun()

        # Exportar a Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Descargar Copia de Seguridad (Excel)", buffer.getvalue(), "Cartera_Permanente.xlsx")
    else:
        st.info("No hay clientes registrados aún.")
