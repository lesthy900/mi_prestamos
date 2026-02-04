import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import io

# --- 1. BASE DE DATOS PERMANENTE ---
def conectar_db():
    conn = sqlite3.connect('cartera_lesthy_total.db')
    c = conn.cursor()
    # Tabla con todos los campos solicitados
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto_base REAL, 
                  interes_p REAL, total_cobrar REAL, cuotas INTEGER, movilidad TEXT, 
                  inicio TEXT, reputacion TEXT)''')
    conn.commit()
    return conn

conn = conectar_db()

# --- 2. CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Lesthy_bot | Gestión Total", layout="wide")
st.title("🛡️ Sistema de Gestión de Cartera Lesthy_bot")

# Menú Lateral con todas las secciones
menu = st.sidebar.radio("NAVEGACIÓN", [
    "🔥 Nuevo Préstamo / Vista Previa", 
    "✅ Clientes Buenos", 
    "🚨 LISTA NEGRA (Morosos)", 
    "🔧 Administrar y Editar por ID"
])

# --- MÓDULO A: REGISTRO CON VISTA PREVIA ---
if menu == "🔥 Nuevo Préstamo / Vista Previa":
    st.subheader("📝 Simulación y Registro de Crédito")
    
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            nombre = st.text_input("👤 Nombre del cliente", placeholder="Ej: Juan Pérez")
            monto = st.number_input("💰 Monto Prestado (COP)", min_value=0, step=10000, value=0)
            interes = st.number_input("📈 Tasa de Interés (%)", value=10.0)
        with c2:
            cuotas = st.number_input("🔢 Número de Cuotas", min_value=1, value=1)
            movilidad = st.selectbox("🔄 Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
            f_inicio = st.date_input("📅 Fecha de Inicio")

    # VISTA PREVIA DINÁMICA
    if monto > 0:
        total_p = monto * (1 + (interes / 100))
        valor_c = total_p / cuotas
        
        st.markdown("---")
        st.subheader("📊 Vista Previa del Cobro")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital", f"${monto:,.0f}".replace(",", "."))
        m2.metric("Intereses", f"${(total_p - monto):,.0f}".replace(",", "."), delta=f"{interes}%")
        m3.metric("TOTAL A COBRAR", f"${total_p:,.0f}".replace(",", "."))

        progreso = monto / total_p
        st.progress(progreso)
        st.caption(f"🔵 Capital: {progreso*100:.1f}% | 🟢 Ganancia: {(1-progreso)*100:.1f}%")
        
        st.info(f"✅ Se generarán {int(cuotas)} cuotas de ${valor_c:,.0f} ({movilidad})".replace(",", "."))

        # Checkboxes de Reputación Inicial
        col_b, col_m = st.columns(2)
        es_bueno = col_b.checkbox("✅ Marcar como BUEN CLIENTE", value=True)
        es_moroso = col_m.checkbox("🚨 Marcar como MOROSO")
        reputacion_ini = "Buen Cliente" if es_bueno and not es_moroso else "Cliente Moroso"

        if st.button("🚀 GUARDAR PRÉSTAMO PERMANENTE"):
            cur = conn.cursor()
            cur.execute("""INSERT INTO registros 
                        (nombre, monto_base, interes_p, total_cobrar, cuotas, movilidad, inicio, reputacion) 
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (nombre, monto, interes, total_p, cuotas, movilidad, f_inicio.strftime('%Y-%m-%d'), reputacion_ini))
            conn.commit()
            st.success(f"✔️ ¡Préstamo de {nombre} guardado exitosamente!")

# --- MÓDULO B: CLIENTES BUENOS ---
elif menu == "✅ Clientes Buenos":
    st.subheader("🟢 Cartera de Clientes al Día")
    df_buenos = pd.read_sql_query("SELECT id, nombre, total_cobrar, cuotas, movilidad, inicio FROM registros WHERE reputacion = 'Buen Cliente'", conn)
    if not df_buenos.empty:
        st.dataframe(df_buenos, use_container_width=True)
    else:
        st.info("No hay clientes con buena calificación actualmente.")

# --- MÓDULO C: LISTA NEGRA ---
elif menu == "🚨 LISTA NEGRA (Morosos)":
    st.subheader("🔴 Lista Negra de Clientes Morosos")
    st.error("⚠️ ATENCIÓN: Clientes con pagos pendientes o mala reputación.")
    df_malos = pd.read_sql_query("SELECT id, nombre, total_cobrar, cuotas, movilidad, inicio FROM registros WHERE reputacion = 'Cliente Moroso'", conn)
    if not df_malos.empty:
        st.table(df_malos)
    else:
        st.success("🎉 No tienes clientes morosos registrados.")

# --- MÓDULO D: ADMINISTRACIÓN Y EDICIÓN TOTAL ---
elif menu == "🔧 Administrar y Editar por ID":
    st.subheader("🛠️ Panel de Control Maestro")
    df_total = pd.read_sql_query("SELECT * FROM registros", conn)
    
    if not df_total.empty:
        st.dataframe(df_total, use_container_width=True)
        
        st.markdown("---")
        id_sel = st.number_input("ID del Préstamo para EDITAR o BORRAR:", min_value=int(df_total['id'].min()), max_value=int(df_total['id'].max()))
        
        # Cargar datos para edición automática
        datos = df_total[df_total['id'] == id_sel].iloc[0]

        with st.expander(f"📝 Modificar Información de: {datos['nombre']} (ID #{id_sel})"):
            with st.form("edicion_total"):
                nuevo_nombre = st.text_input("Nombre", value=datos['nombre'])
                nuevo_monto = st.number_input("Monto Base", value=float(datos['monto_base']))
                nuevas_cuotas = st.number_input("Cuotas", value=int(datos['cuotas']))
                nueva_mov = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"], 
                                         index=["Diario", "Semanal", "Quincenal", "Mensual"].index(datos['movilidad']))
                
                st.write("**Actualizar Reputación:**")
                cb, cm = st.columns(2)
                v_bueno = cb.checkbox("✅ Buen Cliente", value=(datos['reputacion'] == "Buen Cliente"))
                v_malo = cm.checkbox("🚨 Moroso", value=(datos['reputacion'] == "Cliente Moroso"))
                nuevo_estado = "Buen Cliente" if v_bueno and not v_malo else "Cliente Moroso"

                if st.form_submit_button("💾 ACTUALIZAR TODO"):
                    # Recalcular total si el monto cambió
                    nuevo_total = nuevo_monto * (1 + (datos['interes_p']/100))
                    cur = conn.cursor()
                    cur.execute("""UPDATE registros SET nombre=?, monto_base=?, total_cobrar=?, cuotas=?, movilidad=?, reputacion=? 
                                   WHERE id=?""", (nuevo_nombre, nuevo_monto, nuevo_total, nuevas_cuotas, nueva_mov, nuevo_estado, id_sel))
                    conn.commit()
                    st.success("🔄 ¡Datos actualizados!")
                    st.rerun()

        if st.button("🗑️ BORRAR CLIENTE PERMANENTEMENTE"):
            cur = conn.cursor()
            cur.execute("DELETE FROM registros WHERE id=?", (id_sel,))
            conn.commit()
            st.warning(f"ID #{id_sel} eliminado.")
            st.rerun()

        # Botón Excel corregido
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_total.to_excel(writer, index=False)
        st.download_button("📥 DESCARGAR REPORTE TOTAL (Excel)", buffer.getvalue(), "Cartera_Lesthy_Total.xlsx")
