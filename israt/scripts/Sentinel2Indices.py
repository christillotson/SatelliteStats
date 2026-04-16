"""
Sentinel-2 Spectral Index Functions
===================================

Band order expected by all functions:
  B01 - Coastal Aerosol
  B02 - Blue
  B03 - Green
  B04 - Red
  B05 - Red Edge 1
  B06 - Red Edge 2
  B07 - Red Edge 3
  B8A - Narrow NIR
  B09 - Water Vapour
  B11 - SWIR 1
  B12 - SWIR 2

All reflectance values should be float values in the range [0, 1].
"""

EPSILON = 1e-10


def ndvi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B8A - B4) / (B8A + B4 + EPSILON)


def evi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return 2.5 * (B8A - B4) / (B8A + 6 * B4 - 7.5 * B2 + 1 + EPSILON)


def savi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    L = 0.5
    return ((B8A - B4) / (B8A + B4 + L + EPSILON)) * (1 + L)


def msavi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (2 * B8A + 1 - ((2 * B8A + 1) ** 2 - 8 * (B8A - B4)) ** 0.5) / 2


def ndre(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B8A - B5) / (B8A + B5 + EPSILON)


def reci(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B8A / (B5 + EPSILON)) - 1


def cire(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B6 / (B5 + EPSILON)) - 1


def gndvi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B8A - B3) / (B8A + B3 + EPSILON)


def ndwi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B3 - B8A) / (B3 + B8A + EPSILON)


def mndwi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B3 - B11) / (B3 + B11 + EPSILON)


def ndmi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B8A - B11) / (B8A + B11 + EPSILON)


def nbr(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B8A - B12) / (B8A + B12 + EPSILON)


def nbr2(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B11 - B12) / (B11 + B12 + EPSILON)


def ndbi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B11 - B8A) / (B11 + B8A + EPSILON)


def bsi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return ((B11 + B4) - (B8A + B2)) / ((B11 + B4) + (B8A + B2) + EPSILON)


def ui(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B12 - B8A) / (B12 + B8A + EPSILON)


def ndsi(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return (B3 - B11) / (B3 + B11 + EPSILON)


def ri(B1, B2, B3, B4, B5, B6, B7, B8A, B9, B11, B12):
    return B4 / (B2 + EPSILON)


INDICES = [
    ndvi, evi, savi, msavi,
    ndre, reci, cire, gndvi,
    ndwi, mndwi, ndmi,
    nbr, nbr2,
    ndbi, bsi, ui,
    ndsi, ri,
]
