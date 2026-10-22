// Respuesta real de https://date.nager.at/api/v4/Holidays/CO/2026
// Copia local usada por las pruebas: las pruebas NUNCA salen a la red.
//
// Los nombres y las fechas son los que devuelve la API oficial. "Ascension
// Day" (2026-05-14) y "Corpus Christi" (2026-06-04) llegan en el dia de la
// plegaria; la correccion Ley Emiliani los lleva al lunes siguiente
// (2026-05-18 y 2026-06-08).
const FESTIVOS_CO_2026 = [
  { date: '2026-01-01', name: "New Year's Day", countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-01-12', name: 'Epiphany', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-03-23', name: "Saint Joseph's Day", countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-04-02', name: 'Maundy Thursday', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-04-03', name: 'Good Friday', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-05-01', name: 'Labour Day', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-05-14', name: 'Ascension Day', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-06-04', name: 'Corpus Christi', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-06-15', name: 'Sacred Heart', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-06-29', name: 'Saint Peter and Saint Paul', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-07-13', name: 'Our Lady of Chiquinquirá Day', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-07-20', name: 'Declaration of Independence', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-08-07', name: 'Battle of Boyacá', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-08-17', name: 'Assumption of Mary', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-10-12', name: 'Columbus Day', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-11-02', name: 'All Saints’ Day', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-11-16', name: 'Independence of Cartagena', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-12-08', name: 'Immaculate Conception', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
  { date: '2026-12-25', name: 'Christmas Day', countryCode: 'CO', nationalHoliday: true, subdivisionCodes: null, holidayTypes: ['Public'] },
];

// Respuesta de error tipica de la API: objeto con "message".
const ERROR_NAGER = { message: 'Not found' };

module.exports = { FESTIVOS_CO_2026, ERROR_NAGER };
