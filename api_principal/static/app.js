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

/* ---------------------------- Ambitos de monitoreo ---------------------------- */
/* Selector multiple (chips) alimentado por /api/ambitos: un ambito nuevo en la
   base de datos aparece solo, sin editar el front-end. Sin seleccion = todos. */
const ClaveAmbitos = "iotmangrove.ambitos";

function ambitosGuardados() {
  try { return JSON.parse(localStorage.getItem(ClaveAmbitos)) || []; } catch (e) { return []; }
}
function guardarAmbitos(lista) {
  try { localStorage.setItem(ClaveAmbitos, JSON.stringify(lista)); } catch (e) { /* almacenamiento no disponible */ }
}

/* Dibuja los chips dentro de `caja`. Devuelve {catalogo, seleccion()}. `alCambiar` se
   invoca con la lista de codigos elegidos cada vez que el usuario cambia la seleccion. */
async function selectorAmbitos(caja, alCambiar) {
  const r = await api("/api/ambitos?limite=100");
  const catalogo = r.datos.slice().sort((a, b) => a.orden - b.orden);
  const validos = new Set(catalogo.map(a => a.codigo));
  let elegidos = ambitosGuardados().filter(c => validos.has(c));
  function pintar() {
    caja.innerHTML = '<span class="chips-titulo">Mostrar:</span>' + catalogo.map(a =>
      '<button type="button" class="chip" data-codigo="' + escapar(a.codigo) + '" aria-pressed="' +
      elegidos.includes(a.codigo) + '" title="' + escapar(a.descripcion || "") + '">' + escapar(a.nombre) + '</button>').join("") +
      '<button type="button" class="chip chip-todos" data-codigo="" aria-pressed="' + (elegidos.length === 0) + '">Todos</button>';
  }
  caja.addEventListener("click", (e) => {
    const b = e.target.closest("button.chip");
    if (!b) return;
    const codigo = b.dataset.codigo;
    if (!codigo) elegidos = [];
    else elegidos = elegidos.includes(codigo) ? elegidos.filter(c => c !== codigo) : [...elegidos, codigo];
    if (elegidos.length === catalogo.length) elegidos = [];
    guardarAmbitos(elegidos); pintar(); alCambiar(elegidos);
  });
  pintar();
  return { catalogo, seleccion: () => elegidos.slice() };
}

/* Permisos del usuario sobre un modulo, p. ej. permisoModulo("riego").puede_editar */
let _permisos = null;
async function permisoModulo(modulo) {
  if (!_permisos) {
    try { _permisos = (await api("/api/auth/me")).permisos; } catch (e) { _permisos = []; }
  }
  return _permisos.find(p => p.modulo === modulo) || {};
}
