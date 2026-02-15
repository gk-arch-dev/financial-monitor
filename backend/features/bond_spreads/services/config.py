"""Configuration for Bond Spreads feature.

Contains country/series ID mapping for FRED API.
"""

# FRED series IDs for 10-year government bond yields
YIELD_10Y_SERIES = {
    'US': 'DGS10',        # US 10-Year Treasury
    'DE': 'IRLTLT01DEM156N',  # Germany 10-Year
    'GB': 'IRLTLT01GBM156N',  # UK 10-Year
    'JP': 'IRLTLT01JPM156N',  # Japan 10-Year
    'FR': 'IRLTLT01FRM156N',  # France 10-Year
    'CA': 'IRLTLT01CAM156N',  # Canada 10-Year
    'AU': 'IRLTLT01AUM156N',  # Australia 10-Year
    'BR': 'IRLTLT01BRM156N',  # Brazil 10-Year
    'IN': 'IRLTLT01INM156N',  # India 10-Year
    'MX': 'IRLTLT01MXM156N',  # Mexico 10-Year
}

# FRED series IDs for 3-month government bond yields
YIELD_3M_SERIES = {
    'US': 'DTB3',         # US 3-Month T-Bill
    'DE': 'IR3TIB01DEM156N',  # Germany 3-Month
    'GB': 'IR3TIB01GBM156N',  # UK 3-Month
    'JP': 'IR3TIB01JPM156N',  # Japan 3-Month
    'FR': 'IR3TIB01FRM156N',  # France 3-Month
    'CA': 'IR3TIB01CAM156N',  # Canada 3-Month
    'AU': 'IR3TIB01AUM156N',  # Australia 3-Month
    'BR': 'IR3TIB01BRM156N',  # Brazil 3-Month
    'IN': 'IR3TIB01INM156N',  # India 3-Month
    'MX': 'IR3TIB01MXM156N',  # Mexico 3-Month
}

# Country metadata
COUNTRIES = {
    'US': {'name': 'United States', 'currency': 'USD', 'flag': '🇺🇸'},
    'DE': {'name': 'Germany', 'currency': 'EUR', 'flag': '🇩🇪'},
    'GB': {'name': 'United Kingdom', 'currency': 'GBP', 'flag': '🇬🇧'},
    'JP': {'name': 'Japan', 'currency': 'JPY', 'flag': '🇯🇵'},
    'FR': {'name': 'France', 'currency': 'EUR', 'flag': '🇫🇷'},
    'CA': {'name': 'Canada', 'currency': 'CAD', 'flag': '🇨🇦'},
    'AU': {'name': 'Australia', 'currency': 'AUD', 'flag': '🇦🇺'},
    'BR': {'name': 'Brazil', 'currency': 'BRL', 'flag': '🇧🇷'},
    'IN': {'name': 'India', 'currency': 'INR', 'flag': '🇮🇳'},
    'MX': {'name': 'Mexico', 'currency': 'MXN', 'flag': '🇲🇽'},
}
