import numpy as np
import pandas as pd
import stomp


def generate_randoms(mask_path, n_randoms):
    """
    Generate a sample of uniformly distributed objects on a STOMP mask.

    Parameters
    ----------
    mask_path : str
        File path of STOMP mask.
    n_randoms : int
        Number of random points to generate.

    Returns
    -------
    area : pandas.DataFrame
        Data frame with columns RA (right ascension, in degrees) and DEC
        (declination, in degrees) of the random objects.
    """
    # use the stomp methods to generate uniform random points
    stomp_map = stomp.Map(mask_path)
    random_vector = stomp.AngularVector()
    stomp_map.GenerateRandomPoints(random_vector, int(n_randoms))
    # convert to numpy array
    RA = np.asarray([rand.RA() for rand in random_vector.iterator()])
    DEC = np.asarray([rand.DEC() for rand in random_vector.iterator()])
    randoms = pd.DataFrame({"RA": RA, "DEC": DEC})
    del stomp_map, random_vector
    return randoms
