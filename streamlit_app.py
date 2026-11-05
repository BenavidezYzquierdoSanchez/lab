"""FraudCloud · Dashboard de resultados AWS Athena y documentación del pipeline.

Entrada única pensada para GitHub + Streamlit Community Cloud.
Carga CSV ya exportados: no necesita acceso AWS, claves, bases en línea ni BD.
"""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from fraudcloud.data import (DATASETS, ROOT, SOURCES, as_view,
                             download_csv, load_tables, validate_tables)

st.set_page_config(
    page_title="FraudCloud | Inteligencia de transacciones",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETTES = {
    "Azul AWS": ("#155EEF", "#153B73", "#8FB5FF"),
    "Violeta": ("#8053D5", "#422B85", "#CAB7FA"),
    "Verde": ("#15967D", "#08705E", "#A2E4D5"),
}
DIMENSIONS = {
    "Noche frente a día": ("03", "es_noche", {"0": "No nocturna", "1": "Nocturna"},
                             "La tasa nocturna es mayor en este conjunto. Es asociación descriptiva, no causalidad."),
    "Categoría de riesgo": ("04", "high_risk_cat", {"0": "No marcada", "1": "Marcada"},
                             "La bandera no permite identificar la categoría comercial exacta."),
    "Monto winsorizado": ("02", "rango_monto", None,
                            "Montos recortados estadísticamente; moneda y pérdidas reales no verificadas."),
    "Grupo de edad": ("05", "edad_grupo", None,
                        "La tasa por grupo aporta comparación ajustada por el número de operaciones."),
    "Mes disponible": ("06", "mes", None,
                         "Agrupación por número de mes. No hay año ni una serie temporal completa."),
    "Fin de semana": ("07", "es_fin_de_semana", {"0": "Laborable", "1": "Fin de semana"},
                       "Las pequeñas diferencias no demuestran un efecto causal."),
    "Distancia comercio-cliente": ("08", "rango_distancia", None,
                                   "La variable de distancia se presenta por intervalos preprocesados."),
}
EVIDENCE = [
    ("01_cloudformation_create_complete.png", "CloudFormation", "La pila del proyecto se creó con CREATE_COMPLETE."),
    ("02_s3_csv_upload.png", "S3 · datos RAW", "Subida del CSV original a S3."),
    ("03_s3_parquet_curated.png", "S3 · datos curados", "Archivos Parquet posteriores al proceso ETL."),
    ("04_glue_job_console.png", "AWS Glue Job", "Trabajo de procesamiento registrado en Glue."),
    ("05_glue_etl_succeeded.png", "Ejecución ETL", "El trabajo Glue finalizó con estado SUCCEEDED."),
    ("06_glue_crawler_ready.png", "Glue Crawler", "Catálogo preparado mediante el crawler."),
    ("07_athena_resumen.png", "Athena · KPI global", "Consulta SQL con totales y tasa de fraude."),
    ("08_athena_noche.png", "Athena · noche", "Consulta agrupada por es_noche."),
    ("09_athena_riesgo.png", "Athena · riesgo", "Consulta agrupada por high_risk_cat."),
    ("10_dashboard_athena.png", "Dashboard Streamlit", "Captura actualizada del dashboard con resultados de Athena."),
    ("11_budgets.png", "AWS Budgets", "Límite presupuestario configurado (no es un tope técnico de gasto)."),
    ("12_cost_explorer.png", "Cost Explorer", "Vista de costos y proyecciones en AWS."),
    ("13_factura_resumen.png", "Factura estimada", "Imagen informativa, no prueba de costo cero permanente."),
    ("14_factura_servicios.png", "Facturación por servicio", "Desglose que puede contener créditos o periodos no cerrados."),
]


def css_theme(primary: str, dark: str, pale: str) -> None:
    st.markdown(f"""
    <style>
    .block-container {{max-width: 1560px; padding-top: 1.1rem; padding-bottom: 3rem}}
    h1 {{font-size: 2.25rem; letter-spacing: -.065rem; color: #14223b; font-weight: 800}}
    h2, h3 {{letter-spacing: -.025rem; color: #152C49}}
    .fc-subtitle {{color: #64758c; font-size: .98rem; margin: -.8rem 0 1.4rem}}
    .fc-badge {{display:inline-block; font-size:.76rem; font-weight:700; border:1px solid {pale};
       border-radius:40px; padding: 5px 12px; color:{dark}; background:#EFF5FF; margin-right:7px}}
    div[data-testid="stMetric"] {{background:linear-gradient(125deg,#F4F8FF, #FFFFFF 80%);
       border:1px solid #dae5f3; border-radius:18px; padding: 16px; min-height: 120px}}
    [data-testid="stMetricValue"] {{color:{dark}; font-weight:700; font-size:2rem}}
    div[data-testid="stExpander"] {{border:1px solid #dae4f1;border-radius:12px}}
    div[data-testid="stVerticalBlockBorderWrapper"] {{border-radius:15px}}
    .fc-card {{border:1px solid #dfe7f2; background:#fff; padding:20px;
      border-radius:17px; box-shadow:0 4px 14px rgba(15,41,83,.035); margin-bottom:12px}}
    .fc-card .fc-eyebrow {{font-size:.76rem; letter-spacing:.08em; font-weight:800; color:{primary};text-transform:uppercase}}
    .fc-card h3 {{margin:6px 0 8px;font-size:1.14rem}}
    .fc-card p {{color:#53647A;font-size:.92rem;line-height:1.55; margin-bottom:0}}
    .fc-section {{border-left:4px solid {primary};padding:12px 16px;background:#F1F6FE;
       border-radius:4px 12px 12px 4px; margin:12px 0 22px}}
    </style>""", unsafe_allow_html=True)


def card(kicker: str, title: str, text: str) -> None:
    safe = [html.escape(str(v)) for v in (kicker, title, text)]
    st.markdown(
        f'<div class="fc-card"><div class="fc-eyebrow">{safe[0]}</div>'
        f'<h3>{safe[1]}</h3><p>{safe[2]}</p></div>', unsafe_allow_html=True)


def plot_dimension(df: pd.DataFrame, column: str, metric: str, primary: str,
                   pale: str, kind: str = "bar") -> None:
    plot = df.copy()
    label = "Tasa de fraude (%)" if metric == "tasa_fraude_pct" else "Fraudes identificados"
    if kind == "line":
        plot[column] = pd.to_numeric(plot[column], errors="coerce")
        plot = plot.sort_values(column)
        fig = px.line(plot, x=column, y=metric, markers=True, text=metric,
                      labels={column: "Mes (1–12; sin año)", metric: label})
        fig.update_traces(line_color=primary, marker_size=9, textposition="top center")
    else:
        fig = px.bar(plot, x=column, y=metric, text=metric,
                     color=metric, color_continuous_scale=[pale, primary],
                     labels={column: "Grupo", metric: label})
        fig.update_traces(texttemplate="%{text:.3f}" if metric == "tasa_fraude_pct" else "%{text:.0f}",
                          textposition="outside")
        fig.update_layout(coloraxis_showscale=False)
    fig.update_layout(height=350, margin=dict(t=35, b=25, l=10, r=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Arial, sans-serif", size=12, color="#39516F"),
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#E5EDF7"),
                      hovermode="x unified")
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def data_info(tables: dict[str, pd.DataFrame]) -> tuple[int, int, int, float]:
    k = tables["01"].iloc[0]
    return (int(k.total_transacciones), int(k.transacciones_fraude),
            int(k.transacciones_legitimas), float(k.tasa_fraude_pct))


def page_home(tables: dict[str, pd.DataFrame], primary: str, pale: str) -> None:
    total, frauds, legit, rate = data_info(tables)
    cols = st.columns(4, gap="medium")
    cols[0].metric("Transacciones analizadas", f"{total:,}".replace(",", " "))
    cols[1].metric("Fraudes detectados", f"{frauds:,}".replace(",", " "))
    cols[2].metric("Tasa de fraude", f"{rate:.4f} %")
    cols[3].metric("Operaciones legítimas", f"{legit:,}".replace(",", " "))
    st.caption("Los fraudes son etiquetas del conjunto de datos; no son predicciones generadas por este dashboard.")
    st.markdown("### Comparación de indicadores")
    metric_name = st.radio("Visualizar", ["Tasa de fraude (%)", "Cantidad de fraudes"],
                           horizontal=True, key="home_metric")
    metric = "tasa_fraude_pct" if metric_name.startswith("Tasa") else "fraudes"
    left, right = st.columns(2, gap="large")
    for container, heading in [(left, "Noche frente a día"), (right, "Categoría de riesgo")]:
        code, field, labels, note = DIMENSIONS[heading]
        with container:
            st.markdown(f"#### {heading}")
            v = as_view(tables[code], field, labels)
            plot_dimension(v, field, metric, primary, pale)
            st.caption(note)
    st.markdown("### Qué indican los resultados")
    a, b, c = st.columns(3, gap="medium")
    with a:
        card("Hallazgo", "Patrón nocturno",
             "La tasa del segmento nocturno supera a la no nocturna. No demuestra causalidad.")
    with b:
        card("Hallazgo", "Categoría marcada",
             "La bandera high_risk_cat señala una diferencia de tasas en la muestra.")
    with c:
        card("Limitación", "Datos preprocesados",
             "El monto está winsorizado. No corresponde estimar pérdidas monetarias.")
    st.markdown("<div class='fc-section'><strong>Alcance:</strong> sistema analítico batch "
                "sobre datos preparados, no motor de autorización bancaria ni detector en tiempo real.</div>",
                unsafe_allow_html=True)


def page_analysis(tables: dict[str, pd.DataFrame], primary: str, pale: str) -> None:
    st.markdown("## Explorador interactivo de resultados")
    st.caption("Cada vista es una agregación independiente de Athena. Cambiar la dimensión no filtra otras vistas.")
    left, right = st.columns([2, 1])
    with left:
        choice = st.selectbox("Dimensión de análisis", list(DIMENSIONS), key="analysis_dimension")
    with right:
        label = st.selectbox("Indicador", ["Tasa de fraude (%)", "Cantidad de fraudes", "Transacciones"],
                             key="analysis_metric")
    metric = {"Tasa de fraude (%)": "tasa_fraude_pct", "Cantidad de fraudes": "fraudes",
              "Transacciones": "transacciones"}[label]
    code, field, labels, note = DIMENSIONS[choice]
    data = as_view(tables[code], field, labels)
    st.markdown(f"### {choice}")
    plot_dimension(data, field, metric, primary, pale, "line" if code == "06" else "bar")
    st.info(note, icon="ℹ️")
    st.dataframe(data, width="stretch", hide_index=True)
    st.download_button("⬇️ Descargar esta tabla CSV", data=download_csv(data),
                       file_name=f"fraudcloud_{code}_resultado.csv", mime="text/csv")
    st.divider()
    st.markdown("### Otras comparaciones")
    a, b = st.columns(2, gap="large")
    for box, name in [(a, "Monto winsorizado"), (b, "Grupo de edad")]:
        k, d, labels, note = DIMENSIONS[name]
        with box:
            st.markdown(f"#### {name}")
            plot_dimension(as_view(tables[k], d, labels), d, "tasa_fraude_pct", primary, pale)
            st.caption(note)


def page_data(tables: dict[str, pd.DataFrame]) -> None:
    st.markdown("## Auditoría de datos y resultados")
    errors = validate_tables(tables)
    if errors:
        st.error("Se detectaron inconsistencias: " + "; ".join(errors))
    else:
        st.success("Las 8 agregaciones tienen totales y tasas compatibles entre sí.")
    k = tables["01"].iloc[0]
    st.markdown("### Comprobación global")
    a, b, c = st.columns(3)
    a.metric("Filas procesadas", f"{int(k.total_transacciones):,}".replace(",", " "))
    b.metric("Etiquetas positivas", f"{int(k.transacciones_fraude):,}".replace(",", " "))
    c.metric("Prevalencia positiva", f"{float(k.tasa_fraude_pct):.4f} %")
    st.markdown("### Ocho consultas SQL disponibles")
    for code, (title, filename) in DATASETS.items():
        with st.expander(f"{code} · {title} — {filename}", expanded=(code == "01")):
            st.dataframe(tables[code], width="stretch", hide_index=True)
            sql = ROOT / "sql" / filename.replace(".csv", ".sql")
            if sql.exists():
                st.code(sql.read_text(encoding="utf-8"), language="sql")
            st.download_button("Descargar CSV", download_csv(tables[code]), file_name=filename,
                               mime="text/csv", key=f"download_{code}")
    st.warning("**Interpretación:** la fuente incluye transacciones procesadas; "
               "no se conoce moneda real, timestamp completo, año, ni procedencia verificada del dataset original. "
               "No sustituye un modelo predictivo ni un análisis de causalidad.")


def page_pipeline() -> None:
    st.markdown("## Arquitectura y ejecución en AWS")
    architecture = ROOT / "assets" / "diagramas" / "arquitectura.png"
    if architecture.exists():
        st.image(str(architecture), caption="Arquitectura declarada del proyecto FraudCloud", width="stretch")
    st.markdown("### Pipeline de datos")
    a, b, c = st.columns(3, gap="large")
    with a:
        card("1 · Ingesta", "S3 / RAW", "CSV procesado subido a raw/transactions/ en un bucket privado S3.")
        card("4 · Catálogo", "Glue Crawler", "La tabla fraud_transactions se registra en Glue Data Catalog.")
    with b:
        card("2 · Transformación", "AWS Glue ETL", "Trabajo batch que transforma el archivo de entrada en Parquet.")
        card("5 · Consultas", "Amazon Athena", "Ocho SQL agregan KPIs y comparaciones sin mover los datos al navegador.")
    with c:
        card("3 · Almacenamiento", "S3 / CURATED", "Particiones con archivos Parquet para análisis posterior.")
        card("6 · Visualización", "Streamlit", "Este portal lee los 8 CSV exportados. No consulta AWS en vivo.")
    st.markdown("### Infraestructura como código")
    with st.expander("Plantilla CloudFormation / infra/main.yaml"):
        st.code((ROOT / "infra" / "main.yaml").read_text(encoding="utf-8"), language="yaml")
    with st.expander("Trabajo AWS Glue / glue/glue_etl.py"):
        st.code((ROOT / "glue" / "glue_etl.py").read_text(encoding="utf-8"), language="python")
    st.caption("IAM Identity Center/MFA se configuraron en el entorno académico. "
               "El despliegue de Community Cloud es únicamente de la aplicación de visualización.")


def page_evidence() -> None:
    st.markdown("## Galería de evidencias del proyecto")
    st.caption("Capturas históricas seleccionadas del proyecto AWS (noviembre de 2026), "
               "no constituyen verificación actual de recursos encendidos.")
    titles = [t for _f, t, _c in EVIDENCE]
    selected = st.multiselect("Filtrar evidencias", titles, default=titles,
                              placeholder="Seleccionar evidencias")
    results = [e for e in EVIDENCE if e[1] in selected]
    if not results:
        st.info("Selecciona al menos una evidencia.")
        return
    for pos in range(0, len(results), 2):
        cols = st.columns(2, gap="large")
        for col, evidence in zip(cols, results[pos:pos + 2]):
            filename, name, explanation = evidence
            with col:
                st.markdown(f"#### {name}")
                image_path = ROOT / "assets" / "evidencias" / filename
                if image_path.exists():
                    st.image(str(image_path), width="stretch")
                st.caption(explanation)
    st.warning("Antes de publicar capturas en un repositorio público, revisa IDs de cuenta, "
               "datos personales y cualquier información sensible. Nunca publiques QR de MFA ni tokens.")


def page_project() -> None:
    st.markdown("## Código, dependencias y estructura del proyecto")
    c1, c2, c3 = st.columns(3)
    with c1:
        card("Aplicación", "streamlit_app.py", "Entrada del despliegue en Community Cloud. Incluye navegación, gráficos y resultados.")
    with c2:
        card("Dependencias", "requirements.txt", "Streamlit, pandas y Plotly. Para scripts AWS existe requirements-aws.txt.")
    with c3:
        card("Datos", "data/athena_results", "Ocho CSV de consultas Athena ya exportados para operar sin credenciales AWS.")
    structure = """FraudCloud_Streamlit_GitHub_Deploy/
├── streamlit_app.py             # Entrada principal de Community Cloud
├── fraudcloud/data.py          # Carga, transformaciones y controles
├── requirements.txt            # Librerías usadas por Streamlit
├── requirements-aws.txt        # Dependencia opcional boto3 para scripts
├── .streamlit/config.toml      # Tema visual
├── data/
│   ├── athena_results/         # 8 resultados exportados de AWS
│   └── local_preview/          # 8 agregados calculados localmente
├── assets/evidencias/          # Capturas del proyecto
├── assets/diagramas/           # Diagrama y gráficos
├── presentacion/               # Presentación HTML independiente
├── docs/                       # Informe final PDF
├── sql/                        # 8 consultas SQL
├── glue/                       # Código Glue ETL
├── infra/                      # CloudFormation main.yaml
├── scripts/                    # Carga/sincronización opcional
├── tests/                      # Pruebas de consistencia
└── .github/workflows/tests.yml # Validación con cada push"""
    st.code(structure, language="text")
    st.markdown("### Cómo ejecutarlo")
    st.code("python -m pip install -r requirements.txt\npython -m streamlit run streamlit_app.py", "bash")
    st.markdown("### Guía de despliegue")
    st.markdown("Sube **el contenido de esta carpeta** a la raíz de un repositorio GitHub. "
                "Abre [share.streamlit.io](https://share.streamlit.io), selecciona repositorio, "
                "rama `main` y archivo principal `streamlit_app.py`. Pulsa **Deploy**.")
    st.info("No se necesitan variables de entorno ni AWS Secrets para mostrar los CSV incluidos.")
    pdf_file = ROOT / "docs" / "Informe_Final_FraudCloud_2026.pdf"
    if pdf_file.exists():
        st.download_button("📄 Descargar informe final en PDF", pdf_file.read_bytes(),
                           file_name="Informe_Final_FraudCloud_2026.pdf", mime="application/pdf")
    st.markdown("### Limitaciones técnicas y recomendaciones")
    st.markdown("El despliegue **no actualiza Athena automáticamente**. Para incorporar nuevos resultados, "
                "ejecutar `scripts/actualizar_athena.py` en un equipo autorizado y subir los CSV actualizados. "
                "No añadir el dataset transaccional completo ni credenciales al repositorio público.")


def page_presentation() -> None:
    st.markdown("## Presentación HTML del proyecto")
    st.caption("Incluye el pipeline, evidencias, comparativas, código y la pestaña de app de tarjetas. "
               "La presentación es estática e independiente de la ejecución de Streamlit.")
    src = ROOT / "presentacion" / "FraudCloud_Presentacion.html"
    if not src.exists():
        st.warning("No se incluyó la presentación HTML.")
        return
    raw = src.read_bytes()
    st.download_button("⬇️ Descargar presentación HTML para abrir en pantalla completa",
                       data=raw, file_name="FraudCloud_Presentacion.html", mime="text/html")
    if st.toggle("Mostrar presentación dentro de Streamlit", value=False):
        components.html(raw.decode("utf-8", errors="replace"), height=780, scrolling=True)
    st.info("Para usar pantalla completa real, descarga el HTML, ábrelo en el navegador y "
            "utiliza su botón de pantalla completa o la tecla F11.")


# -- Aplicación --
with st.sidebar:
    st.markdown("### 💳 FRAUDCLOUD")
    st.caption("Big Data · AWS · Análisis de fraude")
    st.divider()
    page = st.radio("MENÚ", ["📊 Resumen", "📈 Análisis interactivo", "🧾 Datos y SQL",
                            "☁️ Pipeline y arquitectura", "🖼️ Evidencias",
                            "🧩 Proyecto y despliegue", "🖥️ Presentación HTML"],
                    label_visibility="collapsed")
    st.divider()
    source = st.selectbox("Origen de resultados", list(SOURCES), index=0)
    theme = st.selectbox("Color del dashboard", list(PALETTES), index=0)
    st.caption("🌐 Publicable en Streamlit Community Cloud")
    st.caption("📆 Resultados del proyecto: 04/11/2026")
    st.caption("📌 Datos batch exportados; no actualización en vivo")

primary, dark, pale = PALETTES[theme]
css_theme(primary, dark, pale)
st.title("💳 FraudCloud · Inteligencia de transacciones")
st.markdown('<p class="fc-subtitle">Big Data y Cloud Computing  ·  Amazon S3 → Glue ETL → Data Catalog → Athena → Streamlit</p>',
            unsafe_allow_html=True)
st.markdown(f'<span class="fc-badge">{html.escape(source)}</span>'
            '<span class="fc-badge">AWS us-east-1</span>'
            '<span class="fc-badge">8 vistas agregadas</span>', unsafe_allow_html=True)
st.write("")

try:
    tables = load_tables(source)
except (FileNotFoundError, ValueError, pd.errors.ParserError) as ex:
    st.error(f"Error cargando las exportaciones CSV: {ex}")
    st.stop()

errors = validate_tables(tables)
if errors:
    st.warning("Controles de consistencia: " + "; ".join(errors))

if source.startswith("Previsualización"):
    st.warning("Modo LOCAL: estos agregados no son salidas de AWS Athena.")
else:
    st.success("Modo AWS histórico: resultados CSV exportados de consultas Athena. No existe conexión en vivo a AWS.")

if page == "📊 Resumen":
    page_home(tables, primary, pale)
elif page == "📈 Análisis interactivo":
    page_analysis(tables, primary, pale)
elif page == "🧾 Datos y SQL":
    page_data(tables)
elif page == "☁️ Pipeline y arquitectura":
    page_pipeline()
elif page == "🖼️ Evidencias":
    page_evidence()
elif page == "🧩 Proyecto y despliegue":
    page_project()
elif page == "🖥️ Presentación HTML":
    page_presentation()

st.divider()
st.caption("FraudCloud 2026 · Proyecto académico · El dashboard muestra agregados históricos y no procesa tarjetas reales en tiempo real.")
