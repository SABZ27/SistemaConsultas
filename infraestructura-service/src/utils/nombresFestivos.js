// Nombres en espanol de los festivos de Nager.Date.
//
// Las claves son EXACTAMENTE los valores del campo "name" que devuelve la API
// (verificado contra https://date.nager.at/api/v4/Holidays/CO/2026):
//   "New Year's Day", "Epiphany", "Saint Joseph's Day", "Maundy Thursday",
//   "Good Friday", "Labour Day", "Ascension Day", "Corpus Christi",
//   "Sacred Heart", "Saint Peter and Saint Paul", "Our Lady of Chiquinquirá Day",
//   "Declaration of Independence", "Battle of Boyacá", "Assumption of Mary",
//   "Columbus Day", "All Saints’ Day", "Independence of Cartagena",
//   "Immaculate Conception", "Christmas Day".
//
// Si un festivo no aparece en este mapa se guarda el nombre de la API tal cual.
// Hay un test de regresion que falla si alguna clave deja de existir en la API o
// si la API devuelve un festivo sin traducir.
const NOMBRES_ES = {
  "New Year's Day": 'Año Nuevo',
  Epiphany: 'Día de los Reyes Magos',
  "Saint Joseph's Day": 'Día de San José',
  'Maundy Thursday': 'Jueves Santo',
  'Good Friday': 'Viernes Santo',
  'Labour Day': 'Día del Trabajo',
  'Ascension Day': 'Ascensión del Señor',
  'Corpus Christi': 'Corpus Christi',
  'Sacred Heart': 'Sagrado Corazón',
  'Saint Peter and Saint Paul': 'San Pedro y San Pablo',
  'Our Lady of Chiquinquirá Day': 'Día de la Virgen de Chiquinquirá',
  'Declaration of Independence': 'Declaración de la Independencia de Colombia',
  'Battle of Boyacá': 'Batalla de Boyacá',
  'Assumption of Mary': 'La Asunción',
  'Columbus Day': 'Día de la Raza',
  'All Saints’ Day': 'Día de los Santos',
  'Independence of Cartagena': 'Independencia de Cartagena',
  'Immaculate Conception': 'La Inmaculada Concepción',
  'Christmas Day': 'Navidad',
};

function nombreEnEspanol(nombre) {
  if (!nombre) {
    return null;
  }
  return NOMBRES_ES[nombre] || null;
}

module.exports = { NOMBRES_ES, nombreEnEspanol };
