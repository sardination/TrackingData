"""
Data utils - already exists?
"""
import unidecode

def remove_accents(string):
    return unidecode.unidecode(string)


def plot_bivariate_normal(mu, cov, figax, nsigma=1, lt='ko'):
    mu_X, mu_Y = mu
    cov_X, cov_Y = cov
    matplotlib.mlab.bivariate_normal(
        X,
        Y,
        sigmax=math.sqrt(cov_X),
        sigmay=math.sqrt(cov_Y),
        mux=mu_X,
        muy=mu_Y
    )

    fig, ax = figax

