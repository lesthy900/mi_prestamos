import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

# --- 1. BASE DE DATOS ---
def conectar_db():
    conn = sqlite3.connect('cartera_lesthy_final_whatsapp.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, monto_base REAL, 
                  total_pagar REAL, cuotas_totales INTEGER, cuotas_pagadas INTEGER, 
                  malos_pagos INTEGER, movilidad TEXT, proxima_fecha TEXT, reputacion TEXT)''')
    conn.commit()
    return conn

conn = conectar_db()

# --- 2. FUNCIÓN PARA GENERAR MENSAJE DE WHATSAPP ---
def generar_link_whatsapp(tel, nombre, cuota_n, total_c, monto_p, saldo, reputacion):
    mensaje = f"""*🧾 RECIBO DE PAGO - LESTHY_BOT*
    
*Cliente:* {nombre}
*Cuota Pagada:* {cuota_n} de {total_c}
*Monto Pagado:* ${monto_p:,.0f}
*Saldo Restante:* ${saldo:,.0f}
*Estado de Cuenta:* {'✅ AL DÍA' if reputacion == 'Buen Cliente' else '⚠️ EN OBSERVACIÓN'}

¡Gracias por su puntualidad! 🚀""".replace(",", ".")
    
    # Codificar para URL
    texto_url = urllib.parse.quote(mensaje)
    return f"https://wa.me/{tel}?text={texto_url}"

# --- 3. INTERFAZ ---
st.set_page_config(page_title="Lesthy_bot VIP", layout="wide")
st.title("🛡️ Sistema de Gestión y Recibos WhatsApp")

menu = st.sidebar.radio("MENÚ", ["🔥 Nuevo Préstamo", "✅ Cobros y WhatsApp", "🚨 LISTA NEGRA", "🔧 Administrador"])

# --- MÓDULO A: REGISTRO ---
if menu == "🔥 Nuevo Préstamo":
    st.subheader("📝 Nuevo Crédito")
    col1, col2 = st.columns(2)
    with col1:
        n = st.text_input("👤 Nombre")
        t = st.text_input("📱 WhatsApp (Ej: 573001234567)")
        m = st.number_input("💰 Monto (COP)", min_value=0, step=10000)
    with col2:
        c = st.number_input("🔢 Cuotas", min_value=1)
        mov = st.selectbox("🔄 Movilidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
        f = st.date_input("📅 Inicio")

    # Checkboxes manuales (Desmarcados)
    st.write("**Calificación Inicial:**")
    cb, cm = st.columns(2)
    v_b = cb.checkbox("✅ Buen Cliente", value=False)
    v_m = cm.checkbox("🚨 Moroso", value=False)

    if st.button("🚀 GUARDAR PRÉSTAMO"):
        if (v_b or v_m) and m > 0:
            total = m * 1.10 # 10% Interés ejemplo
            rep = "Buen Cliente" if v_b else "Cliente Moroso"
            cur = conn.cursor()
            cur.execute("INSERT INTO registros (nombre, telefono, monto_base, total_pagar, cuotas_totales, cuotas_pagadas, malos_pagos, movilidad, proxima_fecha, reputacion) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (n, t, m, total, c, 0, 0, mov, f.strftime('%Y-%m-%d'), rep))
            conn.commit()
            st.success("Guardado correctamente.")
        else: st.warning("Complete todos los campos y calificación.")

# --- MÓDULO B: COBROS + WHATSAPP ---
elif menu == "✅ Cobros y WhatsApp":
    st.subheader("📈 Gestión de Cobros")
    df = pd.read_sql_query("SELECT * FROM registros WHERE cuotas_pagadas < cuotas_totales", conn)
    
    for _, row in df.iterrows():
        with st.expander(f"👤 {row['nombre']} | Cuota {row['cuotas_pagadas']+1}"):
            if st.button(f"Registrar Pago Cuota {row['cuotas_pagadas']+1}", key=f"pay_{row['id']}"):
                # Lógica automática de Mal Pago
                hoy = datetime.now().date()
                fecha_p = datetime.strptime(row['proxima_fecha'], '%Y-%m-%d').date()
                m_pagos = row['malos_pagos'] + (1 if hoy > fecha_p else 0)
                
                nuevas_p = row['cuotas_pagadas'] + 1
                valor_cuota = row['total_pagar'] / row['cuotas_totales']
                saldo = row['total_pagar'] - (valor_cuota * nuevas_p)
                
                # Regla de los 5 Strikes
                rep = "Cliente Moroso" if m_pagos >= 5 else "Buen Cliente"
                
                # Actualizar DB
                conn.cursor().execute("UPDATE registros SET cuotas_pagadas=?, malos_pagos=?, reputacion=? WHERE id=?", (nuevas_p, m_pagos, rep, row['id']))
                conn.commit()
                
                # GENERAR RECIBO
                link = generar_link_whatsapp(row['telefono'], row['nombre'], nuevas_p, row['cuotas_totales'], valor_cuota, saldo, rep)
                st.markdown(f'''<a href="{link}" target="_blank" style="text-decoration:none;">
                    <button style="background-color:#25D366; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer;">
                        📱 ENVIAR RECIBO POR WHATSAPP
                    </button></a>''', unsafe_allow_html=True)
                st.success("Pago registrado. Haz clic en el botón verde para enviar el recibo.")

# --- MÓDULO C: LISTA NEGRA ---
elif menu == "🚨 LISTA NEGRA":
    df_m = pd.read_sql_query("SELECT * FROM registros WHERE reputacion = 'Cliente Moroso'", conn)
    st.error("⚠️ CLIENTES CON MÁS DE 5 MALOS PAGOS")
    st.table(df_m)

# --- MÓDULO D: ADMINISTRADOR ---
elif menu == "🔧 Administrador":
    df_t = pd.read_sql_query("SELECT * FROM registros", conn)
    st.dataframe(df_t)
