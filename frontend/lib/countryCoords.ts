export type CountryCoord = { lat: number; lng: number; iso2: string }

export const COUNTRY_COORDS: Record<string, CountryCoord> = {
  UK:             { lat: 55.3781, lng:  -3.4360, iso2: 'GB' },
  US:             { lat: 39.8283, lng: -98.5795, iso2: 'US' },
  Qatar:          { lat: 25.3548, lng:  51.1839, iso2: 'QA' },
  'Saudi Arabia': { lat: 23.8859, lng:  45.0792, iso2: 'SA' },
  Pakistan:       { lat: 30.3753, lng:  69.3451, iso2: 'PK' },
  Russia:         { lat: 61.5240, lng: 105.3188, iso2: 'RU' },
  Germany:        { lat: 51.1657, lng:  10.4515, iso2: 'DE' },
  France:         { lat: 46.6034, lng:   1.8883, iso2: 'FR' },
  India:          { lat: 20.5937, lng:  78.9629, iso2: 'IN' },
  Japan:          { lat: 36.2048, lng: 138.2529, iso2: 'JP' },
}
