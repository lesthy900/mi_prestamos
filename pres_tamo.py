import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse
import io

# =================================================================
# 1. MOTOR DE BASE DE DATOS (ESTRUCTURA DE 50 PUNTOS)
# =================================================================
def conectar_db():
    conn = sqlite3.connect('cartera_lesthy_v88_final.db')
    c = conn.cursor()
    # Tabla Maestra: Logística, Financiera y Multimedia
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nombre TEXT, telefono_cliente TEXT, monto_base REAL, interes_p REAL, 
                  meses_plazo INTEGER, total_pagar REAL, cuotas_totales INTEGER, 
                  cuotas_pagadas INTEGER, modalidad TEXT, proxima_fecha TEXT, 
                  reputacion TEXT, cedula TEXT, ciudad TEXT, direccion TEXT, foto BLOB)''')
    
    # Tabla de Gastos Operativos
    c.execute('''CREATE TABLE IF NOT EXISTS gastos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, descripcion TEXT, monto REAL, fecha TEXT)''')
    conn.commit()
    return conn

conn = conectar_db()

# =================================================================
# 2. INTERFAZ VIP (DISEÑO PROFESIONAL LESTHY)
# =================================================================
st.set_page_config(page_title="Lesthy Master V88 - COP", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    div[data-testid="metric-container"] {
        background-color: #1e2130; padding: 25px; border-radius: 20px;
        border: 2px solid #4F46E5; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .cuota-info-box {
        background: linear-gradient(145deg, #2d1b1b, #450000);
        padding: 20px; border-radius: 15px; border: 2px solid #ff4b4b; margin-bottom: 20px;
    }
    .vista-previa-box {
        background: linear-gradient(145deg, #0d1a12, #162b1e);
        padding: 25px; border-radius: 15px; border: 2px solid #25D366; border-left: 10px solid #25D366;
    }
    .stButton>button {
        width: 100% !important; border-radius: 12px !important; height: 3.5em !important; 
        font-weight: bold !important; background-color: #4F46E5 !important; color: white !important;
    }
    .stButton>button:hover { background-color: #25D366 !important; color: black !important; }
    /* Estilo para el botón de eliminar */
    .btn-eliminar > div > button {
        background-color: #ff4b4b !important; color: white !important;
    }
    .btn-eliminar > div > button:hover {
        background-color: #990000 !important; border: 1px solid white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 3. NAVEGACIÓN Y MENÚ
# =================================================================
st.sidebar.title("💎 LESTHY MASTER V88")
st.sidebar.info("📍 Moneda: Pesos Colombianos (COP)")
menu = st.sidebar.radio("MENÚ PRINCIPAL", [
    "✨ BALANCE GENERAL", 
    "⏳ GESTIÓN DE COBROS", 
    "🔥 NUEVO PRÉSTAMO", 
    "🛠️ EDITOR MAESTRO SMART", 
    "💸 CONTROL DE GASTOS", 
    "📁 BASE DE CLIENTES",
    "✅ CLIENTES ESTRELLA ⭐",
    "🚨 LISTA NEGRA (MOROSOS)"
])

# -----------------------------------------------------------------
# MÓDULO: BALANCE GENERAL
# -----------------------------------------------------------------
if menu == "✨ BALANCE GENERAL":
    st.header("✨ Balance Financiero (COP)")
    df_p = pd.read_sql_query("SELECT * FROM registros", conn)
    df_g = pd.read_sql_query("SELECT SUM(monto) as total FROM gastos", conn)
    g_tot = df_g['total'][0] if df_g['total'][0] else 0

    if not df_p.empty:
        total_p = df_p['monto_base'].sum()
        total_r = df_p['total_pagar'].sum()
        df_p['rec'] = (df_p['total_pagar'] / df_p['cuotas_totales']) * df_p['cuotas_pagadas']
        dinero_recuperado = df_p['rec'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💰 EN LA CALLE", f"$ { (total_r - dinero_recuperado):,.0f}")
        c2.metric("🏠 RECUPERADO", f"$ {dinero_recuperado:,.0f}")
        c3.metric("📈 UTILIDAD NETA", f"$ { (total_r - total_p - g_tot):,.0f}")
        c4.metric("💸 GASTOS", f"$ {g_tot:,.0f}")
        st.bar_chart(df_p.set_index('nombre')[['monto_base', 'total_pagar']])
    else:
        st.warning("No hay registros activos.")

# -----------------------------------------------------------------
# MÓDULO: GESTIÓN DE COBROS
# -----------------------------------------------------------------
elif menu == "⏳ GESTIÓN DE COBROS":
    st.header("⏳ Gestión de Cobros")
    busqueda = st.text_input("🔍 Buscar cliente...")
    df_cob = pd.read_sql_query("SELECT * FROM registros WHERE cuotas_pagadas < cuotas_totales", conn)
    
    if busqueda:
        df_cob = df_cob[df_cob['nombre'].str.contains(busqueda, case=False)]
    
    for _, r in df_cob.iterrows():
        v_cuota = r['total_pagar'] / r['cuotas_totales']
        debe_act = r['cuotas_totales'] - r['cuotas_pagadas']
        
        with st.expander(f"👤 {r['nombre']} | 💰 PRESTADO: ${r['monto_base']:,.0f} | 📅 Debe: {debe_act}"):
            st.markdown(f"""<div class="cuota-info-box">
                <b>📍 DIRECCIÓN:</b> {r['direccion']}, {r['ciudad']}<br>
                <b>📉 CAPITAL:</b> ${r['monto_base']:,.0f} COP<br>
                <b>🔢 CUOTAS TOTALES:</b> {r['cuotas_totales']} | <b>💵 CUOTA:</b> ${v_cuota:,.0f}
            </div>""", unsafe_allow_html=True)
            
            c1, c2 = st.columns([1, 2])
            with c1:
                if r['foto']: st.image(r['foto'], width=250)
            with c2:
                n_abono = st.number_input(f"Abonar cuotas ({r['nombre']})", 1, key=f"ab_{r['id']}")
                if st.button(f"REGISTRAR PAGO ✅", key=f"btn_{r['id']}"):
                    conn.cursor().execute("UPDATE registros SET cuotas_pagadas=? WHERE id=?", (r['cuotas_pagadas'] + n_abono, r['id']))
                    conn.commit(); st.rerun()

            msg = (f"✅ *RECIBO DE PAGO*\n*Cliente:* {r['nombre']}\n*Monto Prestado:* ${r['monto_base']:,.0f} COP\n"
                   f"*Abono:* {n_abono} cuota(s)\n*Saldo Restante:* ${( (debe_act - n_abono) * v_cuota ):,.0f} COP")
            st.link_button("📲 WHATSAPP", f"https://wa.me/{r['telefono_cliente']}?text={urllib.parse.quote(msg)}")

# -----------------------------------------------------------------
# MÓDULO: NUEVO PRÉSTAMO (INTERÉS MENSUAL COP)
# -----------------------------------------------------------------
elif menu == "🔥 NUEVO PRÉSTAMO":
    st.header("🔥 Registro de Nuevo Crédito (COP)")
    c1, c2 = st.columns(2)
    with c1:
        n_nom = st.text_input("Nombre"); n_ced = st.text_input("Cédula")
        n_tel = st.text_input("WhatsApp"); n_ciu = st.text_input("Ciudad")
        n_dir = st.text_input("Dirección"); n_mod = st.selectbox("📅 Modalidad", ["Diario", "Semanal", "Quincenal", "Mensual"])
        n_fec = st.date_input("🗓️ Fecha Inicio", datetime.now())
    with c2: n_fot = st.camera_input("📸 Foto del Cliente")
    
    st.markdown("---")
    f1, f2, f3, f4 = st.columns(4)
    n_cap = f1.number_input("Monto Prestado (COP)", min_value=0, step=100000)
    n_int = f2.number_input("Interés Mensual (%)", value=10.0)
    n_mes = f3.number_input("Plazo (Meses)", min_value=1, value=1)
    n_cuo = f4.number_input("Cuotas Pactadas", min_value=1, value=20)
    
    if n_cap > 0:
        total_int = (n_cap * (n_int/100)) * n_mes
        total_pagar = n_cap + total_int
        v_cuota = total_pagar / n_cuo
        
        st.markdown(f"""<div class="vista-previa-box">
            <b>💰 CAPITAL:</b> ${n_cap:,.0f} COP<br>
            <b>📅 PLAZO:</b> {n_mes} Mes(es) | <b>📈 INTERÉS:</b> {n_int}% mensual<br>
            <hr>
            <b>🔥 TOTAL A RECOGER:</b> ${total_pagar:,.0f} COP<br>
            <b>💵 CUOTA:</b> ${v_cuota:,.0f} COP
        </div>""", unsafe_allow_html=True)
        
        if st.button("🚀 ACTIVAR CRÉDITO"):
            img_bytes = n_fot.getvalue() if n_fot else None
            conn.cursor().execute("""INSERT INTO registros 
                (nombre, telefono_cliente, monto_base, interes_p, meses_plazo, total_pagar, 
                cuotas_totales, cuotas_pagadas, modalidad, proxima_fecha, reputacion, cedula, ciudad, direccion, foto) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
                (n_nom, n_tel, n_cap, n_int, n_mes, total_pagar, n_cuo, 0, n_mod, 
                 n_fec.strftime('%Y-%m-%d'), "Buen Cliente", n_ced, n_ciu, n_dir, img_bytes))
            conn.commit(); st.balloons(); st.success("¡Préstamo registrado!")

# -----------------------------------------------------------------
# MÓDULO: EDITOR MAESTRO (INCLUYE BOTÓN DE ELIMINAR)
# -----------------------------------------------------------------
elif menu == "🛠️ EDITOR MAESTRO SMART":
    st.header("🛠️ Editor Maestro y Eliminación")
    df_ed = pd.read_sql_query("SELECT id, nombre, monto_base, reputacion FROM registros", conn)
    st.dataframe(df_ed)
    id_s = st.number_input("ID del cliente a gestionar:", min_value=1)
    
    if id_s in df_ed['id'].values:
        cli = pd.read_sql_query(f"SELECT * FROM registros WHERE id={id_s}", conn).iloc[0]
        
        # FORMULARIO DE EDICIÓN
        with st.form("edit_form"):
            st.subheader(f"📝 Editando a: {cli['nombre']}")
            e1, e2 = st.columns(2)
            u_nom = e1.text_input("Nombre", cli['nombre'])
            u_rep = e2.selectbox("Estado", ["Buen Cliente", "Moroso", "Lista Negra"], 
                                index=["Buen Cliente", "Moroso", "Lista Negra"].index(cli['reputacion']))
            u_cap = e1.number_input("Monto Prestado", value=float(cli['monto_base']))
            u_int = e2.number_input("Interés Mensual %", value=float(cli['interes_p']))
            u_pactadas = e1.number_input("Cuotas Pactadas", value=int(cli['cuotas_totales']))
            u_debe = e2.number_input("Cuotas que DEBE HOY", value=int(cli['cuotas_totales'] - cli['cuotas_pagadas']))
            u_mes = e1.number_input("Meses Plazo", value=int(cli['meses_plazo']))
            u_dir = e2.text_input("Dirección", cli['direccion'])
            
            if st.form_submit_button("💾 GUARDAR CAMBIOS"):
                n_pagadas = u_pactadas - u_debe
                n_total = u_cap + (u_cap * (u_int/100) * u_mes)
                conn.cursor().execute("""UPDATE registros SET 
                    nombre=?, reputacion=?, monto_base=?, interes_p=?, meses_plazo=?, 
                    total_pagar=?, cuotas_pagadas=?, cuotas_totales=?, direccion=? WHERE id=?""", 
                    (u_nom, u_rep, u_cap, u_int, u_mes, n_total, n_pagadas, u_pactadas, u_dir, id_s))
                conn.commit(); st.success("¡Registro Actualizado!"); st.rerun()
        
        st.markdown("---")
        # SECCIÓN DE ELIMINACIÓN
        st.subheader("🚨 Zona de Peligro")
        st.warning(f"¿Estás seguro de que deseas eliminar el préstamo de **{cli['nombre']}**? Esta acción no se puede deshacer.")
        
        col_del = st.columns([1, 4])
        with col_del[0]:
            st.markdown('<div class="btn-eliminar">', unsafe_allow_html=True)
            if st.button(f"BORRAR PRÉSTAMO #{id_s}"):
                conn.cursor().execute("DELETE FROM registros WHERE id=?", (id_s,))
                conn.commit()
                st.error(f"Préstamo de {cli['nombre']} eliminado correctamente.")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------
# OTROS MÓDULOS (GASTOS, MOROSOS, BASE)
# -----------------------------------------------------------------
elif menu == "💸 CONTROL DE GASTOS":
    st.header("💸 Gastos Operativos")
    g_d = st.text_input("Descripción"); g_m = st.number_input("Monto COP", min_value=0)
    if st.button("Guardar Gasto"):
        conn.cursor().execute("INSERT INTO gastos (descripcion, monto, fecha) VALUES (?,?,?)", (g_d, g_m, datetime.now().strftime('%Y-%m-%d')))
        conn.commit(); st.success("Gasto guardado.")

elif menu == "🚨 LISTA NEGRA (MOROSOS)":
    st.header("🚨 Lista Negra")
    st.table(pd.read_sql_query("SELECT nombre, ciudad, direccion, reputacion FROM registros WHERE reputacion != 'Buen Cliente'", conn))

elif menu == "✅ CLIENTES ESTRELLA ⭐":
    st.header("✅ Clientes VIP")
    st.table(pd.read_sql_query("SELECT nombre, ciudad, reputacion FROM registros WHERE reputacion = 'Buen Cliente'", conn))

elif menu == "📁 BASE DE CLIENTES":
    st.header("📁 Base de Datos Maestra")
    st.dataframe(pd.read_sql_query("SELECT id, nombre, cedula, telefono_cliente, ciudad, direccion FROM registros", conn))

