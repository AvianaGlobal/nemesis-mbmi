import numpy as np


def auto_bin(x, method=None):
    """ Use heuristics to determine the bin size for a data set.
    
    Parameters
    ----------
    x : array_like
        Input data.
    
    method : str, optional (default = 'rice')
        The bining method to use.
        
        Supported methods are:
            'sqrt' : Square-root choice (Excel default)
            'sturges' : Sturges' formula (R default)
            'rice' : Rice rule
            'fd': Freedman-Diaconis' choice
    
    Returns:
    --------
    The number of bins, a positive integer.
        
    References
    ----------
    http://en.wikipedia.org/wiki/Histogram#Number_of_bins_and_width
    """
    # Pre-process the data.
    x = np.asarray(x)
    x = x[~np.isnan(x)] # Remove NaNs
    
    # Handle degenerate cases.
    n = len(x)
    if n == 0:
        return 1

    # Compute the number of bins.
    cbrt = lambda t: np.power(t, 1./3.)
    if method is None:
        method = 'rice'
    if method == 'sqrt':
        k = np.sqrt(n)
    elif method == 'sturges':
        k = np.log2(n) + 1
    elif method == 'rice':
        k = 2 * cbrt(n)
    elif method == 'fd':
        q0, q25, q75, q100 = np.percentile(x, [0, 25, 75, 100])
        if len(np.unique([q0, q25, q75, q100])) == 4:
            h = 2 * (q75 - q25) / cbrt(n)
            k = (q100 - q0) / h
        else:
            # If there aren't distinct quartiles, fall back to Rice.
            k = 2 * cbrt(n)
    else:
        raise ValueError('Unknown binning method %r' % method)
    return int(np.ceil(k))


def auto_histogram(x, method=None, density=None):
    """ Compute the histogram of a data set with automatic binning.
    
    Parameters
    ----------
    x : array_like
        Input data.
    
    method : str, optional
        The bining method to use. See ``auto_bin()``.
    
    density : bool, optional (default = False)
        Whether to compute a probability density. See ``np.histogram()``.
    
    Returns
    -------
    A tuple of the same form as ``np.histogram()``.
    """
    # Pre-process the data.
    x = np.asarray(x)
    x = x[~np.isnan(x)] # Remove NaNs
    
    # Compute the histogram.
    bins = auto_bin(x, method=method)
    return np.histogram(x, bins=bins, density=density)
