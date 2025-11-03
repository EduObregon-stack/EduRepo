# =========================================
# Leads App (Streamlit + SQLite)
# Guardar • Buscar • Exportar
# =========================================
import os, time, sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import date

DB_PATH = os.environ.get("LEADS_DB_PATH", "leads.db")
TABLE   = "leads"

# ------------- DB helpers -------------
def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            tema TEXT, nombre TEXT, apellido TEXT, puesto TEXT,
            tel_trabajo TEXT, tel_movil TEXT, email TEXT,
            compania TEXT, web TEXT,
            calle1 TEXT, calle2 TEXT, calle3 TEXT,
            ciudad TEXT, estado TEXT, pais TEXT,
            notas TEXT, fuente TEXT
        )
    """)
    con.commit(); con.close()

def insert_lead(row: dict):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cols = ("created_at, tema, nombre, apellido, puesto, tel_trabajo, tel_movil, email, "
            "compania, web, calle1, calle2, calle3, ciudad, estado, pais, notas, fuente")
    vals = tuple(row[c] for c in [
        "created_at","tema","nombre","apellido","puesto","tel_trabajo","tel_movil","email",
        "compania","web","calle1","calle2","calle3","ciudad","estado","pais","notas","fuente"
    ])
    cur.execute(f"INSERT INTO {TABLE} ({cols}) VALUES ({','.join(['?']*18)})", vals)
    con.commit(); con.close()

def query_df(text="", fuente="(todas)", f_ini=None, f_fin=None):
    init_db()
    con = sqlite3.connect(DB_PATH)
    where, params = [], []

    if text:
        like = f"%{text.strip()}%"
        cols = ["tema","nombre","apellido","email","compania","tel_trabajo","tel_movil",
                "ciudad","estado","pais","notas","web"]
        where.append("(" + " OR ".join([f"{c} LIKE ?" for c in cols]) + ")")
        params += [like]*len(cols)

    if fuente and fuente != "(todas)":
        where.append("fuente = ?")
        params.append(fuente)

    if f_ini:
        where.append("created_at >= ?")
        params.append(f"{f_ini.strftime('%Y-%m-%d')} 00:00:00")
    if f_fin:
        where.append("created_at <= ?")
        params.append(f"{f_fin.strftime('%Y-%m-%d')} 23:59:59")

    sql = f"SELECT * FROM {TABLE}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"

    df = pd.read_sql_query(sql, con, params=params)
    con.close()
    return df

# ------------- UI -------------
st.set_page_config(page_title="Leads (SQLite)", page_icon="📋", layout="wide")
init_db()

st.markdown("""
<style>
/* afinado visual sutil */
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

st.title("📋 Registro de Leads (SQLite)")
st.caption("Guardar • Buscar • Exportar")

# --- Layout principal: dos columnas (form a la izquierda, resultados a la derecha) ---
col_form, col_res = st.columns([1.05, 1.6], gap="large")

with col_form:
    st.subheader("Alta de lead")
    with st.form("form_lead", clear_on_submit=False):
        # Primera fila
        c1, c2 = st.columns(2)
        tema      = c1.text_input("Tema", placeholder="Miranza - Interés en Fundanet")
        compania  = c2.text_input("Compañía", placeholder="Miranza")

        # Segunda fila
        c1, c2, c3 = st.columns(3)
        nombre     = c1.text_input("Nombre", placeholder="David")
        apellido   = c2.text_input("Apellido", placeholder="Castro Miranza")
        puesto     = c3.text_input("Puesto", placeholder="---")

        # Tercera fila
        c1, c2, c3 = st.columns(3)
        tel_trab   = c1.text_input("Teléfono del trabajo", placeholder="---")
        tel_movil  = c2.text_input("Teléfono móvil", placeholder="691091509")
        email      = c3.text_input("Correo electrónico", placeholder="nombre@empresa.com")

        # Cuarta fila
        c1, c2, c3 = st.columns(3)
        web        = c1.text_input("Sitio web", placeholder="https://miranza.es/")
        estado     = c2.text_input("Estado/Provincia", placeholder="Madrid")
        ciudad     = c3.text_input("Ciudad", placeholder="Madrid")

        # Quinta fila
        c1, c2, c3 = st.columns(3)
        calle1     = c1.text_input("Calle 1")
        calle2     = c2.text_input("Calle 2")
        calle3     = c3.text_input("Calle 3")

        # Sexta fila
        c1, c2 = st.columns(2)
        pais       = c1.text_input("País", placeholder="España")
        fuente     = c2.selectbox("Fuente del lead", ["Web","Evento","Referido","Campaña","Llamada","Email","Otro"], index=0)

        # Notas
        notas      = st.text_area("Notas", placeholder="Detalles, próximos pasos…", height=90)

        submitted = st.form_submit_button("Guardar lead", type="primary", use_container_width=True)
        if submitted:
            row = {
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "tema": tema or "", "nombre": nombre or "", "apellido": apellido or "",
                "puesto": puesto or "", "tel_trabajo": tel_trab or "", "tel_movil": tel_movil or "",
                "email": email or "", "compania": compania or "", "web": web or "",
                "calle1": calle1 or "", "calle2": calle2 or "", "calle3": calle3 or "",
                "ciudad": ciudad or "", "estado": estado or "", "pais": pais or "",
                "notas": notas or "", "fuente": fuente or ""
            }
            insert_lead(row)
            st.success(f"Lead guardado: {row['nombre']} {row['apellido']} — {row['tema']}")

with col_res:
    st.subheader("Búsqueda y resultados")
    # Barra de búsqueda
    s1, s2, s3, s4 = st.columns([1.6, 0.9, 0.7, 0.7])
    search_text   = s1.text_input("Texto (nombre, empresa, email…)", placeholder="Buscar…")
    search_fuente = s2.selectbox("Fuente", ["(todas)","Web","Evento","Referido","Campaña","Llamada","Email","Otro"])
    today = date.today()
    s3.caption("Desde"); f_ini = s3.date_input("", value=None, key="finicio")
    s4.caption("Hasta"); f_fin = s4.date_input("", value=None, key="ffin")

    # Acciones
    b1, b2, b3 = st.columns([0.25, 0.25, 0.5])
    do_search   = b1.button("Buscar", type="primary", use_container_width=True)
    do_reset    = b2.button("Limpiar filtros", use_container_width=True)

    if do_reset:
        search_text = ""
        search_fuente = "(todas)"
        f_ini, f_fin = None, None
        # Reinicia los widgets visualmente (persistencia de estado)
        st.experimental_rerun()

    # Ejecutar búsqueda (en primer render y cuando se pulsa "Buscar")
    if "first_load_done" not in st.session_state:
        st.session_state.first_load_done = True
        df_results = query_df()
    else:
        df_results = query_df(search_text, search_fuente, f_ini, f_fin) if do_search else query_df(search_text, search_fuente, f_ini, f_fin)

    # Métricas y gráfico
    ctop1, ctop2 = st.columns([0.35, 0.65])
    ctop1.metric("Resultados", value=len(df_results))
    with ctop2:
        if not df_results.empty:
            counts = df_results["fuente"].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(6, 2.8))
            counts.plot(kind="bar", ax=ax)
            ax.set_title("Distribución de leads por fuente")
            ax.set_ylabel("Leads"); ax.set_xlabel("")
            ax.grid(axis='y', linestyle='--', alpha=0.35)
            plt.xticks(rotation=0)
            st.pyplot(fig)
        else:
            st.info("No hay datos para graficar con los filtros actuales.")

    # Tabla
    if not df_results.empty:
        vis = df_results.drop(columns=["id"]).rename(columns={
            "created_at":"Fecha/Hora","tema":"Tema","nombre":"Nombre","apellido":"Apellido",
            "puesto":"Puesto","tel_trabajo":"Teléfono del trabajo","tel_movil":"Teléfono móvil",
            "email":"Correo electrónico","compania":"Compañía","web":"Sitio web",
            "calle1":"Calle 1","calle2":"Calle 2","calle3":"Calle 3",
            "ciudad":"Ciudad","estado":"Estado/Provincia","pais":"País",
            "notas":"Notas","fuente":"Fuente del lead"
        })
        st.dataframe(vis, use_container_width=True, hide_index=True)
        # Exportar a CSV (solo resultados actuales)
        csv_bytes = vis.to_csv(index=False).encode("utf-8")
        st.download_button("Exportar resultados a CSV", data=csv_bytes,
                           file_name="leads_export.csv", mime="text/csv", use_container_width=True)
    else:
        st.dataframe(pd.DataFrame(columns=[
            "Fecha/Hora","Tema","Nombre","Apellido","Puesto","Teléfono del trabajo","Teléfono móvil",
            "Correo electrónico","Compañía","Sitio web","Calle 1","Calle 2","Calle 3",
            "Ciudad","Estado/Provincia","País","Notas","Fuente del lead"
        ]), use_container_width=True)
