from fraudcloud.data import SOURCES, load_tables, validate_tables, as_view


def test_athena_totals():
    data = load_tables("Athena · resultados exportados (AWS)")
    assert not validate_tables(data)
    k = data["01"].iloc[0]
    assert int(k["total_transacciones"]) == 339607
    assert int(k["transacciones_fraude"]) == 1782
    assert abs(float(k["tasa_fraude_pct"]) - 0.5247) < 1e-9


def test_local_totals():
    data = load_tables("Previsualización local · no es AWS")
    assert not validate_tables(data)


def test_labels_are_strings():
    data = load_tables("Athena · resultados exportados (AWS)")
    v = as_view(data["03"], "es_noche", {"0": "Día", "1": "Noche"})
    assert set(v.es_noche) == {"Día", "Noche"}
