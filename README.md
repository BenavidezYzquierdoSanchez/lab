# FraudCloud 2026 · Streamlit listo para GitHub

Dashboard académico de **339 607 transacciones**, **1 782 fraudes**, **337 825 operaciones legítimas** y **0,5247 %** de tasa de fraude. Está basado en ocho archivos CSV exportados de **Amazon Athena**, producidos por el proyecto AWS con **S3 → Glue ETL (Parquet) → Data Catalog → Athena**.

## 1. Subir a GitHub

1. Descomprimir este ZIP.
2. Ir a [github.com/new](https://github.com/new) y crear un repositorio, por ejemplo `fraudcloud-streamlit`. Puede ser público tras revisar las evidencias y eliminar identificadores personales.
3. En el repositorio, elegir **Add file → Upload files**.
4. Subir **el contenido interior de `FraudCloud_Streamlit_GitHub_Deploy/`**, con `streamlit_app.py` y `requirements.txt` en la raíz del repositorio. Deben estar las carpetas ocultas `.streamlit/` y `.github/` (usando Git suele ser más sencillo).
5. Confirmar los cambios con **Commit changes**.

### Alternativa con PowerShell / VS Code

Ejecutar estos comandos desde la carpeta descomprimida:

```powershell
cd "RUTA\FraudCloud_Streamlit_GitHub_Deploy"
git init
git add .
git commit -m "Publicar FraudCloud Streamlit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/fraudcloud-streamlit.git
git push -u origin main
```

Cambia `TU_USUARIO` por tu usuario; el repositorio de GitHub debe existir primero. Si ya tiene un commit inicial (README automático), clónalo primero o resuelve el historial antes del push.

## 2. Desplegar en Streamlit Community Cloud

1. Abrir [share.streamlit.io](https://share.streamlit.io) e iniciar sesión con GitHub.
2. Seleccionar **Create app** → **Yup, I have an app**.
3. Repositorio: `TU_USUARIO/fraudcloud-streamlit`.
4. Rama: **`main`**.
5. Archivo principal (**Main file path**): **`streamlit_app.py`**.
6. En *Advanced settings*, seleccionar Python **3.12** para reproducibilidad. **No se requieren secretos.**
7. Hacer clic en **Deploy**. Al finalizar podrás compartir el enlace `https://...streamlit.app` de tu aplicación.

**Importante:** publicar en Streamlit Community Cloud no despliega AWS Glue, Athena ni CloudFormation; solo publica el dashboard usando resultados históricos exportados.

## 3. Ejecutar en tu computadora

Se recomienda Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

En Linux o macOS se activa con `source .venv/bin/activate`.

## Contenido de las pestañas

- **Resumen**: cuatro indicadores, comparaciones noche/riesgo, análisis descriptivo.
- **Análisis interactivo**: siete dimensiones, selección de tasa/conteo y exportación CSV.
- **Datos y SQL**: controles de calidad, ocho consultas y tablas originales exportadas.
- **Pipeline y arquitectura**: diagrama, fases, plantilla CloudFormation y código Glue.
- **Evidencias**: 17 capturas seleccionadas; filtros por etapa, resultados, costos y seguridad.
- **Seguridad MFA**: imágenes protegidas de la configuración y del registro exitoso de un MFA virtual.
- **Costos y créditos**: facturación histórica, AWS Budgets, Cost Explorer y correo del 29/10/2026 con USD 69 disponibles **en esa fecha**, no saldo actual.
- **Proyecto y despliegue**: carpetas, dependencias, guía, informe PDF.
- **Presentación HTML**: HTML autónomo actualizado con las 17 evidencias, la pestaña de app de tarjetas y botón de pantalla completa; visualización integrada opcional.

## 4. Estructura técnica

```text
streamlit_app.py             # App principal
fraudcloud/data.py          # Funciones de carga y validación
requirements.txt            # Solo dependencias necesarias en Community Cloud
requirements-aws.txt        # Dependencias opcionales de los scripts AWS
.streamlit/config.toml      # Apariencia visual
data/athena_results/         # 8 CSV exportados de Athena
data/local_preview/          # 8 CSV locales, correctamente etiquetados
assets/evidencias/          # Capturas de pantalla del proyecto
assets/diagramas/           # Arquitectura AWS
presentacion/               # Presentación HTML corregida y autónoma
docs/                       # Informe profesional completo PDF + Word
sql/                        # Consultas Athena
infra/                      # CloudFormation
glue/                       # Script ETL
scripts/                    # Ejecución local, AWS, sincronización manual
tests/                      # Validación de agregados
.github/workflows/          # Pruebas CI para cada commit
```

## 5. Actualizar CSV desde AWS (opcional, fuera de Streamlit Community Cloud)

**Nunca** incluyas claves, tokens SSO, código MFA ni `.streamlit/secrets.toml` en el repositorio público. Si tu cuenta AWS tiene permiso, desde una PC autorizada:

```powershell
python -m pip install -r requirements-aws.txt
aws sso login --profile fraudlab
python scripts/actualizar_athena.py --profile fraudlab --region us-east-1
```

El script usa los ocho SQL y actualiza `data/athena_results/`. Luego haz **git commit** y **git push** para publicar nuevos CSV. Por defecto, las consultas apuntan a la base `fraude_tarjetas_db`, tabla `fraud_transactions`, workgroup `fraude-tarjetas-wg` y bucket de la cuenta documentada. Ajusta los parámetros si cambiaste de infraestructura. **No se ejecuta automáticamente al visitar la app.**

## 6. Seguridad, privacidad y calidad

- El CSV original de 54 MB **no se incluye**, porque la aplicación consume solo agregados y conviene no exponer transacciones individuales públicamente.
- El valor `monto_winsorizado_99` no representa el monto monetario original; **no** se deducen pérdidas financieras ni moneda.
- El dataset no permite reconstruir fechas/años completos ni demostrar causas; la bandera `high_risk_cat` no identifica una categoría de comercio específica.
- Las 8 exportaciones AWS están empaquetadas como un **snapshot**, no son sincronización Athena en vivo.
- Las capturas son históricas; revisa datos personales y números de cuenta antes de publicar el repositorio.
- **No hay modelos de machine learning predictivos**, autorización de pagos ni detección de fraude en línea. Es análisis de datos agregados.
- El dashboard puede permanecer público; los recursos AWS S3, Glue, Athena y presupuestos se administran de manera independiente y pueden generar costos incluso cuando la aplicación esté inactiva.

## 7. Validación local

```powershell
python -m pip install -r requirements.txt pytest
python -m pytest -q tests
```

Si aparece un error de importación de Streamlit en tu PC, instala las dependencias del `requirements.txt` en el Python que usas para correr la app.


### Evidencias MFA (05/11/2026)

La galería contiene las capturas 15 y 16 del alta de un autenticador virtual y del mensaje de AWS que confirma su asignación exitosa. En la versión publicable se **ocultan** QR de enrolamiento, claves, códigos temporales, correo y teléfono de recuperación. El PDF completo actualizado se encuentra en `docs/Informe_FraudCloud_2026_MFA_Validado.pdf`. Estas evidencias no demuestran que MFA sea obligatorio para todos los usuarios.


## Actualización de seguridad y FinOps · 11/11/2026

- Se incorporó **Evidencia 17**, correo AWS Billing del **29/10/2026**. Los **USD 69** son un saldo histórico comunicado entonces, no el saldo actual.
- Se mantienen evidencias **15** y **16** (configuración y alta de MFA virtual) con QR, códigos y detalles de recuperación protegidos.
- Se agregaron páginas nativas de Streamlit **Seguridad MFA** y **Costos y créditos**, con carga local robusta de imágenes (sin URLs relativas ni conexión a AWS).
- La pestaña de presentación incluye el HTML corregido, con las imágenes protegidas incrustadas y acceso a la app didáctica de tarjetas.
- Se sustituyó el informe anterior por el informe profesional más reciente en **PDF y DOCX**.
- La app **no consulta AWS en tiempo real**. La publicación de estas evidencias no valida un saldo vigente ni implica que el MFA esté aplicado a todas las identidades.

**Antes de hacer público el repositorio**, revisa cuidadosamente también las evidencias históricas 1–14 y los documentos. No incluyas claves, tokens, tarjetas reales, números completos de cuenta, correos personales ni datos de recuperación de MFA.
