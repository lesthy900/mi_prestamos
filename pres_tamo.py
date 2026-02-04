import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import io

# --- 1. CONEXIÓN PERMANENTE ---
def conectar():
    conn = sqlite3.connect('cartera_v3.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prestamos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto REAL, 
                  interes REAL, cuotas INTEGER, movilidad TEXT, fecha_inicio TEXT, 
                  estado TEXT)''')
    conn.commit()
    return conn

# --- 2. INTERFAZ ---
st.set_page_config(page_title="Control Maestro Lesthy_bot", layout="wide")
st.title("⚖️ Panel de Control Total de Préstamos")

menu = st.sidebar.radio("Navegación", ["Registrar Nuevo", "Administrar / Editar / Borrar"])
conn = conectar()

# --- MÓDULO A: REGISTRO ---
if menu == "Registrar Nuevo":
    with st.form("nuevo"):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Nombre")
            m = st.number_input("Monto (COP)", step=10000)
            i = st.number_input("Interés %", value=10.0)
        with col2:
            c = st.number_input("Cuotas", min_value=1)
            mov = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
            f = st.date_input("Fecha Inicio")
        
        if st.form_submit_button("Guardar Préstamo"):
            cur = conn.cursor()
            cur.execute("INSERT INTO prestamos (nombre, monto, interes, cuotas, movilidad, fecha_inicio, estado) VALUES (?,?,?,?,?,?,?)",
                        (n, m, i, c, mov, f.strftime('%Y-%m-%d'), "Buen Cliente"))
            conn.commit()
            st.success(f"✅ Préstamo para {n} guardado con éxito.")

# --- MÓDULO B: ADMINISTRACIÓN TOTAL ---
else:
    df = pd.read_sql_query("SELECT * FROM prestamos", conn)
    if not df.empty:
        st.subheader("📋 Lista General de Clientes")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.subheader("🔧 Modo Editor (Usa el ID)")
        
        id_edit = st.number_input("Escribe el ID del préstamo para modificar:", min_value=int(df['id'].min()), max_value=int(df['id'].max()))
        
        # Cargar datos actuales del ID seleccionado
        datos_id = df[df['id'] == id_edit].iloc[0]

        with st.expander(f"⚙️ Editar Préstamo #{id_edit} - {datos_id['nombre']}"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                nuevo_n = st.text_input("Editar Nombre", value=datos_id['nombre'])
                nuevo_m = st.number_input("Editar Monto", value=float(datos_id['monto']))
                nuevo_est = st.selectbox("Tipo de Cliente", ["Buen Cliente", "Cliente Moroso", "En Seguimiento"], index=0)
            with col_e2:
                nueva_c = st.number_input("Editar Cuotas", value=int(datos_id['cuotas']))
                nueva_f = st.date_input("Editar Fecha de Inicio", value=datetime.strptime(datos_id['fecha_inicio'], '%Y-%m-%d'))
            
            c1, c2 = st.columns(2)
            if c1.button("💾 GUARDAR CAMBIOS"):
                cur = conn.cursor()
                cur.execute("""UPDATE prestamos SET nombre=?, monto=?, cuotas=?, fecha_inicio=?, estado=? 
                               WHERE id=?""", (nuevo_n, nuevo_m, nueva_c, nueva_f.strftime('%Y-%m-%d'), nuevo_est, id_edit))
                conn.commit()
                st.success("🔄 Información actualizada correctamente.")
                st.rerun()

            if c2.button("🗑️ BORRAR PRÉSTAMO PERMANENTE"):
                cur = conn.cursor()
                cur.execute("DELETE FROM prestamos WHERE id=?", (id_edit,))
                conn.commit()
                st.warning(f"Préstamo #{id_edit} eliminado del sistema.")
                st.rerun()
    else:
        st.info("No hay préstamos registrados.")
