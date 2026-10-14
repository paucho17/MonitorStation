'use strict';

/**
 * Catalogo declarativo de recursos CRUD de la base auxiliar.
 * La lectura es pública en los recursos de conocimiento (los consume el
 * chatbot); toda escritura exige JWT de la API principal.
 */
module.exports = [
  {
    ruta: 'categorias',
    tabla: 'categoria_conocimiento',
    lecturaPublica: true,
    campos: [
      { nombre: 'nombre', tipo: 'texto', requerido: true, max: 80 },
      { nombre: 'descripcion', tipo: 'texto', max: 255 },
    ],
  },
  {
    ruta: 'referencias',
    tabla: 'referencia_variable',
    lecturaPublica: true,
    filtros: ['codigo_variable'],
    campos: [
      { nombre: 'codigo_variable', tipo: 'texto', requerido: true, max: 30 },
      { nombre: 'nombre', tipo: 'texto', requerido: true, max: 100 },
      { nombre: 'unidad', tipo: 'texto', requerido: true, max: 20 },
      { nombre: 'descripcion', tipo: 'texto', requerido: true },
      { nombre: 'uso', tipo: 'texto', requerido: true },
      { nombre: 'rango_normal_min', tipo: 'numero' },
      { nombre: 'rango_normal_max', tipo: 'numero' },
      { nombre: 'fuente', tipo: 'texto', max: 255 },
    ],
  },
  {
    ruta: 'conocimiento',
    tabla: 'conocimiento_chatbot',
    lecturaPublica: true,
    filtros: ['categoria_id', 'referencia_variable_id'],
    campos: [
      { nombre: 'categoria_id', tipo: 'entero', requerido: true },
      { nombre: 'referencia_variable_id', tipo: 'entero' },
      { nombre: 'pregunta', tipo: 'texto', requerido: true, max: 255 },
      { nombre: 'respuesta', tipo: 'texto', requerido: true },
      { nombre: 'palabras_clave', tipo: 'texto', requerido: true, max: 255 },
    ],
  },
  {
    // La bitacora la escribe el endpoint /chatbot/consultar; aqui solo se
    // consulta (admin y operador) y se elimina logicamente (solo admin).
    ruta: 'consultas',
    tabla: 'consulta_chatbot',
    lecturaPublica: false,
    permitirCrear: false,
    permitirEditar: false,
    ordenDescendente: true,
    rolesEliminar: ['admin'],
    filtros: ['conocimiento_id', 'encontrada', 'origen'],
    campos: [
      { nombre: 'conocimiento_id', tipo: 'entero', editable: false },
      { nombre: 'texto_consulta', tipo: 'texto', editable: false },
      { nombre: 'encontrada', tipo: 'booleano', editable: false },
      { nombre: 'origen', tipo: 'texto', editable: false },
    ],
  },
];
