class Household_APS(object):
    """
    This class models one household's behavior (especially supply and demand of electricity)
    """

    householdName = None # name of household
    demand_house_t = None # should be an array with 24h entries
    supply_house_t = None # should be an array with 24h entries
    grid_selling_price = 0.00008
    grid_buying_price = 0.0003
    learning_RLS = 0.5 # default learning to RLS

    def __init__(self, name):
        self.householdName = name

    def __init__(self, name, demand, supply):
        self.householdName = name
        self.demand_house_t = demand
        self.supply_house_t = supply
