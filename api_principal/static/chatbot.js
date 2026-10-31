/* IoT-Mangrove: widget de chat integrado en el front-end.
   Se conecta a la API auxiliar (a traves de Nginx, bajo /aux) con
   POST /aux/chatbot/consultar y muestra el campo "respuesta".
   No depende de servicios externos. Basta incluir <script src="chatbot.js">
   en cualquier pagina. La ruta se puede cambiar con window.CHATBOT_URL antes
   de cargar el script. */
(function () {
  "use strict";
  const URL_CONSULTA = window.CHATBOT_URL || "/aux/chatbot/consultar";
  const SUGERENCIAS = [
    "Que es el pH y cual es su rango normal?",
    "Cuando se riega automaticamente?",
    "Que significa una alerta critica?",
    "Que mide el sensor de CO2?",
  ];
  const BIENVENIDA = "Hola, soy el asistente de IoT-Mangrove. Puedo explicarte las variables que medimos, sus umbrales y como funciona el riego.";

  function el(etiqueta, atributos, texto) {
    const e = document.createElement(etiqueta);
    Object.entries(atributos || {}).forEach(([k, v]) => e.setAttribute(k, v));
    if (texto != null) e.textContent = texto;
    return e;
  }

  function construir() {
    const boton = el("button", { type: "button", class: "chat-boton", "aria-label": "Abrir asistente", "aria-expanded": "false", "aria-controls": "chat-panel" }, "Asistente");
    const panel = el("section", { class: "chat-panel", id: "chat-panel", role: "dialog", "aria-label": "Asistente de IoT-Mangrove", hidden: "" });
    const cabecera = el("header", { class: "chat-cabecera" });
    cabecera.append(el("strong", {}, "Asistente IoT-Mangrove"));
    const cerrar = el("button", { type: "button", class: "chat-cerrar", "aria-label": "Cerrar" }, "x");
    cabecera.append(cerrar);
    const registro = el("div", { class: "chat-registro", role: "log", "aria-live": "polite" });
    const sugerencias = el("div", { class: "chat-sugerencias" });
    const formulario = el("form", { class: "chat-form", autocomplete: "off" });
    const entrada = el("input", { type: "text", name: "q", maxlength: "300", placeholder: "Escribe tu pregunta", "aria-label": "Pregunta" });
    const enviar = el("button", { type: "submit", class: "primario" }, "Enviar");
    formulario.append(entrada, enviar);
    panel.append(cabecera, registro, sugerencias, formulario);
    document.body.append(boton, panel);

    function burbuja(texto, quien) {
      const b = el("div", { class: "chat-msg " + quien }, texto);
      registro.append(b);
      registro.scrollTop = registro.scrollHeight;
      return b;
    }

    async function preguntar(texto) {
      texto = texto.trim();
      if (!texto) return;
      burbuja(texto, "usuario");
      sugerencias.hidden = true;
      const espera = burbuja("Escribiendo...", "bot espera");
      enviar.disabled = true;
      try {
        const resp = await fetch(URL_CONSULTA, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ q: texto, origen: "web" }),
        });
        const cuerpo = await resp.json().catch(() => ({}));
        if (!resp.ok) throw new Error(cuerpo.detail || "Error " + resp.status);
        espera.className = "chat-msg bot";
        espera.textContent = cuerpo.respuesta || "No tengo respuesta para eso.";
        if (cuerpo.variable && cuerpo.variable.rango_normal_min != null && cuerpo.variable.rango_normal_max != null) {
          espera.append(el("div", { class: "chat-nota" },
            "Rango de referencia: " + cuerpo.variable.rango_normal_min + " a " + cuerpo.variable.rango_normal_max + " " + (cuerpo.variable.unidad || "")));
        }
      } catch (err) {
        espera.className = "chat-msg bot error";
        espera.textContent = "No pude consultar el asistente: " + err.message;
      }
      enviar.disabled = false;
      registro.scrollTop = registro.scrollHeight;
      entrada.focus();
    }

    SUGERENCIAS.forEach((s) => {
      const b = el("button", { type: "button", class: "chat-sugerencia" }, s);
      b.addEventListener("click", () => preguntar(s));
      sugerencias.append(b);
    });
    formulario.addEventListener("submit", (e) => { e.preventDefault(); const t = entrada.value; entrada.value = ""; preguntar(t); });

    function alternar(abrir) {
      panel.hidden = !abrir;
      boton.setAttribute("aria-expanded", String(abrir));
      boton.hidden = abrir;
      if (abrir) { if (!registro.children.length) burbuja(BIENVENIDA, "bot"); entrada.focus(); } else { boton.focus(); }
    }
    boton.addEventListener("click", () => alternar(true));
    cerrar.addEventListener("click", () => alternar(false));
    panel.addEventListener("keydown", (e) => { if (e.key === "Escape") alternar(false); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", construir);
  else construir();
})();
