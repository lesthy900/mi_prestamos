import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. BASE DE DATOS (Persistencia Total de Datos y Configuración) ---
def conectar_db():
    conn = sqlite3.connect('cartera_lesthy_definitiva_final.db')
    c = conn.cursor()
    # Tabla Principal: El historial completo de cada crédito
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono_cliente TEXT, 
                  monto_base REAL, interes_p REAL, total_pagar REAL, cuotas_totales INTEGER, 
                  cuotas_pagadas INTEGER, malos_pagos INTEGER, movilidad TEXT, 
                  proxima_fecha TEXT, reputacion TEXT)''')
    # Tabla de Configuración: Para guardar tu número personal
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion (mi_tel TEXT)''')
    conn.commit()
    return conn

conn = conectar_db()

def obtener_mi_tel():
    cur = conn.cursor()
    cur.execute("SELECT mi_tel FROM configuracion")
    result = cur.fetchone()
    return result[0] if result else "573000000000"

# --- 2. CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="Lesthy_bot Master Pro", layout="wide")

# Barra Lateral: Configuración de tu número y Navegación
st.sidebar.header("⚙️ CONFIGURACIÓN MAESTRA")
mi_numero = st.sidebar.text_input("Tu WhatsApp (Ej: 57310...)", value=obtener_mi_tel())
if st.sidebar.button("💾 Guardar Mi Configuración"):
    conn.cursor().execute("DELETE FROM configuracion")
    conn.cursor().execute("INSERT INTO configuracion (mi_tel) VALUES (?)", (mi_numero,))
    conn.commit()
    st.sidebar.success("Número Guardado Correctamente")

menu = st.sidebar.radio("NAVEGACIÓN PRINCIPAL", [
    "🔥 Nuevo Préstamo / Vista Previa", 
    "✅ Gestión de Cobros (Link WhatsApp)", 
    "🚨 LISTA NEGRA (Automática)", 
    "🏆 Historial de Ganancias",
    "🔧 Editor Maestro y Administración"
])

# --- MÓDULO A: REGISTRO CON VISTA PREVIA ---
if menu == "🔥 Nuevo Préstamo / Vista Previa":
    st.subheader("📝 Apertura de Nuevo Crédito")
    col1, col2 = st.columns(2)
    with col1:
        n = st.text_input("👤 Nombre Completo del Cliente")
        t_c = st.text_input("📱 WhatsApp del Cliente (Ej: 57315...)")
        m = st.number_input("💰 Capital Prestado (COP)", min_value=0, step=10000)
        i = st.number_input("📈 Tasa de Interés (%)", value=10.0)
    with col2:
        c = st.number_input("🔢 Cantidad de Cuotas", min_value=1, value=4)
        mov = st.selectbox("🔄 Frecuencia de Pago", ["Diario", "Semanal", "Quincenal", "Mensual"])
        f = st.date_input("📅 Fecha de Inicio de Cobro")

    if m > 0:
        total_p = m * (1 + (i / 100))
        valor_c = total_p / c
        st.markdown("---")
        st.subheader("📊 Análisis y Vista Previa")
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital", f"${m:,.0f}".replace(",","."))
        m2.metric("Ganancia Estimada", f"${(total_p - m):,.0f}".replace(",","."), delta=f"{i}%")
        m3.metric("Total a Recoger", f"${total_p:,.0f}".replace(",","."))
        
        st.progress(m / total_p)
        st.info(f"💡 Resumen: {int(c)} cuotas de ${valor_c:,.0f} ({mov})".replace(",","."))

        st.write("**Calificación Inicial (Manual):**")
        cb, cm = st.columns(2)
        v_b = cb.checkbox("✅ Empezar como BUEN CLIENTE", value=False)
        v_m = cm.checkbox("🚨 Empezar como MOROSO", value=False)

        if st.button("🚀 ACTIVAR Y GUARDAR PRÉSTAMO"):
            if v_b or v_m:
                rep_ini = "Buen Cliente" if v_b else "Cliente Moroso"
                conn.cursor().execute("""INSERT INTO registros 
                    (nombre, telefono_cliente, monto_base, interes_p, total_pagar, cuotas_totales, 
                     cuotas_pagadas, malos_pagos, movilidad, proxima_fecha, reputacion) 
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (n, t_c, m, i, total_p, c, 0, 0, mov, f.strftime('%Y-%m-%d'), rep_ini))
                conn.commit()
                st.success(f"✔️ ¡Préstamo de {n} activado!")
            else: st.warning("⚠️ Debes elegir una calificación inicial.")

# --- MÓDULO B: COBROS + LINK DE WHATSAPP (CORREGIDO) ---
elif menu == "✅ Gestión de Cobros (Link WhatsApp)":
    st.subheader("📈 Cobranza Activa")
    df = pd.read_sql_query("SELECT * FROM registros WHERE cuotas_pagadas < cuotas_totales AND reputacion != 'Cliente Moroso'", conn)
    
    for _, row in df.iterrows():
        with st.expander(f"👤 {row['nombre']} | Cuota {row['cuotas_pagadas']+1} | Próximo: {row['proxima_fecha']}"):
            if st.button(f"REGISTRAR PAGO #{row['cuotas_pagadas']+1}", key=f"btn_{row['id']}"):
                hoy = datetime.now().date()
                fecha_p = datetime.strptime(row['proxima_fecha'], '%Y-%m-%d').date()
                
                # Lógica de Malos Pagos (5 strikes = Lista Negra)
                nuevos_malos = row['malos_pagos'] + (1 if hoy > fecha_p else 0)
                nuevas_p = row['cuotas_pagadas'] + 1
                
                estado = "Buen Cliente"
                if nuevos_malos >= 5: estado = "Cliente Moroso"
                elif nuevas_p >= row['cuotas_totales']: estado = "Finalizado"

                salto = {"Diario":1, "Semanal":7, "Quincenal":15, "Mensual":30}[row['movilidad']]
                nueva_f = (fecha_p + timedelta(days=salto)).strftime('%Y-%m-%d')

                conn.cursor().execute("UPDATE registros SET cuotas_pagadas=?, malos_pagos=?, proxima_fecha=?, reputacion=? WHERE id=?", 
                                      (nuevas_p, nuevos_malos, nueva_f, estado, row['id']))
                conn.commit()
                
                # GENERAR ENLACE HACIA TU WHATSAPP PERSONAL (LINK DIRECTO)
                saldo = row['total_pagar'] - ((row['total_pagar']/row['cuotas_totales']) * nuevas_p)
                msg = f"*🧾 RECIBO LESTHY_BOT*\n\n*Cliente:* {row['nombre']}\n*WhatsApp:* {row['telefono_cliente']}\n*Cuota:* {nuevas_p}/{row['cuotas_totales']}\n*Saldo Pendiente:* ${saldo:,.0f}\n*Estado:* {estado}\n*Malos Pagos:* {nuevos_malos}/5\n\n_Reenviar al cliente._".replace(",",".")
                link_wa = f"https://wa.me/{mi_numero}?text={urllib.parse.quote(msg)}"
                
                st.markdown(f'''<a href="{link_wa}" target="_blank">
                    <button style="background-color:#25D366; color:white; border:none; padding:15px; border-radius:10px; cursor:pointer; width:100%; font-weight:bold;">
                        📲 OBTENER RECIBO EN MI WHATSAPP
                    </button></a>''', unsafe_allow_html=True)
                st.balloons()

# --- MÓDULO C: EDITOR MAESTRO (EDICIÓN TOTAL) ---
elif menu == "🔧 Editor Maestro y Administración":
    st.subheader("🛠️ Panel de Edición Maestra por ID")
    df_full = pd.read_sql_query("SELECT * FROM registros", conn)
    st.dataframe(df_full, use_container_width=True)
    
    st.markdown("---")
    id_edit = st.number_input("ID del Cliente para EDITAR o BORRAR:", min_value=1)
    
    if id_edit in df_full['id'].values:
        cl = df_full[df_full['id'] == id_edit].iloc[0]
        with st.form("edit_form"):
            st.write(f"📝 Editando: **{cl['nombre']}**")
            c1, c2 = st.columns(2)
            en = c1.text_input("Nombre", cl['nombre'])
            et = c1.text_input("WhatsApp Cliente", cl['telefono_cliente'])
            em = c2.number_input("Monto Base", value=float(cl['monto_base']))
            ect = c2.number_input("Cuotas Totales", value=int(cl['cuotas_totales']))
            ecp = c2.number_input("Cuotas Pagadas", value=int(cl['cuotas_pagadas']))
            emp = c2.number_input("Malos Pagos", value=int(cl['malos_pagos']))
            er = c1.selectbox("Reputación", ["Buen Cliente", "Cliente Moroso", "Finalizado"], 
                              index=["Buen Cliente", "Cliente Moroso", "Finalizado"].index(cl['reputacion']))
            
            if st.form_submit_button("💾 GUARDAR CAMBIOS"):
                conn.cursor().execute("""UPDATE registros SET nombre=?, telefono_cliente=?, monto_base=?, 
                    cuotas_totales=?, cuotas_pagadas=?, malos_pagos=?, reputacion=? WHERE id=?""", 
                    (en, et, em, ect, ecp, emp, er, id_edit))
                conn.commit()
                st.success("✔️ Registro actualizado.")
                st.rerun()

    if st.button("🗑️ ELIMINAR CLIENTE PERMANENTEMENTE"):
        conn.cursor().execute("DELETE FROM registros WHERE id=?", (id_edit,))
        conn.commit()
        st.rerun()

# --- MÓDULOS DE ANÁLISIS ---
elif menu == "🚨 LISTA NEGRA (Automática)":
    st.subheader("🔴 Lista Negra (+5 Malos Pagos)")
    st.table(pd.read_sql_query("SELECT * FROM registros WHERE reputacion = 'Cliente Moroso'", conn))

elif menu == "🏆 Historial de Ganancias":
    st.subheader("🏁 Resultados de Negocios Finalizados")
    df_f = pd.read_sql_query("SELECT * FROM registros WHERE reputacion = 'Finalizado'", conn)
    if not df_f.empty:
        neto = df_f['total_pagar'].sum() - df_f['monto_base'].sum()
        st.metric("Ganancia Neta Total", f"${neto:,.0f}".replace(",","."), delta="💰")
        st.dataframe(df_f)
    else: st.info("No hay préstamos finalizados aún.")
