import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- 1. BASE DE DATOS PERMANENTE (Persistencia Total) ---
def conectar_db():
    conn = sqlite3.connect('cartera_lesthy_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, monto_base REAL, 
                  interes_p REAL, total_cobrar REAL, cuotas INTEGER, movilidad TEXT, 
                  inicio TEXT, reputacion TEXT)''')
    conn.commit()
    return conn

conn = conectar_db()

# --- 2. CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Lesthy_bot | Gestión VIP", layout="wide")
st.title("🛡️ Sistema de Gestión de Cartera Lesthy_bot")

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

    # ANÁLISIS COMPLETO Y VISTA PREVIA DINÁMICA
    if monto > 0:
        total_p = monto * (1 + (interes / 100))
        valor_cuota = total_p / cuotas
        
        st.markdown("---")
        st.subheader("📊 Análisis de Retorno de Inversión")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital a Recuperar", f"${monto:,.0f}".replace(",", "."))
        m2.metric("Intereses Ganados", f"${(total_p - monto):,.0f}".replace(",", "."), delta=f"{interes}%")
        m3.metric("TOTAL A COBRAR", f"${total_p:,.0f}".replace(",", "."))

        # Barra de Composición Protegida
        progreso = monto / total_p
        st.progress(progreso)
        st.caption(f"🔵 Capital: {progreso*100:.1f}% | 🟢 Tu Ganancia: {(1-progreso)*100:.1f}%")
        
        st.info(f"💡 El cliente pagará **{int(cuotas)} cuotas** de **${valor_cuota:,.0f}** ({movilidad})".replace(",", "."))

        # CORRECCIÓN: Checkboxes manuales desmarcados por defecto
        st.write("**Defina la Reputación para Guardar:**")
        col_bueno, col_malo = st.columns(2)
        buen_cliente = col_bueno.checkbox("✅ Marcar como BUEN CLIENTE", value=False)
        moroso = col_malo.checkbox("🚨 Marcar como CLIENTE MOROSO", value=False)

        if st.button("🚀 GUARDAR PRÉSTAMO PERMANENTE"):
            if not buen_cliente and not moroso:
                st.warning("⚠️ Debe seleccionar una calificación (Buen Cliente o Moroso) antes de guardar.")
            elif buen_cliente and moroso:
                st.error("❌ No puede marcar ambas opciones al mismo tiempo.")
            else:
                estado_final = "Buen Cliente" if buen_cliente else "Cliente Moroso"
                cur = conn.cursor()
                cur.execute("""INSERT INTO registros 
                            (nombre, monto_base, interes_p, total_cobrar, cuotas, movilidad, inicio, reputacion) 
                            VALUES (?,?,?,?,?,?,?,?)""",
                            (nombre, monto, interes, total_p, cuotas, movilidad, f_inicio.strftime('%Y-%m-%d'), estado_final))
                conn.commit()
                st.success(f"✔️ Cliente {nombre} guardado exitosamente en la lista de {estado_final}.")

# --- MÓDULO B: CLIENTES BUENOS ---
elif menu == "✅ Clientes Buenos":
    st.subheader("🟢 Cartera de Clientes al Día")
    df_buenos = pd.read_sql_query("SELECT id, nombre, total_cobrar, cuotas, movilidad, inicio FROM registros WHERE reputacion = 'Buen Cliente'", conn)
    if not df_buenos.empty:
        st.dataframe(df_buenos, use_container_width=True)
    else:
        st.info("No hay clientes con buena calificación actualmente.")

# --- MÓDULO C: LISTA NEGRA (Apartado Independiente) ---
elif menu == "🚨 LISTA NEGRA (Morosos)":
    st.subheader("🔴 Control de Clientes Morosos / Malos")
    st.markdown("⚠️ *Estos registros están separados de la cartera general para cobro urgente.*")
    df_malos = pd.read_sql_query("SELECT id, nombre, total_cobrar, cuotas, movilidad, inicio FROM registros WHERE reputacion = 'Cliente Moroso'", conn)
    if not df_malos.empty:
        st.error("LISTA DE MOROSOS:")
        st.table(df_malos)
    else:
        st.success("🎉 ¡Felicidades! No hay clientes morosos en el sistema.")

# --- MÓDULO D: ADMINISTRACIÓN Y EDICIÓN TOTAL POR ID ---
elif menu == "🔧 Administrar y Editar por ID":
    st.subheader("🛠️ Panel de Control Maestro")
    df_total = pd.read_sql_query("SELECT * FROM registros", conn)
    
    if not df_total.empty:
        st.dataframe(df_total, use_container_width=True)
        
        st.markdown("---")
        id_sel = st.number_input("ID del Préstamo para EDITAR o BORRAR:", min_value=int(df_total['id'].min()), max_value=int(df_total['id'].max()))
        
        datos = df_total[df_total['id'] == id_sel].iloc[0]

        with st.expander(f"📝 Modificar Información de: {datos['nombre']} (ID #{id_sel})"):
            with st.form("edicion_total"):
                nuevo_n = st.text_input("Nombre", value=datos['nombre'])
                nuevo_m = st.number_input("Monto Base", value=float(datos['monto_base']))
                nuevas_c = st.number_input("Cuotas", value=int(datos['cuotas']))
                nueva_mov = st.selectbox("Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"], 
                                         index=["Diario", "Semanal", "Quincenal", "Mensual"].index(datos['movilidad']))
                
                st.write("**Actualizar Reputación:**")
                cb, cm = st.columns(2)
                v_bueno = cb.checkbox("✅ Cambiar a Buen Cliente", value=(datos['reputacion'] == "Buen Cliente"))
                v_malo = cm.checkbox("🚨 Cambiar a Moroso", value=(datos['reputacion'] == "Cliente Moroso"))
                nuevo_estado = "Buen Cliente" if v_bueno and not v_malo else "Cliente Moroso"

                if st.form_submit_button("💾 ACTUALIZAR TODO"):
                    cur = conn.cursor()
                    cur.execute("""UPDATE registros SET nombre=?, monto_base=?, cuotas=?, movilidad=?, reputacion=? 
                                   WHERE id=?""", (nuevo_n, nuevo_m, nuevas_c, nueva_mov, nuevo_estado, id_sel))
                    conn.commit()
                    st.success("🔄 Información actualizada correctamente.")
                    st.rerun()

        if st.button("🗑️ BORRAR CLIENTE PERMANENTEMENTE"):
            cur = conn.cursor()
            cur.execute("DELETE FROM registros WHERE id=?", (id_sel,))
            conn.commit()
            st.warning(f"ID #{id_sel} eliminado.")
            st.rerun()

        # Excel con motor corregido
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_total.to_excel(writer, index=False)
        st.download_button("📥 DESCARGAR REPORTE TOTAL (Excel)", buffer.getvalue(), "Cartera_Lesthy_Total.xlsx")

