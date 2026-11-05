# FRAUDCLOUD 2026 — Presentación web HTML/CSS/JavaScript

## Abrir la presentación

Opción más fácil: abrir **FraudCloud_Presentacion_Standalone.html**, que incluye estilos, JavaScript, gráficos, diagramas y 14 capturas de evidencia dentro del mismo archivo. Funciona sin conexión a AWS ni a Internet.

Opción editable: descomprimir este ZIP y abrir `index.html` en Chrome/Edge. Para editar, utilizar VS Code: `index.html`, `styles.css`, `data.js` y `app.js`. NO separar `index.html` de la carpeta `assets/` ni de `documentos/` si se utiliza esta opción.

Para **pantalla completa**, pulsa el botón de la barra superior, junto a «Presentar». También puedes usar `Shift+F` desde la página o `F11` como atajo propio del navegador. Pulsa `Esc` para salir del modo pantalla completa. El botón «Presentar» solamente oculta o muestra la barra lateral.

## Contenido

- 11 pestañas: Inicio ejecutivo, Problema y datos, Arquitectura, Implementación, Resultados reales, App de tarjetas de crédito, Evidencias, Costos, Seguridad y Conclusiones.
- Datos de 339 607 transacciones, 1 782 fraudes, 337 825 legítimas y tasa 0,5247 %.
- 8 archivos CSV exportados de Athena; 3 consultas tienen además capturas directas: KPI global, noche y bandera high_risk_cat.
- 5 consultas adicionales con CSV exportado desde Athena: monto, edad, mes, fin de semana y distancia. No disponen de captura individual de consola en este paquete.
- 14 evidencias reales seleccionadas y diagrama de arquitectura.
- Interacción JavaScript: pestañas, gráfico SVG sin librerías, selector de medida y filtro, temas y colores, exportación de agregados CSV, galería con ampliación, copia de comandos, presentación sin menú y modo pantalla completa real (botón «⛶ Pantalla completa», Shift+F, Esc para salir).
- Archivo aportado `FraudCloud_Streamlit_original_guardado.html` conservado como fuente en `documentos/`.

## Diferencia entre app HTML y Streamlit original

El HTML aportado por el usuario es **un archivo guardado de una página Streamlit desde `http://localhost:8501/`**. No incluye el servidor Python ni convierte automáticamente los widgets originales en una app estática funcional. La pestaña «App tarjetas de crédito» es una reconstrucción interactiva en HTML/JS que conserva los mismos KPIs y las comparaciones clave a partir de los agregados del proyecto. Si deseas usar el Streamlit original, inicia el backend con `python -m streamlit run dashboard/app.py` en el proyecto Python correspondiente y abre el puerto 8501.

Los datos que visualiza la presentación **no se sincronizan en vivo desde AWS**; son los ocho CSV Athena históricos del proyecto. Para actualizar, sustituir los agregados `data.js` tras repetir la extracción validada del pipeline.

## Evidencias y cifras que NO deben confundirse

- CloudFormation CREATE_COMPLETE, ETL SUCCEEDED y crawler READY: evidencias del pipeline real.
- 8 CSV de resultados Athena, de los que 3 tienen capturas directas; las otras 5 salidas se verifican por el paquete aws.zip.
- US$ 5,288387813 ≈ US$ 5,29: escenario modelado en AWS Pricing Calculator antes de descuentos, no una factura.
- US$ 0,00 en Bills: vista neta de la cuenta al 04/11/2026, con posibles créditos; no significa costo cero de la carga.
- EC2, RDS, NAT/VPC antiguos son ajenos al stack documentado de FraudCloud.
- No hay evidencia de dashboard Streamlit públicamente publicado en EC2: se documentó su ejecución en localhost.

## Publicar en AWS (sitio web estático)

Para mostrar **esta presentación HTML**, alojar los archivos con un servicio de hosting estático como S3 + CloudFront. Se recomienda **S3 privado + CloudFront Origin Access Control (OAC) + HTTPS**. No publicar el CSV original de transacciones ni claves AWS. Revisar y anonimizar evidencias de consola antes de hacerlas públicas.

Esta presentación HTML no ejecuta consultas Athena desde el navegador, no registra transacciones, no detecta fraude en tiempo real y no cambia los recursos AWS existentes.

## Procedencia

Proyecto FraudCloud AWS Big Data 2026. Fecha de evidencias: 04/11/2026. Base técnica: informe final, repositorio y material audiovisual aportado; 14 imágenes seleccionadas. Informe original, diccionario y CSV de Pricing Calculator disponibles en las entregas previas del proyecto.


## Pestaña adicional: Proyecto completo y código fuente

Se incorporó la pestaña **«Proyecto completo»** con:

- Evaluación honesta de cumplimiento de la rúbrica en `PF.pdf`: completo, parcialmente acreditado, opcional y pendiente.
- Tarjetas por carpeta, dependencias tomadas de los `requirements.txt` reales, mapa de scripts y ocho SQL.
- Navegador interactivo del árbol de archivos y visor de código fuente íntegro para archivos de texto.
- Descarga de cada archivo fuente visible y comandos de ejecución local o AWS.
- Paquete principal **con configuración corregida**, en `proyecto_fuente/aws.zip`, que incluye el CSV completo (54 MB) dentro del ZIP.
- Paquete adicional para EC2 en `proyecto_fuente/FraudCloud_Streamlit_AWS_EC2.zip`.

La presentación en HTML no contiene el dataset crudo (por volumen). El archivo único standalone sí contiene las fuentes textuales y las 14 capturas y los ocho CSV Athena, por lo que es interactivo sin archivos auxiliares. La existencia de los scripts EC2 no prueba por sí sola un despliegue público de Streamlit.


## Cambios del pipeline · 05/11/2026

- Se incorporan al visor y carpeta `documentos/` los 8 CSV **exportados de Athena** contenidos en el archivo `aws.zip` aportado.
- En el proceso se muestran las etapas SSO, MFA, CloudFormation, S3, Glue ETL, Crawler, Athena y visualización.
- MFA figura **validado por las capturas aportadas por el usuario**. El uso de `AdministratorAccess` no representa el principio de mínimo privilegio y continúa siendo una recomendación de mejora.
- Se eliminó de la presentación HTML la sección **«Guion de exposición de 12 minutos»**. Se conservan las conclusiones.
- El ZIP fuente actualizado está incluido como `proyecto_fuente/aws.zip`, sin modificar sus archivos de origen.
- Las nuevas imágenes de MFA, al no disponerse como archivo de imagen independiente en el directorio de trabajo, no se han sustituido por ilustraciones ni se han añadido capturas ficticias a la galería.
