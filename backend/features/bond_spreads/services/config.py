"""Configuration for Bond Spreads feature.

Contains country/series ID mapping for FRED API.
"""

from features.bond_spreads.models.types import CountryConfig

# DynamoDB key prefix for this feature
DYNAMO_PK_PREFIX = "BS"

# S3 data path for this feature
S3_DATA_PREFIX = "data/bond-spreads"

# Country configurations with FRED series IDs
COUNTRIES: list[CountryConfig] = [
    CountryConfig(
        code="US",
        name="United States",
        currency="USD",
        flag="🇺🇸",
        series_10y="DGS10",  # US 10-Year Treasury Constant Maturity Rate
        series_3m="DTB3"     # US 3-Month Treasury Bill
    ),
    CountryConfig(
        code="DE",
        name="Germany",
        currency="EUR",
        flag="🇩🇪",
        series_10y="IRLTLT01DEM156N",  # Germany 10-Year
        series_3m="IR3TIB01DEM156N"    # Germany 3-Month
    ),
    CountryConfig(
        code="GB",
        name="United Kingdom",
        currency="GBP",
        flag="🇬🇧",
        series_10y="IRLTLT01GBM156N",  # UK 10-Year
        series_3m="IR3TIB01GBM156N"    # UK 3-Month
    ),
    CountryConfig(
        code="JP",
        name="Japan",
        currency="JPY",
        flag="🇯🇵",
        series_10y="IRLTLT01JPM156N",  # Japan 10-Year
        series_3m="IR3TIB01JPM156N"    # Japan 3-Month
    ),
    CountryConfig(
        code="FR",
        name="France",
        currency="EUR",
        flag="🇫🇷",
        series_10y="IRLTLT01FRM156N",  # France 10-Year
        series_3m="IR3TIB01FRM156N"    # France 3-Month
    ),
    CountryConfig(
        code="CA",
        name="Canada",
        currency="CAD",
        flag="🇨🇦",
        series_10y="IRLTLT01CAM156N",  # Canada 10-Year
        series_3m="IR3TIB01CAM156N"    # Canada 3-Month
    ),
    CountryConfig(
        code="AU",
        name="Australia",
        currency="AUD",
        flag="🇦🇺",
        series_10y="IRLTLT01AUM156N",  # Australia 10-Year
        series_3m="IR3TIB01AUM156N"    # Australia 3-Month
    ),
    # Brazil removed: FRED doesn't have OECD-format long-term bond yield data for Brazil
    # (not an OECD member, only has treasury bill data: INTGSTBRM193N)
    CountryConfig(
        code="IN",
        name="India",
        currency="INR",
        flag="🇮🇳",
        series_10y="INDIRLTLT01STM",  # India 10-Year (OECD format different for non-members)
        series_3m="INDIR3TIB01STM"    # India 3-Month (OECD format different for non-members)
    ),
    CountryConfig(
        code="MX",
        name="Mexico",
        currency="MXN",
        flag="🇲🇽",
        series_10y="IRLTLT01MXM156N",  # Mexico 10-Year
        series_3m="IR3TIB01MXM156N"    # Mexico 3-Month
    ),
]
