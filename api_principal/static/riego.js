/* IoT-Mangrove: panel del sistema de riego (se muestra con el ambito RIEGO).
   Consulta /api/riego/estado, permite cambiar el modo de cada zona y enviar
   ordenes manuales. Las ordenes pasan por una cola: la valvula la mueve el
   controlador central, por eso la posicion se actualiza con el siguiente
   reporte y no al pulsar el boton. */

const ETIQUETA_MODO = { AUTO: "Automatico", PROGRAMADO: "Programado", MANUAL: "Manual", APAGADO: "Apagado" };

function textoDuracion(s) {
  if (s == null) return "-";
  return s >= 60 ? Math.round(s / 60) + " min" : s + " s";
}

function tarjetaActuador(a, zona, puedeMandar) {
  const abierto = a.posicion === "ABIERTA" || a.posicion === "ENCENDIDA";
  const clase = abierto ? "ok" : a.posicion === "DESCONOCIDA" ? "adv" : "";
  let botones = "";
  if (puedeMandar) {
    const manual = !zona || zona.modo === "MANUAL";
    botones = '<div class="acciones">' +
      '<button type="button" class="primario" data-act="' + a.id + '" data-accion="ABRIR"' + (manual ? "" : " disabled title=\"La zona debe estar en modo Manual\"") + '>Abrir</button>' +
      '<button type="button" data-act="' + a.id + '" data-accion="CERRAR">Cerrar</button></div>';
  }
  return '<div class="actuador ' + clase + '"><div><strong>' + escapar(a.nombre) + '</strong> <span class="pie">' + escapar(a.codigo) + '</span></div>' +
    '<div class="pie">' + escapar(a.posicion) + (a.ultimo_reporte ? " | " + formatoFecha(a.ultimo_reporte) : " | sin reporte") + '</div>' + botones + '</div>';
}

function tarjetaZona(z, permiso) {
  const puedeEditar = Boolean(permiso.puede_editar), puedeMandar = Boolean(permiso.puede_crear);
  const humedad = z.humedad_actual != null ? Number(z.humedad_actual).toFixed(1) + " %" : "sin dato";
  const opciones = Object.entries(ETIQUETA_MODO).map(([k, v]) =>
    '<option value="' + k + '"' + (k === z.modo ? " selected" : "") + ">" + v + "</option>").join("");
  const modo = puedeEditar
    ? '<label>Modo<select data-zona="' + z.id + '">' + opciones + "</select></label>"
    : '<div class="pie">Modo: ' + escapar(ETIQUETA_MODO[z.modo]) + "</div>";
  const porcentaje = Math.min(100, Math.round(100 * (z.regado_hoy_s || 0) / z.limite_diario_s));
  return '<div class="tarjeta zona-riego"><div class="etiqueta">' + escapar(z.codigo) + " | " + escapar(z.ambito) + "</div>" +
    "<h3>" + escapar(z.nombre) + "</h3>" + modo +
    '<div class="datos-zona"><div><span class="pie">Humedad actual</span><br><strong>' + humedad + "</strong></div>" +
    '<div><span class="pie">Objetivo</span><br><strong>' + z.humedad_min + " - " + z.humedad_max + " %</strong></div></div>" +
    '<div class="pie">Regado hoy: ' + textoDuracion(z.regado_hoy_s) + " de " + textoDuracion(z.limite_diario_s) + "</div>" +
    '<div class="barra-uso" role="img" aria-label="Uso del limite diario ' + porcentaje + '%"><span style="width:' + porcentaje + '%"></span></div>' +
    '<div class="actuadores">' + (z.actuadores.length ? z.actuadores.map(a => tarjetaActuador(a, z, puedeMandar)).join("") : '<p class="pie">Sin valvulas asignadas</p>') + "</div></div>";
}

async function pintarPanelRiego(caja) {
  const [est, permiso] = await Promise.all([api("/api/riego/estado"), permisoModulo("riego")]);
  let html = "";
  if (!est.zonas.length && !est.actuadores_sin_zona.length) {
    html = '<p class="vacio">Aun no hay zonas de riego configuradas.</p>';
  } else {
    html += '<div class="rejilla">' + est.zonas.map(z => tarjetaZona(z, permiso)).join("") + "</div>";
    if (est.actuadores_sin_zona.length) {
      html += "<h3>Bomba y otros actuadores</h3><div class=\"rejilla\">" +
        est.actuadores_sin_zona.map(a => '<div class="tarjeta">' + tarjetaActuador(a, null, Boolean(permiso.puede_crear)) + "</div>").join("") + "</div>";
    }
    html += '<p class="pie" style="margin-top:8px">Ordenes en curso: ' + est.comandos_en_curso + "</p>";
    if (est.ultimos_eventos.length) {
      html += '<h3>Ultimos riegos</h3><div class="tabla-caja"><table><thead><tr><th>Inicio</th><th>Zona</th><th>Actuador</th><th>Duracion</th><th>Origen</th></tr></thead><tbody>' +
        est.ultimos_eventos.map(e => "<tr><td>" + formatoFecha(e.inicio) + "</td><td>" + escapar(e.zona || "-") + "</td><td>" + escapar(e.actuador) +
          "</td><td>" + textoDuracion(e.duracion_s) + "</td><td>" + escapar(e.origen) + "</td></tr>").join("") + "</tbody></table></div>";
    }
  }
  const mensaje = caja.querySelector(".mensaje");
  const previo = mensaje ? mensaje.outerHTML : '<div class="mensaje" role="status"></div>';
  caja.innerHTML = previo + html;
}

/* Delegacion de eventos: se instala una sola vez sobre la caja del panel */
function instalarMandoRiego(caja) {
  const aviso = (texto, ok) => {
    const m = caja.querySelector(".mensaje");
    if (m) { m.className = "mensaje " + (ok ? "ok" : "error"); m.textContent = texto; }
  };
  caja.addEventListener("change", async (e) => {
    const sel = e.target.closest("select[data-zona]");
    if (!sel) return;
    try {
      await api("/api/riego/zonas/" + sel.dataset.zona + "/modo", { method: "PUT", body: JSON.stringify({ modo: sel.value }) });
      await pintarPanelRiego(caja); aviso("Modo actualizado", true);
    } catch (err) { await pintarPanelRiego(caja); aviso(err.message, false); }
  });
  caja.addEventListener("click", async (e) => {
    const b = e.target.closest("button[data-act]");
    if (!b || b.disabled) return;
    b.disabled = true;
    try {
      const r = await api("/api/riego/comandos", { method: "POST",
        body: JSON.stringify({ actuador_id: Number(b.dataset.act), accion: b.dataset.accion }) });
      aviso("Orden " + r.accion + " enviada a " + r.actuador + ". El controlador la ejecutara en el siguiente intercambio.", true);
    } catch (err) { aviso(err.message, false); }
    b.disabled = false;
  });
}
