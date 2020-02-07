import numpy as np


def is_discrete(x):
    """ Use heuristics to guess whether a data set is discrete or continuous.
    
    The simple heuristic used below was arrived at in the following way.
    Using the ``readMLData`` R package, I downloaded ~90 data sets from the 
    UCI Machine Learning Repository, along with metadata describing their
    ~2600 columns. Using as features 'n', the length of the column, and 
    'unique', the number of unique values in the column, I used logistic 
    regression to classify the column as categorical or numerical.
    
    It turns out that the regressed coefficient for 'n' is very small and not
    statistically significant, so I dropped 'n' altogether to obtain the 
    following extremely simple linear decision boundary. The 10-fold
    cross-validation error rate with this rule is ~7.5%.
    
    I also briefly explored some nonlinear methods (SVMs), but I think it is 
    doubtful that one can do much better than this simple rule without
    overfitting the data. However, one probably could do better by improving
    the feature set. I have not explored any features that depend on the
    *coding* of the categorical variable as an integer. For example, one might
    consider the spread of column values or conformance with Benford's law.
    """
    # First dispatch on data type, if possible.
    x = np.asarray(x)
    if not x.dtype.kind in 'iufc': # (signed, unsigned, float, complex)
        return True
    elif not np.all(x.real.astype('i') == x):
        return False
    
    # At this point, we have an array of integers. Invoke the logisitic 
    # regression decision rule.
    unique = np.unique(x)
    return len(unique) <= 12