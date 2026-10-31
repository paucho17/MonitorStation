"""Pruebas de ambitos, ingesta con alias en base de datos y sistema de riego."""

from datetime import datetime, timedelta, timezone

import pytest


def ingestar(cliente, gw, **trama):
    r = cliente.post("/api/ingest", json=trama, headers=gw)
    assert r.status_code == 201, r.text
    return r.json()


def test_ambitos_listados(cliente, consulta):
    r = cliente.get("/api/ambitos", headers=consulta)
    assert r.status_code == 200
    assert [a["codigo"] for a in r.json()["datos"]] == ["MANGLAR", "VIVERO", "RIEGO"]


def test_nodos_existentes_quedan_en_manglar(cliente, admin):
    nodos = cliente.get("/api/nodos", headers=admin).json()["datos"]
    assert nodos and all(n["ambito_id"] == 1 for n in nodos)


def test_ingesta_nueva_variable_por_alias_y_ambito(cliente, gw):
    r = ingestar(cliente, gw, nodeID="0xV1", type="SOIL", scope="vivero", rssi=-80,
                 data={"soilHumidity": 41.5, "soilTemp": 27.3, "desconocida": 5})
    assert r["mediciones"] == 2 and r["ignoradas"] == ["desconocida"]


def test_ingesta_ambito_invalido(cliente, gw):
    r = cliente.post("/api/ingest", headers=gw,
                     json={"nodeID": "0xV9", "type": "SOIL", "scope": "LUNA", "data": {"soilHumidity": 1}})
    assert r.status_code == 400


def test_ingesta_scope_no_cambia_nodo_existente(cliente, gw, admin):
    ingestar(cliente, gw, nodeID="0xV1", type="SOIL", scope="RIEGO", data={"soilHumidity": 40})
    nodo = [n for n in cliente.get("/api/nodos", headers=admin).json()["datos"] if n["codigo"] == "0XV1"][0]
    assert nodo["ambito_id"] == 2  # sigue en VIVERO


def test_alias_nuevo_sin_tocar_codigo(cliente, gw, admin):
    var = [v for v in cliente.get("/api/variables", headers=admin).json()["datos"] if v["codigo"] == "co2"][0]
    assert cliente.post("/api/alias-variables", headers=admin,
                        json={"alias": "scd_co2", "variable_id": var["id"]}).status_code == 201
    r = ingestar(cliente, gw, nodeID="0xV2", type="AMB", scope="VIVERO", data={"scd_co2": 650, "pm25": 12, "pm10": 20})
    assert r["mediciones"] == 3


def test_alerta_por_umbral_nuevo(cliente, gw):
    r = ingestar(cliente, gw, nodeID="0xR1", type="RIEGO", scope="RIEGO", data={"tankLevel": 8, "vbat": 12.4})
    assert any(a["variable"] == "tank_level" and a["nivel"] == "CRITICO" for a in r["alertas"])


def test_dashboard_filtra_por_ambito(cliente, admin):
    def nodos(ambito):
        params = {"ambito": ambito} if ambito else {}
        d = cliente.get("/api/dashboard", headers=admin, params=params).json()
        return {v["nodo"] for v in d["variables"]}, {v["ambito"] for v in d["variables"]}
    todos, _ = nodos(None)
    n_viv, a_viv = nodos("VIVERO")
    n_rie, a_rie = nodos("RIEGO")
    n_ambos, a_ambos = nodos("vivero,riego")
    assert a_viv == {"VIVERO"} and a_rie == {"RIEGO"} and a_ambos == {"VIVERO", "RIEGO"}
    assert "0XAA" in todos and "0XAA" not in n_ambos
    assert n_ambos == n_viv | n_rie
    assert nodos("todos")[0] == todos


def test_historial_filtra_por_ambito(cliente, admin):
    d = cliente.get("/api/historial", headers=admin, params={"ambito": "RIEGO"}).json()
    assert d["total"] > 0 and {f["ambito"] for f in d["datos"]} == {"RIEGO"}


# ------------------------------- Riego -------------------------------

@pytest.fixture(scope="module")
def riego(cliente, admin):
    """Zona de vivero con dos valvulas y una bomba."""
    zona = cliente.post("/api/zonas-riego", headers=admin, json={
        "codigo": "z1", "nombre": "Vivero A", "ambito_id": 2,
        "duracion_max_s": 300, "descanso_min_s": 60, "limite_diario_s": 500}).json()
    v1 = cliente.post("/api/actuadores", headers=admin,
                      json={"codigo": "v1", "nombre": "Valvula 1", "tipo": "VALVULA", "zona_riego_id": zona["id"]}).json()
    bomba = cliente.post("/api/actuadores", headers=admin,
                         json={"codigo": "b1", "nombre": "Bomba", "tipo": "BOMBA"}).json()
    return {"zona": zona, "v1": v1, "bomba": bomba}


def test_zona_nace_apagada(riego):
    assert riego["zona"]["modo"] == "APAGADO" and riego["v1"]["codigo"] == "V1"


def test_zona_humedad_invalida(cliente, admin):
    r = cliente.post("/api/zonas-riego", headers=admin, json={
        "codigo": "zx", "nombre": "x", "ambito_id": 2, "humedad_min": 80, "humedad_max": 20})
    assert r.status_code == 400


def test_abrir_exige_modo_manual(cliente, admin, riego):
    r = cliente.post("/api/riego/comandos", headers=admin, json={"actuador_id": riego["v1"]["id"], "accion": "ABRIR"})
    assert r.status_code == 409


def test_flujo_manual_completo(cliente, admin, gw, riego):
    zid = riego["zona"]["id"]
    assert cliente.put(f"/api/riego/zonas/{zid}/modo", headers=admin, json={"modo": "MANUAL"}).status_code == 200
    r = cliente.post("/api/riego/comandos", headers=admin,
                     json={"actuador_id": riego["v1"]["id"], "accion": "ABRIR", "duracion_s": 120})
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    p = cliente.get("/api/riego/central/pendientes", headers=gw).json()
    assert [c["id"] for c in p["comandos"]] == [cid] and p["comandos"][0]["actuador"] == "V1"
    assert any(z["codigo"] == "Z1" and z["valvulas"] == ["V1"] for z in p["zonas"])
    assert cliente.get("/api/riego/central/pendientes", headers=gw).json()["comandos"] == []
    fin = datetime.now(timezone.utc) - timedelta(seconds=10)
    rep = cliente.post("/api/riego/central/reporte", headers=gw, json={
        "actuadores": [{"codigo": "v1", "posicion": "ABIERTA"}, {"codigo": "zz", "posicion": "CERRADA"}],
        "comandos": [{"id": cid, "situacion": "EJECUTADO"}],
        "eventos": [{"actuador": "V1", "inicio": (fin - timedelta(seconds=120)).isoformat(),
                     "fin": fin.isoformat(), "origen": "MANUAL"}]})
    assert rep.status_code == 200 and rep.json()["ignorados"] == ["ZZ"]
    assert cliente.get(f"/api/riego/comandos/{cid}", headers=admin).json()["situacion"] == "EJECUTADO"
    est = cliente.get("/api/riego/estado", headers=admin, params={"ambito": "VIVERO"}).json()
    zona = [z for z in est["zonas"] if z["codigo"] == "Z1"][0]
    assert zona["actuadores"][0]["posicion"] == "ABIERTA"
    assert any(a["codigo"] == "B1" for a in est["actuadores_sin_zona"])


def test_limites_de_seguridad(cliente, admin, riego):
    ab = {"actuador_id": riego["v1"]["id"], "accion": "ABRIR"}
    assert cliente.post("/api/riego/comandos", headers=admin, json={**ab, "duracion_s": 301}).status_code == 400
    assert cliente.post("/api/riego/comandos", headers=admin, json={**ab, "duracion_s": 100}).status_code == 409  # en descanso
    assert cliente.post("/api/riego/comandos", headers=admin,
                        json={"actuador_id": riego["v1"]["id"], "accion": "CERRAR"}).status_code == 201


def test_apagar_zona_ordena_cerrar(cliente, admin, gw, riego):
    zid = riego["zona"]["id"]
    cliente.put(f"/api/riego/zonas/{zid}/modo", headers=admin, json={"modo": "APAGADO"})
    cmds = cliente.get("/api/riego/central/pendientes", headers=gw).json()["comandos"]
    assert cmds and all(c["accion"] == "CERRAR" for c in cmds)


def test_modo_invalido(cliente, admin, riego):
    assert cliente.put(f"/api/riego/zonas/{riego['zona']['id']}/modo", headers=admin, json={"modo": "TURBO"}).status_code == 422


def test_permisos_consulta(cliente, consulta, riego):
    assert cliente.get("/api/riego/estado", headers=consulta).status_code == 200
    assert cliente.put(f"/api/riego/zonas/{riego['zona']['id']}/modo", headers=consulta, json={"modo": "AUTO"}).status_code == 403
    assert cliente.post("/api/riego/comandos", headers=consulta,
                        json={"actuador_id": riego["v1"]["id"], "accion": "ABRIR"}).status_code == 403


def test_central_exige_clave(cliente):
    assert cliente.get("/api/riego/central/pendientes").status_code == 401
    assert cliente.get("/api/riego/central/pendientes", headers={"X-API-Key": "mala"}).status_code == 401


def test_ordenes_caducadas_se_cancelan(cliente, admin, gw, riego):
    import psycopg
    from tests.conftest import _conectar, BASE
    cliente.put(f"/api/riego/zonas/{riego['zona']['id']}/modo", headers=admin, json={"modo": "MANUAL"})
    cliente.get("/api/riego/central/pendientes", headers=gw)
    c = cliente.post("/api/riego/comandos", headers=admin,
                     json={"actuador_id": riego["bomba"]["id"], "accion": "ABRIR", "duracion_s": 60}).json()
    with _conectar(BASE) as db:
        db.execute("UPDATE comando_riego SET creado = now() - interval '1 hour' WHERE id = %s", (c["id"],))
    assert cliente.get("/api/riego/central/pendientes", headers=gw).json()["comandos"] == []
    assert cliente.get(f"/api/riego/comandos/{c['id']}", headers=admin).json()["situacion"] == "CANCELADO"
