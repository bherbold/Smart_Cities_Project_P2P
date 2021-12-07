class Household_APS(object):
    """
    This class models one household's behavior (especially supply and demand of electricity)
    """

    householdName = None # name of household
    balance_house_t = None # should be an array with 24h entries
    grid_selling_price = 0.00008
    grid_buying_price = 0.0003
    learning_RLS = 0.5 # default learning to RLS

    def __init__(self, name):
        self.householdName = name

    def __init__(self, name, balance):
        self.householdName = name
        self.balance_house_t = balance
