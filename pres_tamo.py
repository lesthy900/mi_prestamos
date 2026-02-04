import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. CONEXIÓN A BASE DE DATOS ---
def conectar_db():
    conn = sqlite3.connect('cartera_lesthy_v5.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto REAL, 
                  cuotas INTEGER, movilidad TEXT, inicio TEXT, reputacion TEXT)''')
    conn.commit()
    return conn

conn = conectar_db()

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestor Lesthy Pro", layout="wide")
st.title("⚖️ Panel de Control y Edición Maestra")

menu = st.sidebar.radio("Navegación", ["Registrar Nuevo", "Ver y Editar Clientes"])

# --- MÓDULO A: REGISTRO ---
if menu == "Registrar Nuevo":
    st.subheader("📝 Nuevo Préstamo")
    with st.form("form_registro"):
        n = st.text_input("Nombre del Cliente")
        m = st.number_input("Monto (COP)", min_value=0, step=10000)
        c = st.number_input("Cuotas", min_value=1)
        mov = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
        f = st.date_input("Fecha Inicio")
        rep = st.selectbox("Estado Inicial", ["Buen Cliente", "Cliente Moroso"])
        
        if st.form_submit_button("Guardar Registro"):
            cur = conn.cursor()
            cur.execute("INSERT INTO registros (nombre, monto, cuotas, movilidad, inicio, reputacion) VALUES (?,?,?,?,?,?)",
                        (n, m, c, mov, f.strftime('%Y-%m-%d'), rep))
            conn.commit()
            st.success(f"✅ {n} guardado con éxito.")

# --- MÓDULO B: VER Y EDITAR (Aquí está la solución) ---
else:
    df = pd.read_sql_query("SELECT * FROM registros", conn)
    
    if not df.empty:
        st.subheader("📋 Lista General")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.subheader("🔧 Editor de Cliente por ID")
        
        # Seleccionar ID para editar
        id_edit = st.number_input("Escribe el ID para modificar:", min_value=int(df['id'].min()), max_value=int(df['id'].max()))
        
        # Cargar datos actuales del ID seleccionado
        datos = df[df['id'] == id_edit].iloc[0]

        with st.expander(f"📝 Modificar datos de: {datos['nombre']} (ID: {id_edit})"):
            with st.form("form_edicion"):
                # Cargamos los valores actuales en los campos
                nuevo_n = st.text_input("Nombre del Cliente", value=datos['nombre'])
                nuevo_m = st.number_input("Monto (COP)", value=float(datos['monto']))
                nuevo_c = st.number_input("Cuotas", value=int(datos['cuotas']))
                nuevo_mov = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"], 
                                         index=["Diario", "Semanal", "Quincenal", "Mensual"].index(datos['movilidad']))
                
                st.write("**Actualizar Reputación:**")
                # Lógica de Checkboxes solicitada
                col_b, col_m = st.columns(2)
                es_bueno = col_b.checkbox("✅ Es Buen Cliente", value=(datos['reputacion'] == "Buen Cliente"))
                es_moroso = col_m.checkbox("🚨 Es Moroso", value=(datos['reputacion'] == "Cliente Moroso"))
                
                nuevo_rep = "Buen Cliente" if es_bueno and not es_moroso else "Cliente Moroso"

                if st.form_submit_button("💾 ACTUALIZAR TODA LA INFORMACIÓN"):
                    cur = conn.cursor()
                    cur.execute("""UPDATE registros SET nombre=?, monto=?, cuotas=?, movilidad=?, reputacion=? 
                                   WHERE id=?""", (nuevo_n, nuevo_m, nuevo_c, nuevo_mov, nuevo_rep, id_edit))
                    conn.commit()
                    st.success(f"🔄 ¡Datos de {nuevo_n} actualizados correctamente!")
                    st.rerun()

        # Opción de Borrado Individual
        if st.button("🗑️ Borrar este préstamo permanentemente"):
            cur = conn.cursor()
            cur.execute("DELETE FROM registros WHERE id=?", (id_edit,))
            conn.commit()
            st.warning("Registro eliminado.")
            st.rerun()
    else:
        st.info("No hay clientes en la base de datos.")
