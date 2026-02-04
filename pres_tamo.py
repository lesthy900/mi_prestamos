import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import io

# --- 1. BASE DE DATOS PERMANENTE ---
def conectar():
    conn = sqlite3.connect('cartera_v4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prestamos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto_base REAL, 
                  interes_p REAL, total_cobrar REAL, cuotas INTEGER, movilidad TEXT, 
                  fecha_inicio TEXT, estado TEXT)''')
    conn.commit()
    return conn

# --- 2. CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Control Maestro Lesthy_bot", layout="wide")
st.title("⚖️ Sistema de Gestión y Simulación de Créditos")

conn = conectar()
menu = st.sidebar.radio("Navegación", ["Simulador / Registrar Nuevo", "Administrar / Editar / Borrar"])

# --- MÓDULO A: SIMULADOR Y REGISTRO ---
if menu == "Simulador / Registrar Nuevo":
    st.subheader("📝 Simulación de Préstamo")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Nombre del Cliente")
            m = st.number_input("Capital a prestar (COP)", min_value=0, step=10000, value=100000)
            i_porcen = st.number_input("Tasa de Interés (%)", min_value=0.0, value=10.0)
        with col2:
            c_cant = st.number_input("Cantidad de Cuotas", min_value=1, value=4)
            mov = st.selectbox("Movilidad de Cobro", ["Diario", "Semanal", "Quincenal", "Mensual"])
            f_ini = st.date_input("Fecha del Primer Cobro")

    # --- VISTA PREVIA DINÁMICA ---
    if m > 0:
        interes_ganado = m * (i_porcen / 100)
        total_final = m + interes_ganado
        cuota_indiv = total_final / c_cant
        
        st.markdown("---")
        st.subheader("👀 VISTA PREVIA (Cálculos Automáticos)")
        
        # Métricas de resumen
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital Inicial", f"${m:,.0f}".replace(",", "."))
        m2.metric("Intereses (+)", f"${interes_ganado:,.0f}".replace(",", "."), delta=f"{i_porcen}%")
        m3.metric("TOTAL A COBRAR", f"${total_final:,.0f}".replace(",", "."))

        # Barra de composición Capital vs Ganancia
        progreso = m / total_final
        st.progress(progreso)
        st.caption(f"🔵 Capital: {progreso*100:.1f}% | 🟢 Tu Ganancia Neta: {(1-progreso)*100:.1f}%")

        st.info(f"👉 El cliente pagará **{int(c_cant)}** cuotas de **${cuota_indiv:,.0f}** cada una.".replace(",", "."))

        if st.button("💾 CONFIRMAR Y GUARDAR PRÉSTAMO"):
            cur = conn.cursor()
            cur.execute("""INSERT INTO prestamos 
                        (nombre, monto_base, interes_p, total_cobrar, cuotas, movilidad, fecha_inicio, estado) 
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (n, m, i_porcen, total_final, c_cant, mov, f_ini.strftime('%Y-%m-%d'), "Buen Cliente"))
            conn.commit()
            st.success(f"✅ El préstamo de {n} ha sido archivado permanentemente.")

# --- MÓDULO B: ADMINISTRACIÓN Y EDICIÓN ---
else:
    df = pd.read_sql_query("SELECT * FROM prestamos", conn)
    if not df.empty:
        st.subheader("📋 Historial Permanente de Clientes")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        id_gestion = st.number_input("ID del Préstamo a gestionar:", min_value=int(df['id'].min()), max_value=int(df['id'].max()))
        
        # Lógica de Borrado y Edición se mantiene igual que en la versión anterior
        if st.button("🗑️ ELIMINAR PRÉSTAMO SELECCIONADO"):
            cur = conn.cursor()
            cur.execute("DELETE FROM prestamos WHERE id=?", (id_gestion,))
            conn.commit()
            st.warning(f"Registro #{id_gestion} borrado.")
            st.rerun()
    else:
        st.info("No hay datos guardados aún.")
