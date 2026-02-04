import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. BASE DE DATOS PROFESIONAL ---
def conectar_db():
    conn = sqlite3.connect('cartera_lesthy_definitiva_v7.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono_cliente TEXT, 
                  monto_base REAL, interes_p REAL, total_pagar REAL, cuotas_totales INTEGER, 
                  cuotas_pagadas INTEGER, malos_pagos INTEGER, movilidad TEXT, 
                  proxima_fecha TEXT, reputacion TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion (mi_tel TEXT)''')
    conn.commit()
    return conn

conn = conectar_db()

def obtener_mi_tel():
    cur = conn.cursor()
    cur.execute("SELECT mi_tel FROM configuracion")
    result = cur.fetchone()
    return result[0] if result else "573000000000"

# --- 2. INTERFAZ ---
st.set_page_config(page_title="Lesthy_bot Master Pro", layout="wide")
st.sidebar.header("⚙️ Configuración Maestra")
mi_numero = st.sidebar.text_input("Tu WhatsApp (Ej: 57310...) ", value=obtener_mi_tel())
if st.sidebar.button("💾 Guardar Mi Configuración"):
    conn.cursor().execute("DELETE FROM configuracion")
    conn.cursor().execute("INSERT INTO configuracion (mi_tel) VALUES (?)", (mi_numero,))
    conn.commit()
    st.sidebar.success("Configuración Guardada")

menu = st.sidebar.radio("MENÚ DE CONTROL", [
    "🔥 Nuevo Préstamo / Vista Previa", 
    "✅ Cobros Activos (WhatsApp)", 
    "🚨 LISTA NEGRA (Automática)", 
    "🏆 Historial de Ganancias",
    "🔧 Administrador y Edición Total"
])

# --- MÓDULO A: REGISTRO CON VISTA PREVIA ---
if menu == "🔥 Nuevo Préstamo / Vista Previa":
    st.subheader("📝 Simulación y Apertura de Crédito")
    col1, col2 = st.columns(2)
    with col1:
        n = st.text_input("👤 Nombre del Cliente")
        t_c = st.text_input("📱 WhatsApp Cliente (Ej: 57315...)")
        m = st.number_input("💰 Capital (COP)", min_value=0, step=10000)
        i = st.number_input("📈 Interés (%)", value=10.0)
    with col2:
        c = st.number_input("🔢 Cuotas", min_value=1, value=1)
        mov = st.selectbox("🔄 Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
        f = st.date_input("📅 Fecha Inicio")

    if m > 0:
        total_p = m * (1 + (i / 100))
        valor_c = total_p / c
        st.markdown("---")
        st.subheader("📊 Análisis del Préstamo")
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital", f"${m:,.0f}".replace(",","."))
        m2.metric("Ganancia", f"${(total_p - m):,.0f}".replace(",","."), delta=f"{i}%")
        m3.metric("Total", f"${total_p:,.0f}".replace(",","."))
        st.progress(m / total_p)
        st.write("**Calificación Inicial:**")
        cb, cm = st.columns(2)
        v_b, v_m = cb.checkbox("✅ Buen Cliente", False), cm.checkbox("🚨 Moroso", False)

        if st.button("🚀 ACTIVAR PRÉSTAMO"):
            if v_b or v_m:
                rep = "Buen Cliente" if v_b else "Cliente Moroso"
                conn.cursor().execute("""INSERT INTO registros 
                    (nombre, telefono_cliente, monto_base, interes_p, total_pagar, cuotas_totales, 
                     cuotas_pagadas, malos_pagos, movilidad, proxima_fecha, reputacion) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (n, t_c, m, i, total_p, c, 0, 0, mov, f.strftime('%Y-%m-%d'), rep))
                conn.commit()
                st.success("Préstamo Activado")
            else: st.warning("Seleccione calificación.")

# --- MÓDULO B: COBROS + REENVÍO A TU NÚMERO ---
elif menu == "✅ Cobros Activos (WhatsApp)":
    st.subheader("📈 Gestión de Cobros (Envío a tu WhatsApp)")
    df = pd.read_sql_query("SELECT * FROM registros WHERE cuotas_pagadas < cuotas_totales AND reputacion != 'Cliente Moroso'", conn)
    
    for _, row in df.iterrows():
        with st.expander(f"👤 {row['nombre']} | Próximo: {row['proxima_fecha']}"):
            if st.button(f"Registrar Pago Cuota {row['cuotas_pagadas']+1}", key=f"p_{row['id']}"):
                hoy, fecha_p = datetime.now().date(), datetime.strptime(row['proxima_fecha'], '%Y-%m-%d').date()
                m_pagos = row['malos_pagos'] + (1 if hoy > fecha_p else 0)
                nuevas_p = row['cuotas_pagadas'] + 1
                estado = "Cliente Moroso" if m_pagos >= 5 else ("Finalizado" if nuevas_p >= row['cuotas_totales'] else "Buen Cliente")
                
                dias = {"Diario":1, "Semanal":7, "Quincenal":15, "Mensual":30}[row['movilidad']]
                sig_f = (fecha_p + timedelta(days=dias)).strftime('%Y-%m-%d')
                conn.cursor().execute("UPDATE registros SET cuotas_pagadas=?, malos_pagos=?, proxima_fecha=?, reputacion=? WHERE id=?", 
                                      (nuevas_p, m_pagos, sig_f, estado, row['id']))
                conn.commit()
                
                # REENVÍO A TU NÚMERO
                msg = f"*🧾 REPORTE RECIBO - LESTHY_BOT*\n\n*Para:* {row['nombre']}\n*WhatsApp:* {row['telefono_cliente']}\n*Cuota:* {nuevas_p}/{row['cuotas_totales']}\n*Estado:* {estado}\n\n_Favor reenviar al cliente._".replace(",",".")
                url_wa = f"https://wa.me/{mi_numero}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{url_wa}" target="_blank">🟢 ENVIAR INFORMACIÓN A MI WHATSAPP</a>', unsafe_allow_html=True)
                st.rerun()

# --- MÓDULO E: ADMINISTRADOR Y EDICIÓN TOTAL ---
elif menu == "🔧 Administrador y Edición Total":
    st.subheader("⚙️ Edición Maestra por ID")
    df_all = pd.read_sql_query("SELECT * FROM registros", conn)
    st.dataframe(df_all, use_container_width=True)
    
    id_edit = st.number_input("ID del Cliente a EDITAR:", min_value=1)
    if id_edit in df_all['id'].values:
        d = df_all[df_all['id'] == id_edit].iloc[0]
        with st.form("edit_form"):
            col_e1, col_e2 = st.columns(2)
            new_n = col_e1.text_input("Nombre", d['nombre'])
            new_t = col_e1.text_input("WhatsApp Cliente", d['telefono_cliente'])
            new_m = col_e2.number_input("Capital", value=float(d['monto_base']))
            new_c = col_e2.number_input("Cuotas Totales", value=int(d['cuotas_totales']))
            new_mp = col_e2.number_input("Malos Pagos (Strikes)", value=int(d['malos_pagos']))
            new_rep = col_e1.selectbox("Reputación", ["Buen Cliente", "Cliente Moroso", "Finalizado"], index=["Buen Cliente", "Cliente Moroso", "Finalizado"].index(d['reputacion']))
            
            if st.form_submit_button("💾 GUARDAR CAMBIOS TOTALES"):
                conn.cursor().execute("""UPDATE registros SET nombre=?, telefono_cliente=?, monto_base=?, 
                    cuotas_totales=?, malos_pagos=?, reputacion=? WHERE id=?""", 
                    (new_n, new_t, new_m, new_c, new_mp, new_rep, id_edit))
                conn.commit()
                st.success("Cliente Editado")
                st.rerun()
    
    if st.button("🗑️ ELIMINAR REGISTRO"):
        conn.cursor().execute("DELETE FROM registros WHERE id=?", (id_edit,))
        conn.commit()
        st.rerun()

# --- OTROS MÓDULOS (LISTA NEGRA Y GANANCIAS) ---
elif menu == "🚨 LISTA NEGRA (Automática)":
    st.table(pd.read_sql_query("SELECT * FROM registros WHERE reputacion = 'Cliente Moroso'", conn))
elif menu == "🏆 Historial de Ganancias":
    df_f = pd.read_sql_query("SELECT * FROM registros WHERE reputacion = 'Finalizado'", conn)
    if not df_f.empty:
        st.metric("Ganancia Neta", f"${(df_f['total_pagar'].sum() - df_f['monto_base'].sum()):,.0f}".replace(",","."))
        st.dataframe(df_f)
