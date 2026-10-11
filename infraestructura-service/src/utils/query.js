function incluirInactivos(req) {
  const valor = req.query.incluir_inactivos ?? req.query.incluirInactivos;
  return String(valor || '').toLowerCase() === 'true';
}

function numeroQuery(valor) {
  if (valor === undefined || valor === null || valor === '') {
    return undefined;
  }
  const n = Number(valor);
  return Number.isFinite(n) ? n : undefined;
}

module.exports = { incluirInactivos, numeroQuery };
