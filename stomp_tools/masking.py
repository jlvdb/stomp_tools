import numpy as np
import stomp


def adapt_mask(RA, DEC, resolution):
    """
    Adapt a STOMP pixel mask from a vector of right ascensions and declinations
    at a given mask resolution. Creates new pixel for each position until
    all objects are covered.

    Parameters
    ----------
    RA : array_like
        List of right ascensions in degrees.
    DEC : array_like
        List of declinations in degrees.
    resolution : int
        Mask resolution (powers of 2 between 2 and 32768).

    Returns
    -------
    mask : stomp.Map
        STOMP pixel mask derived from the input data geometry.
    """
    assert(len(RA) == len(DEC))
    # create pixels for each object and convert them into a pixel map
    pix_vect = stomp.PixelVector()
    iterator = zip(
        np.asarray(RA, dtype=np.double),
        np.asarray(DEC, dtype=np.double))
    for RA, DEC in iterator:
        ang = stomp.AngularCoordinate(
            RA, DEC, stomp.AngularCoordinate.Equatorial)
        pix_vect.push_back(stomp.Pixel(ang, resolution, 1.0))
    # create the final map
    mask = stomp.Map()
    mask.IngestMap(pix_vect)
    return mask


def apply_mask(RA, DEC, map_path):
    """
    Adapt a STOMP pixel mask from a vector of right ascensions and declinations
    at a given mask resolution. Creates new pixel for each position until
    all objects are covered.

    Parameters
    ----------
    RA : array_like
        List of right ascensions in degrees.
    DEC : array_like
        List of declinations in degrees.
    map_path : string
        Stomp map file path to load from. The map cannot be parsed as object
        because objects wrapped with SWIG cannot be pickled, however this
        function must support multiprocessing.

    Returns
    -------
    mask : array_like of bools
        Boolean mask indicated whether an input object lies within the mask
        footprint.
    """
    assert(len(RA) == len(DEC))
    smap = stomp.Map(map_path)
    # check if objects fall within the mask
    mask = np.empty(len(RA), dtype="bool")
    iterator = zip(
        np.asarray(RA, dtype=np.double),
        np.asarray(DEC, dtype=np.double))
    for i, (ra, dec) in enumerate(iterator):
        new_obj = stomp.WeightedAngularCoordinate(
            ra, dec, 1.0, stomp.AngularCoordinate.Equatorial)
        mask[i] = smap.Contains(new_obj)
    return mask
