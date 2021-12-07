class Household_APS(object):
    """
    This class models one household's behavior (especially supply and demand of electricity)
    """

    householdName = None # name of household
    balance_house_t = None # should be an array with 24h entries
    grid_selling_price = 0.00003 # per Wh. Swedish price = 0.03€/kWh
    grid_buying_price = 0.00018 # per Wh. Swedish price = 0.18€/kWh
    learning_RLS = 0.5 # default learning to RLS

    def __init__(self, name):
        self.householdName = name

    def __init__(self, name, balance):
        self.householdName = name
        self.balance_house_t = balance
