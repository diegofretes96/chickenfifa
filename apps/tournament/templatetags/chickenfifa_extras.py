from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permite acceder a dict[key] desde templates: {{ dict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def puntos_class(puntos):
    """Devuelve la clase CSS para el badge de puntos."""
    if puntos == 5:
        return "puntos-5"
    if puntos == 3:
        return "puntos-3"
    if puntos == 2:
        return "puntos-2"
    return "puntos-0"


# Mapa de código FIFA (3 letras) → código ISO 3166-1 alpha-2 para flag-icons.
# Casos especiales: ENG/SCO/WAL usan subdivisiones GB.
_FIFA_A_ISO2 = {
    # CONCACAF
    "USA": "us", "CAN": "ca", "MEX": "mx", "PAN": "pa",
    "HON": "hn", "CRC": "cr", "JAM": "jm", "GUA": "gt",
    "SLV": "sv", "HAI": "ht", "TRI": "tt", "CUB": "cu",
    "BLZ": "bz", "GRN": "gd", "NCA": "ni", "MTQ": "mq",
    # CONMEBOL
    "ARG": "ar", "BRA": "br", "URU": "uy", "COL": "co",
    "CHI": "cl", "ECU": "ec", "PER": "pe", "VEN": "ve",
    "PAR": "py", "BOL": "bo",
    # UEFA
    "ESP": "es", "FRA": "fr", "GER": "de", "ENG": "gb-eng",
    "POR": "pt", "NED": "nl", "BEL": "be", "CRO": "hr",
    "SUI": "ch", "DEN": "dk", "AUT": "at", "SWE": "se",
    "NOR": "no", "SCO": "gb-sct", "WAL": "gb-wls", "IRL": "ie",
    "POL": "pl", "CZE": "cz", "SVK": "sk", "HUN": "hu",
    "ROU": "ro", "SRB": "rs", "TUR": "tr", "GRE": "gr",
    "UKR": "ua", "SVN": "si", "ISL": "is", "ALB": "al",
    "GEO": "ge", "MKD": "mk", "MNE": "me", "BIH": "ba",
    "FIN": "fi", "LUX": "lu", "NIR": "gb-nir",
    # CAF
    "MAR": "ma", "SEN": "sn", "NGA": "ng", "NGR": "ng",
    "CMR": "cm", "GHA": "gh", "TUN": "tn", "EGY": "eg",
    "ALG": "dz", "CIV": "ci", "MLI": "ml", "ZAF": "za",
    "COD": "cd", "BEN": "bj", "UGA": "ug", "KEN": "ke",
    "ZIM": "zw", "MDG": "mg", "ANG": "ao", "ETH": "et",
    "CPV": "cv", "COM": "km", "GUI": "gn", "MTN": "mr",
    "MOZ": "mz", "NAM": "na", "RWA": "rw", "SOM": "so",
    "SUD": "sd", "TAN": "tz", "ZAM": "zm",
    # AFC
    "JPN": "jp", "KOR": "kr", "AUS": "au", "IRN": "ir",
    "SAU": "sa", "QAT": "qa", "UAE": "ae", "IRQ": "iq",
    "JOR": "jo", "UZB": "uz", "THA": "th", "CHN": "cn",
    "IND": "in", "OMA": "om", "BHR": "bh", "IDN": "id",
    "PAL": "ps", "KGZ": "kg", "SYR": "sy", "LIB": "lb",
    "PRK": "kp", "VIE": "vn", "PHI": "ph", "MYA": "mm",
    "TKM": "tm", "AFG": "af", "PAK": "pk", "BAN": "bd",
    "SRI": "lk", "NEP": "np", "MLD": "mv",
    # OFC
    "NZL": "nz", "TAH": "pf", "NCL": "nc",
}


@register.filter
def bandera_iso2(equipo):
    """Devuelve el código ISO-2 en minúsculas para usar con flag-icons CSS.
    Uso: {{ partido.equipo_local|bandera_iso2 }} → 'ar'
    """
    if equipo is None:
        return ""
    code = getattr(equipo, "codigo_fifa", None) or str(equipo)
    return _FIFA_A_ISO2.get(code.upper(), "")
