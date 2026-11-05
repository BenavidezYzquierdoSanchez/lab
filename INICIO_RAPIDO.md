# INICIO RÁPIDO · FRAUDCLOUD 2026

## Quiero publicarlo en internet

**Paso 1.** Descomprime el archivo ZIP.

**Paso 2.** En GitHub, crea un repositorio llamado `fraudcloud-streamlit`.

**Paso 3.** Sube los archivos y carpetas que hay dentro de `FraudCloud_Streamlit_GitHub_Deploy/`, asegurándote de que `streamlit_app.py` y `requirements.txt` queden en la raíz. No subas una carpeta externa por error.

**Paso 4.** Visita https://share.streamlit.io, inicia sesión con GitHub y pulsa **Create app**.

**Paso 5.** Elige tu repositorio; rama `main`; **Main file path: `streamlit_app.py`**; Python 3.12; despliega con **Deploy**.

**Paso 6.** Abre la dirección `https://...streamlit.app` asignada por Streamlit.

### Si aparece `ModuleNotFoundError`

Comprueba que `requirements.txt` esté en la raíz del repositorio y que incluya Streamlit, pandas y Plotly.

### Si aparece `FileNotFoundError`

Confirma que los ocho archivos CSV estén subidos en `data/athena_results/` y que el directorio se llame exactamente así.

### Si Streamlit muestra una página en blanco

Revisa los logs de la aplicación en Streamlit Community Cloud. Prueba localmente con `python -m streamlit run streamlit_app.py`.

### Seguridad

El repositorio no debe incluir el dataset original, claves AWS, datos MFA, archivos `.env` ni secretos. Revisa las capturas antes de hacer público el repositorio.

## Ejecutarlo en Windows (VS Code)

Abre una terminal dentro de la carpeta descomprimida y escribe:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Se abre normalmente en http://localhost:8501.
