import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse
import io

# --- 1. BASE DE DATOS PROFESIONAL ---
def conectar_db():
    conn = sqlite3.connect('cartera_maestra_v6.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono_cliente TEXT, 
                  monto_base REAL, interes_p REAL, total_pagar REAL, cuotas_totales INTEGER, 
                  cuotas_pagadas INTEGER, malos_pagos INTEGER, movilidad TEXT, 
                  proxima_fecha TEXT, reputacion TEXT)''')
    # Tabla para guardar TU número de WhatsApp
    c.execute('''CREATE TABLE IF NOT EXISTS configuracion (mi_tel TEXT)''')
    conn.commit()
    return conn

conn = conectar_db()

# --- 2. GESTIÓN DE TU NÚMERO PERSONALIZADO ---
def obtener_mi_tel():
    cur = conn.cursor()
    cur.execute("SELECT mi_tel FROM configuracion")
    result = cur.fetchone()
    return result[0] if result else "573000000000"

# --- 3. INTERFAZ ---
st.set_page_config(page_title="Lesthy_bot Master Pro", layout="wide")
st.title("⚖️ Sistema Integral Lesthy_bot")

# Barra lateral con tu configuración
st.sidebar.header("⚙️ Configuración Maestra")
mi_numero = st.sidebar.text_input("Tu WhatsApp (Ej: 57310...) ", value=obtener_mi_tel())
if st.sidebar.button("💾 Guardar Mi Número"):
    conn.cursor().execute("DELETE FROM configuracion")
    conn.cursor().execute("INSERT INTO configuracion (mi_tel) VALUES (?)", (mi_numero,))
    conn.commit()
    st.sidebar.success("Número guardado")

menu = st.sidebar.radio("MENÚ DE CONTROL", [
    "🔥 Nuevo Préstamo / Vista Previa", 
    "✅ Cobros Activos (WhatsApp)", 
    "🚨 LISTA NEGRA (Automática)", 
    "🏆 Historial de Ganancias",
    "🔧 Administrador General"
])

# --- MÓDULO A: REGISTRO CON VISTA PREVIA ---
if menu == "🔥 Nuevo Préstamo / Vista Previa":
    st.subheader("📝 Apertura de Crédito")
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
        st.subheader("📊 Vista Previa Dinámica")
        m1, m2, m3 = st.columns(3)
        m1.metric("Capital", f"${m:,.0f}".replace(",","."))
        m2.metric("Ganancia", f"${(total_p - m):,.0f}".replace(",","."), delta=f"{i}%")
        m3.metric("Total", f"${total_p:,.0f}".replace(",","."))
        
        st.progress(m / total_p)
        st.info(f"💡 {int(c)} cuotas de ${valor_c:,.0f} ({mov})".replace(",","."))

        st.write("**Calificación Inicial:**")
        cb, cm = st.columns(2)
        v_b = cb.checkbox("✅ Buen Cliente", value=False)
        v_m = cm.checkbox("🚨 Moroso", value=False)

        if st.button("🚀 ACTIVAR PRÉSTAMO"):
            if v_b or v_m:
                rep = "Buen Cliente" if v_b else "Cliente Moroso"
                cur = conn.cursor()
                cur.execute("""INSERT INTO registros 
                            (nombre, telefono_cliente, monto_base, interes_p, total_pagar, cuotas_totales, 
                             cuotas_pagadas, malos_pagos, movilidad, proxima_fecha, reputacion) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                            (n, t_c, m, i, total_p, c, 0, 0, mov, f.strftime('%Y-%m-%d'), rep))
                conn.commit()
                st.success("Guardado permanentemente.")
            else: st.warning("Seleccione calificación.")

# --- MÓDULO B: COBROS + RECIBO PERSONALIZADO ---
elif menu == "✅ Cobros Activos (WhatsApp)":
    st.subheader("📈 Gestión de Cobros")
    df = pd.read_sql_query("SELECT * FROM registros WHERE cuotas_pagadas < cuotas_totales AND reputacion != 'Cliente Moroso'", conn)
    
    for _, row in df.iterrows():
        with st.expander(f"👤 {row['nombre']} | Próximo: {row['proxima_fecha']}"):
            if st.button(f"Registrar Pago Cuota {row['cuotas_pagadas']+1}", key=f"p_{row['id']}"):
                hoy = datetime.now().date()
                fecha_p = datetime.strptime(row['proxima_fecha'], '%Y-%m-%d').date()
                m_pagos = row['malos_pagos'] + (1 if hoy > fecha_p else 0)
                nuevas_p = row['cuotas_pagadas'] + 1
                
                estado = "Buen Cliente"
                if m_pagos >= 5: estado = "Cliente Moroso"
                elif nuevas_p >= row['cuotas_totales']: estado = "Finalizado"

                # Siguiente fecha
                dias = {"Diario":1, "Semanal":7, "Quincenal":15, "Mensual":30}[row['movilidad']]
                sig_f = (fecha_p + timedelta(days=dias)).strftime('%Y-%m-%d')

                conn.cursor().execute("UPDATE registros SET cuotas_pagadas=?, malos_pagos=?, proxima_fecha=?, reputacion=? WHERE id=?", 
                                      (nuevas_p, m_pagos, sig_f, estado, row['id']))
                conn.commit()
                
                # GENERACIÓN DEL RECIBO PERSONALIZADO
                saldo = row['total_pagar'] - ((row['total_pagar']/row['cuotas_totales']) * nuevas_p)
                msg = f"""*🧾 RECIBO LESTHY_BOT*
*Cliente:* {row['nombre']}
*Cuota:* {nuevas_p}/{row['cuotas_totales']}
*Monto Pagado:* ${(row['total_pagar']/row['cuotas_totales']):,.0f}
*Saldo Pendiente:* ${saldo:,.0f}
*Malos Pagos:* {m_pagos}/5
*Estado:* {estado}
--------------------------
_Enviado desde el panel de {mi_numero}_""".replace(",",".")
                
                url_wa = f"https://wa.me/{row['telefono_cliente']}?text={urllib.parse.quote(msg)}"
                st.markdown(f'''<a href="{url_wa}" target="_blank">
                    <button style="background-color:#25D366; color:white; border:none; padding:12px; border-radius:10px; width:100%;">
                        🟢 ENVIAR RECIBO AL CLIENTE
                    </button></a>''', unsafe_allow_html=True)
                st.rerun()

# --- MÓDULO C: LISTA NEGRA ---
elif menu == "🚨 LISTA NEGRA (Automática)":
    st.subheader("🔴 Clientes con +5 Malos Pagos")
    df_m = pd.read_sql_query("SELECT * FROM registros WHERE reputacion = 'Cliente Moroso'", conn)
    st.error("⚠️ Estas personas requieren cobro judicial / lista negra.")
    st.table(df_m)

# --- MÓDULO D: HISTORIAL DE GANANCIAS ---
elif menu == "🏆 Historial de Ganancias":
    st.subheader("🏁 Resultados de Préstamos Finalizados")
    df_f = pd.read_sql_query("SELECT * FROM registros WHERE reputacion = 'Finalizado'", conn)
    if not df_f.empty:
        cap = df_f['monto_base'].sum()
        gan = df_f['total_pagar'].sum() - cap
        c1, c2 = st.columns(2)
        c1.metric("Capital Recuperado", f"${cap:,.0f}".replace(",","."))
        c2.metric("Ganancia Neta", f"${gan:,.0f}".replace(",","."), delta="💰")
        st.dataframe(df_f)
    else: st.info("No hay préstamos finalizados aún.")

# --- MÓDULO E: ADMINISTRADOR ---
elif menu == "🔧 Administrador General":
    st.subheader("⚙️ Gestión de Base de Datos")
    df_all = pd.read_sql_query("SELECT * FROM registros", conn)
    st.dataframe(df_all)
    id_del = st.number_input("ID para borrar:", min_value=1)
    if st.button("🗑️ ELIMINAR PERMANENTE"):
        conn.cursor().execute("DELETE FROM registros WHERE id=?", (id_del,))
        conn.commit()
        st.rerun()
