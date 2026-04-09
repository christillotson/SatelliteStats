"""
Sentinel-2 Spectral Index Functions
=====================================
Each function accepts all 13 Sentinel-2 band values for a single pixel
and returns the computed index value as a float.

Band order and approximate wavelengths:
  B1   - 443 nm  - Coastal Aerosol
  B2   - 490 nm  - Blue
  B3   - 560 nm  - Green
  B4   - 665 nm  - Red
  B5   - 705 nm  - Red Edge 1
  B6   - 740 nm  - Red Edge 2
  B7   - 783 nm  - Red Edge 3
  B8   - 842 nm  - NIR (Broad)
  B8A  - 865 nm  - NIR (Narrow)
  B9   - 940 nm  - Water Vapour
  B10  - 1375 nm - SWIR Cirrus
  B11  - 1610 nm - SWIR 1
  B12  - 2190 nm - SWIR 2

All reflectance values are expected in the range [0, 1].
A small epsilon is used in denominators to avoid division by zero.
"""

EPSILON = 1e-10


# ---------------------------------------------------------------------------
# Vegetation Indices
# ---------------------------------------------------------------------------

def ndvi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Normalized Difference Vegetation Index
    Healthy vegetation: ~0.6–0.9 | Bare soil: ~0.1 | Water: < 0
    Formula: (NIR - Red) / (NIR + Red)
    """
    return (B8 - B4) / (B8 + B4 + EPSILON)


def evi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Enhanced Vegetation Index
    Reduces atmospheric and soil background noise vs NDVI.
    Formula: 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)
    """
    return 2.5 * (B8 - B4) / (B8 + 6 * B4 - 7.5 * B2 + 1 + EPSILON)


def savi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Soil-Adjusted Vegetation Index
    Minimises soil brightness influence. L=0.5 (intermediate cover).
    Formula: ((NIR - Red) / (NIR + Red + L)) * (1 + L)
    """
    L = 0.5
    return ((B8 - B4) / (B8 + B4 + L + EPSILON)) * (1 + L)


def ndre(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Normalized Difference Red Edge
    Sensitive to chlorophyll content; better than NDVI for dense canopies.
    Formula: (NIR - RedEdge1) / (NIR + RedEdge1)
    """
    return (B8 - B5) / (B8 + B5 + EPSILON)


def reci(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Red Edge Chlorophyll Index
    Estimates canopy chlorophyll content.
    Formula: (NIR / RedEdge1) - 1
    """
    return (B8 / (B5 + EPSILON)) - 1


def cire(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Chlorophyll Index Red Edge
    Uses Red Edge 2 & Red Edge 1; good for leaf chlorophyll.
    Formula: (RedEdge2 / RedEdge1) - 1
    """
    return (B6 / (B5 + EPSILON)) - 1


def gndvi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Green Normalized Difference Vegetation Index
    More sensitive to chlorophyll concentration than NDVI.
    Formula: (NIR - Green) / (NIR + Green)
    """
    return (B8 - B3) / (B8 + B3 + EPSILON)


def msavi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Modified Soil-Adjusted Vegetation Index
    Self-adjusting L factor reduces soil noise without needing to specify L.
    Formula: (2*NIR + 1 - sqrt((2*NIR + 1)^2 - 8*(NIR - Red))) / 2
    """
    return (2 * B8 + 1 - ((2 * B8 + 1) ** 2 - 8 * (B8 - B4)) ** 0.5) / 2


# ---------------------------------------------------------------------------
# Water / Moisture Indices
# ---------------------------------------------------------------------------

def ndwi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Normalized Difference Water Index (Gao 1996)
    Detects open water bodies. Water > 0.
    Formula: (Green - NIR) / (Green + NIR)
    """
    return (B3 - B8) / (B3 + B8 + EPSILON)


def mndwi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Modified Normalized Difference Water Index (Xu 2006)
    Suppresses built-up land noise better than NDWI. Water > 0.
    Formula: (Green - SWIR1) / (Green + SWIR1)
    """
    return (B3 - B11) / (B3 + B11 + EPSILON)


def ndmi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Normalized Difference Moisture Index
    Measures vegetation water content / canopy moisture stress.
    Formula: (NIR - SWIR1) / (NIR + SWIR1)
    """
    return (B8 - B11) / (B8 + B11 + EPSILON)


# ---------------------------------------------------------------------------
# Fire / Burn Indices
# ---------------------------------------------------------------------------

def nbr(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Normalized Burn Ratio
    Detects burned areas and burn severity. Low/negative = burned.
    Formula: (NIR - SWIR2) / (NIR + SWIR2)
    """
    return (B8 - B12) / (B8 + B12 + EPSILON)


def nbr2(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Normalized Burn Ratio 2
    Highlights post-fire recovery using both SWIR bands.
    Formula: (SWIR1 - SWIR2) / (SWIR1 + SWIR2)
    """
    return (B11 - B12) / (B11 + B12 + EPSILON)


# ---------------------------------------------------------------------------
# Urban / Bare Soil Indices
# ---------------------------------------------------------------------------

def ndbi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Normalized Difference Built-up Index
    Highlights urban/built-up areas. Built-up > 0.
    Formula: (SWIR1 - NIR) / (SWIR1 + NIR)
    """
    return (B11 - B8) / (B11 + B8 + EPSILON)


def bsi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Bare Soil Index
    Distinguishes bare soil from vegetated surfaces.
    Formula: ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))
    """
    return ((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2) + EPSILON)


def ui(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Urban Index
    Highlights impervious urban surfaces using SWIR2 and NIR.
    Formula: (SWIR2 - NIR) / (SWIR2 + NIR)
    """
    return (B12 - B8) / (B12 + B8 + EPSILON)


# ---------------------------------------------------------------------------
# Snow / Ice Indices
# ---------------------------------------------------------------------------

def ndsi(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Normalized Difference Snow Index
    Separates snow/ice from clouds and land. Snow > 0.4.
    Formula: (Green - SWIR1) / (Green + SWIR1)
    """
    return (B3 - B11) / (B3 + B11 + EPSILON)


# ---------------------------------------------------------------------------
# Aerosol / Atmospheric Indices
# ---------------------------------------------------------------------------

def ri(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Redness Index (Iron Oxide / Ferric Iron proxy)
    Highlights iron-oxide-rich soils and geological features.
    Formula: Red / Blue
    """
    return B4 / (B2 + EPSILON)


def ci(B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B10, B11, B12) -> float:
    """
    Cirrus Index
    Uses the cirrus band (B10) to flag cloud contamination.
    Formula: B10 / (B2 + EPSILON)   (high values = cirrus cloud likely present)
    """
    return B10 / (B2 + EPSILON)


# ---------------------------------------------------------------------------
# Master list — iterate over this to compute all indices for a pixel
# ---------------------------------------------------------------------------

INDICES = [
    ndvi,
    evi,
    savi,
    ndre,
    reci,
    cire,
    gndvi,
    msavi,
    ndwi,
    mndwi,
    ndmi,
    nbr,
    nbr2,
    ndbi,
    bsi,
    ui,
    ndsi,
    ri,
    ci,
]