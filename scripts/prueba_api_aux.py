"""Prueba de humo de la API auxiliar (Express + MySQL).

Uso:
    python scripts/prueba_api_aux.py URL_PRINCIPAL URL_AUXILIAR ADMIN_PASSWORD

Obtiene un JWT en la API principal y comprueba que la API auxiliar lo
acepta: lectura publica, escritura protegida, CRUD con eliminacion
logica, buscador del chatbot y bitacora de consultas.
"""

import sys
import uuid

import httpx

PRINCIPAL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
AUX = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3000"
CLAVE = sys.argv[3] if len(sys.argv) > 3 else "Admin#Prueba1"

resultados = []


def verificar(nombre, condicion, detalle=""):
    resultados.append(bool(condicion))
    print(("OK    " if condicion else "FALLO ") + nombre + (f"  [{detalle}]" if not condicion else ""))


tok = httpx.post(f"{PRINCIPAL}/api/auth/login", json={"username": "admin", "password": CLAVE}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
c = httpx.Client(base_url=AUX, timeout=15)
sufijo = uuid.uuid4().hex[:6]

verificar("salud", c.get("/salud").json()["estado"] == "ok")
verificar("lectura publica de categorias", c.get("/categorias").json()["total"] >= 4)
r = c.get("/referencias/codigo/PH")
verificar("ficha de variable por codigo", r.status_code == 200 and r.json()["unidad"] == "pH", r.text)
verificar("ficha inexistente devuelve 404", c.get("/referencias/codigo/xyz").status_code == 404)

verificar("escribir sin token devuelve 401", c.post("/categorias", json={"nombre": "x"}).status_code == 401)
verificar("token invalido devuelve 401", c.post("/categorias", json={"nombre": "x"}, headers={"Authorization": "Bearer abc"}).status_code == 401)

r = c.post("/categorias", headers=H, json={"nombre": f"Prueba {sufijo}", "descripcion": "temporal"})
verificar("crear categoria", r.status_code == 201 and r.json()["estado"] is True and r.json()["creado"], r.text)
cat = r.json()
verificar("categoria duplicada devuelve 409", c.post("/categorias", headers=H, json={"nombre": f"Prueba {sufijo}"}).status_code == 409)
verificar("campo obligatorio ausente devuelve 400", c.post("/categorias", headers=H, json={"descripcion": "x"}).status_code == 400)

r = c.put(f"/categorias/{cat['id']}", headers=H, json={"descripcion": "editada"})
verificar("actualizar categoria", r.status_code == 200 and r.json()["descripcion"] == "editada", r.text)

r = c.post("/conocimiento", headers=H, json={"categoria_id": cat["id"], "pregunta": f"Pregunta {sufijo}?", "respuesta": "Respuesta de prueba", "palabras_clave": f"zzprueba{sufijo}"})
verificar("crear conocimiento", r.status_code == 201, r.text)
con = r.json()
r = c.post("/conocimiento", headers=H, json={"categoria_id": 99999, "pregunta": "otra?", "respuesta": "x", "palabras_clave": "x"})
verificar("categoria inexistente devuelve 400", r.status_code == 400, r.text)
r = c.get(f"/chatbot/consultar?q=zzprueba{sufijo}")
verificar("el chatbot encuentra la entrada nueva", r.json()["encontrada"] and r.json()["respuesta"] == "Respuesta de prueba", r.text)
r = c.post("/chatbot/consultar", json={"q": "que es el TDS", "origen": "tidio"})
verificar("consulta por POST (webhook)", r.status_code == 200 and r.json()["encontrada"], r.text)

verificar("bitacora protegida sin token", c.get("/consultas").status_code == 401)
log = c.get("/consultas?limite=5", headers=H).json()
verificar("bitacora registra las consultas", log["total"] >= 3 and log["datos"][0]["texto_consulta"], str(log)[:200])

r = c.delete(f"/conocimiento/{con['id']}", headers=H)
verificar("eliminar es logico", r.status_code == 200 and r.json()["estado"] is False, r.text)
verificar("no aparece en el listado", all(x["id"] != con["id"] for x in c.get("/conocimiento").json()["datos"]))
verificar("el chatbot ya no la usa", not c.get(f"/chatbot/consultar?q=zzprueba{sufijo}").json()["encontrada"])
r = c.post(f"/conocimiento/{con['id']}/restaurar", headers=H)
verificar("restaurar", r.status_code == 200 and r.json()["estado"] is True, r.text)
verificar("id invalido devuelve 400", c.get("/categorias/abc").status_code == 400)

# Rol sin permiso (consulta) no puede escribir
usuario = f"c_{sufijo}"
httpx.post(f"{PRINCIPAL}/api/auth/registro", json={"username": usuario, "password": "Clave123"})
tok2 = httpx.post(f"{PRINCIPAL}/api/auth/login", json={"username": usuario, "password": "Clave123"}).json()["access_token"]
verificar("rol consulta no puede escribir (403)", c.post("/categorias", headers={"Authorization": f"Bearer {tok2}"}, json={"nombre": "z"}).status_code == 403)

print(f"\n{sum(resultados)}/{len(resultados)} pruebas correctas")
sys.exit(0 if all(resultados) else 1)
