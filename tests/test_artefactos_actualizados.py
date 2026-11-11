"""Pruebas sin credenciales AWS ni dependencia del servidor Streamlit."""
from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]


def test_17_evidencias_validas():
    directory = ROOT / "assets" / "evidencias"
    images = sorted(directory.glob("*.png"))
    assert len(images) == 17
    assert [int(p.name.split("_", 1)[0]) for p in images] == list(range(1, 18))
    for path in images:
        assert path.read_bytes().startswith(bytes.fromhex("89504e470d0a1a0a"))
    for prefix in ("15_mfa", "16_mfa", "17_correo"):
        assert any(p.name.startswith(prefix) for p in images)


def test_presentacion_y_reportes_integrados():
    presentation = ROOT / "presentacion" / "FraudCloud_Presentacion.html"
    assert presentation.is_file()
    content = presentation.read_text(encoding="utf8")
    assert content.count("data:image/png;base64,") >= 17
    assert 'Configuración AWS de autenticador MFA' in content
    assert 'Correo AWS Billing' in content
    for extension in ("pdf", "docx"):
        assert (ROOT / "docs" / f"Informe_FraudCloud_2026_Completo_MFA_Creditos.{extension}").is_file()


def test_paginas_streamlit_de_seguridad_y_costos():
    code = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    ast.parse(code)
    for item in ("def page_finops()", "def page_security()", "17_correo_creditos_aws_protegido.png",
                 "st.image(path.read_bytes()", "FraudCloud_Presentacion.html"):
        assert item in code
