# estimate clearing price (bid from household with electricity demand) by using an recrusive least square RLS model

def rls(learning, c_n_g_t_est, c_n_g_t):
    """
    Calculating the estimated clearing price for the bidder (household who buys energy)
    :param c_n_g: estimated price for period t+1
    :param learning: learning factor from household n (between 0-1)
    :param c_n_g_t_est: estimated clearing price from t period (before)
    :param c_n_g_t: actual clearing price from period 1 (before)
    :return: estimated clearing price from bidder
    """
    print(learning)
    print(c_n_g_t)
    print(c_n_g_t_est)
    c_n_g = c_n_g_t_est + learning * (c_n_g_t - c_n_g_t_est)

    return c_n_g

