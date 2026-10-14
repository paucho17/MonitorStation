/* IoT-Mangrove: utilidades compartidas del front-end (JWT en sessionStorage). */
const Sesion = {
  token() { return sessionStorage.getItem("token"); },
  usuario() { try { return JSON.parse(sessionStorage.getItem("usuario")); } catch (e) { return null; } },
  guardar(datos) {
    sessionStorage.setItem("token", datos.access_token);
    sessionStorage.setItem("usuario", JSON.stringify(datos.usuario));
  },
  limpiar() { sessionStorage.removeItem("token"); sessionStorage.removeItem("usuario"); },
};

async function api(ruta, opciones = {}) {
  const cabeceras = { "Content-Type": "application/json", ...(opciones.headers || {}) };
  if (Sesion.token()) cabeceras["Authorization"] = "Bearer " + Sesion.token();
  const resp = await fetch(ruta, { ...opciones, headers: cabeceras });
  if (resp.status === 401 && !ruta.includes("/auth/login")) {
    Sesion.limpiar();
    window.location.href = "index.html";
    throw new Error("Sesión expirada");
  }
  const cuerpo = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(typeof cuerpo.detail === "string" ? cuerpo.detail : "Error " + resp.status);
  return cuerpo;
}

function exigirSesion() {
  if (!Sesion.token()) { window.location.href = "index.html"; return false; }
  const nombre = document.getElementById("usuario-actual");
  if (nombre && Sesion.usuario()) nombre.textContent = Sesion.usuario().username + " (" + Sesion.usuario().rol + ")";
  const salir = document.getElementById("salir");
  if (salir) salir.addEventListener("click", async () => {
    try { await api("/api/auth/logout", { method: "POST" }); } catch (e) { /* sesion ya cerrada */ }
    Sesion.limpiar(); window.location.href = "index.html";
  });
  return true;
}

function formatoFecha(iso) {
  return iso ? new Date(iso).toLocaleString("es-CO") : "-";
}
function escapar(texto) {
  const d = document.createElement("div"); d.textContent = texto == null ? "" : String(texto); return d.innerHTML;
}
