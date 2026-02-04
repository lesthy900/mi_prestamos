import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import io

# --- 1. BASE DE DATOS PERSISTENTE ---
def conectar_db():
    conn = sqlite3.connect('cartera_lesthy.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto REAL, 
                  total_pagar REAL, cuotas INTEGER, movilidad TEXT, 
                  inicio TEXT, reputacion TEXT)''')
    conn.commit()
    return conn

# --- 2. CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Gestión de Cartera Lesthy", layout="wide")
st.title("⚖️ Panel de Control Total de Préstamos")

conn = conectar_db()
menu = st.sidebar.radio("Navegación", ["Registrar Nuevo", "Administrar / Editar / Borrar"])

# --- MÓDULO A: REGISTRAR NUEVO CON VISTA PREVIA ---
if menu == "Registrar Nuevo":
    st.subheader("📝 Ingreso de Datos")
    
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("Nombre del cliente")
            monto = st.number_input("Monto (COP)", min_value=0, step=10000, value=0)
            interes = st.number_input("Interés (%)", value=10.0)
        with c2:
            cuotas = st.number_input("Cuotas", min_value=1, value=1)
            movilidad = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
            f_inicio = st.date_input("Fecha Inicio", value=datetime.now())

    # --- VISTA PREVIA DINÁMICA (Cálculos antes de guardar) ---
    if monto > 0:
        total_p = monto * (1 + (interes / 100))
        valor_c = total_p / cuotas
        
        st.markdown("---")
        st.subheader("📊 Análisis de Retorno de Inversión") # Estilo de tu imagen
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital a Recuperar", f"${monto:,.0f}".replace(",", "."))
        m2.metric("Intereses Ganados", f"${(total_p - monto):,.0f}".replace(",", "."), delta=f"{interes}%")
        m3.metric("TOTAL A COBRAR", f"${total_p:,.0f}".replace(",", "."))

        # Barra de Composición Protegida
        st.write("**Composición del Cobro Total (Capital vs Interés):**")
        progreso = monto / total_p
        st.progress(progreso)
        
        st.info(f"💡 El cliente pagará {int(cuotas)} cuotas de ${valor_c:,.0f} ({movilidad})".replace(",", "."))

        # Checkboxes de Reputación
        st.write("**Calificación del Cliente:**")
        col_bueno, col_malo = st.columns(2)
        buen_cliente = col_bueno.checkbox("✅ Buen Cliente", value=True)
        moroso = col_malo.checkbox("🚨 Cliente Moroso")
        
        estado = "Buen Cliente" if buen_cliente and not moroso else "Cliente Moroso"

        if st.button("💾 Guardar Préstamo Permanentemente"):
            cur = conn.cursor()
            cur.execute("""INSERT INTO registros (nombre, monto, total_pagar, cuotas, movilidad, inicio, reputacion) 
                           VALUES (?,?,?,?,?,?,?)""",
                        (nombre, monto, total_p, cuotas, movilidad, f_inicio.strftime('%Y-%m-%d'), estado))
            conn.commit()
            st.success(f"✔️ Cliente {nombre} guardado como {estado}")

# --- MÓDULO B: ADMINISTRAR / EDITAR / BORRAR POR ID ---
else:
    st.subheader("📋 Lista General de Clientes")
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True) # Como en tu imagen

        st.markdown("---")
        st.subheader("🔧 Modo Editor (Usa el ID)")
        id_sel = st.number_input("Escribe el ID del préstamo para modificar:", min_value=int(df['id'].min()))
        
        col_edit, col_del = st.columns(2)
        
        if col_edit.button("📝 Actualizar Información"):
            st.info(f"Para editar el ID {id_sel}, cambia los valores en el registro y vuelve a guardar.")
            
        if col_del.button("🗑️ Borrar Préstamo del ID Seleccionado"):
            cur = conn.cursor()
            cur.execute("DELETE FROM registros WHERE id=?", (id_sel,))
            conn.commit()
            st.warning(f"Préstamo #{id_sel} eliminado.")
            st.rerun()

        # Botón Excel corregido
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Descargar Historial Completo", buffer.getvalue(), "Cartera_Lesthy.xlsx")
    else:
        st.info("Aún no hay clientes registrados.")
