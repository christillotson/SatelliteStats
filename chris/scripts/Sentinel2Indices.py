"""
Sentinel-2 Spectral Index Functions
=====================================
Band order (11 bands, no B08 or B10):
  B1   - 443 nm  - Coastal Aerosol
  B2   - 490 nm  - Blue
  B3   - 560 nm  - Green
  B4   - 665 nm  - Red
  B5   - 705 nm  - Red Edge 1
  B6   - 740 nm  - Red Edge 2
  B7   - 783 nm  - Red Edge 3
  B8A  - 865 nm  - NIR (Narrow) — used as NIR throughout
  B9   - 940 nm  - Water Vapour
  B11  - 1610 nm - SWIR 1
  B12  - 2190 nm - SWIR 2

All reflectance values are expected in the range [0, 1].
"""

EPSILON = 1e-10


# ---------------------------------------------------------------------------
# Land Vegetation Indices
# ---------------------------------------------------------------------------

def ndvi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Difference Vegetation Index. (NIR - Red) / (NIR + Red)"""
    return (B8A - B4) / (B8A + B4 + EPSILON)


def evi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Enhanced Vegetation Index. 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)"""
    return 2.5 * (B8A - B4) / (B8A + 6 * B4 - 7.5 * B2 + 1 + EPSILON)


def savi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Soil-Adjusted Vegetation Index. ((NIR - Red) / (NIR + Red + L)) * (1 + L)"""
    L = 0.5
    return ((B8A - B4) / (B8A + B4 + L + EPSILON)) * (1 + L)


def msavi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Modified Soil-Adjusted Vegetation Index."""
    return (2 * B8A + 1 - ((2 * B8A + 1) ** 2 - 8 * (B8A - B4)) ** 0.5) / 2

def reci(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Red Edge Chlorophyll Index. (NIR / RedEdge1) - 1"""
    return (B8A / (B5 + EPSILON)) - 1


def cire(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Chlorophyll Index Red Edge. (RedEdge2 / RedEdge1) - 1"""
    return (B6 / (B5 + EPSILON)) - 1


def gndvi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Green NDVI. (NIR - Green) / (NIR + Green)"""
    return (B8A - B3) / (B8A + B3 + EPSILON)


# ---------------------------------------------------------------------------
# Water / Moisture Indices
# ---------------------------------------------------------------------------

def ndwi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Difference Water Index. (Green - NIR) / (Green + NIR)"""
    return (B3 - B8A) / (B3 + B8A + EPSILON)


def mndwi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Modified NDWI. (Green - SWIR1) / (Green + SWIR1)"""
    return (B3 - B11) / (B3 + B11 + EPSILON)


def ndmi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Difference Moisture Index. (NIR - SWIR1) / (NIR + SWIR1)"""
    return (B8A - B11) / (B8A + B11 + EPSILON)


# ---------------------------------------------------------------------------
# Fire / Burn Indices
# ---------------------------------------------------------------------------

def nbr(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Burn Ratio. (NIR - SWIR2) / (NIR + SWIR2)"""
    return (B8A - B12) / (B8A + B12 + EPSILON)


def nbr2(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Burn Ratio 2. (SWIR1 - SWIR2) / (SWIR1 + SWIR2)"""
    return (B11 - B12) / (B11 + B12 + EPSILON)


# ---------------------------------------------------------------------------
# Urban / Bare Soil Indices
# ---------------------------------------------------------------------------

def ndbi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Difference Built-up Index. (SWIR1 - NIR) / (SWIR1 + NIR)"""
    return (B11 - B8A) / (B11 + B8A + EPSILON)


def bsi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Bare Soil Index. ((SWIR1 + Red) - (NIR + Blue)) / ((SWIR1 + Red) + (NIR + Blue))"""
    return ((B11 + B4) - (B8A + B2)) / ((B11 + B4) + (B8A + B2) + EPSILON)


def ui(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Urban Index. (SWIR2 - NIR) / (SWIR2 + NIR)"""
    return (B12 - B8A) / (B12 + B8A + EPSILON)


# ---------------------------------------------------------------------------
# Snow / Other
# ---------------------------------------------------------------------------

def ndsi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Difference Snow Index. (Green - SWIR1) / (Green + SWIR1)"""
    return (B3 - B11) / (B3 + B11 + EPSILON)


def ri(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Redness Index. Red / Blue"""
    return B4 / (B2 + EPSILON)


# ---------------------------------------------------------------------------
# Water vegetation
# ---------------------------------------------------------------------------

def fai(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Floating Algae Index. NIR - (Red + (SWIR1 - Red) * baseline_slope)
    Isolates floating vegetation against water background."""
    baseline = B4 + (B11 - B4) * (0.8 / 1.6)  # wavelength interpolation ~833nm between 665 and 1610
    return B8A - baseline

def ndre(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Difference Red Edge. (NIR - RedEdge) / (NIR + RedEdge)
    More sensitive than NDVI at low chlorophyll concentrations."""
    return (B8A - B5) / (B8A + B5 + EPSILON)

def rededge_chlorophyll(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Red Edge Chlorophyll Index. (NIR / RedEdge) - 1
    Correlates well with chlorophyll content in algae and aquatic plants."""
    return (B8A / (B5 + EPSILON)) - 1

def ndwi_aquatic(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Difference Water Index. (Green - NIR) / (Green + NIR)
    Highlights water surface; floating vegetation will deviate positively from open water."""
    return (B3 - B8A) / (B3 + B8A + EPSILON)

def ci_green(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Green Chlorophyll Index. (NIR / Green) - 1
    Widely used for chlorophyll-a estimation in water bodies."""
    return (B8A / (B3 + EPSILON)) - 1

def ndci(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12) -> float:
    """Normalized Difference Chlorophyll Index. (RedEdge - Red) / (RedEdge + Red)
    Specifically developed for phytoplankton chlorophyll in coastal/inland water."""
    return (B5 - B4) / (B5 + B4 + EPSILON)

# ---------------------------------------------------------------------------
# Master list
# ---------------------------------------------------------------------------

INDICES = [
    ndvi, evi, savi, msavi,
    reci, cire, gndvi,
    ndwi, mndwi, ndmi,
    nbr, nbr2,
    ndbi, bsi, ui,
    ndsi, ri,
    fai, ndre, rededge_chlorophyll, ndwi_aquatic, ci_green, ndci
]