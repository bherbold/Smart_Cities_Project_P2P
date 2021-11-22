import Household_APS

class Bidders (object):
    householdName = None  # name of household
    energy_balance_t = None  # if positive -> more power than needed
    energy_transanction_p2p = None  # traded energy in p2p -> if negative energy was sold, if positive, energy was bought
    energy_transaction_grid = None  # traded energy with grid -> if negative energy was sold, if positive, energy was bought
    clearing_price_p2p = []  # price of household
    clearing_price_grid_buy = None  # price to buy power from grid for each household
    clearing_price_sell_grid = None  # price household gets to sell to grid
    previous_p2p_bid_est = None
    clearing_price_p2p_estimate_t = None  # estimated clearing price based on RLS
    learning_RLS = None # adjustment rate to previous bid
    selling_PV = False
    bill = 0 # cost: if negative: more income than costs
    ave_clearing_price = None# average of all clearing prices (for calculation of RLS)
    demand_house_t = None  # should be an array with 24h entries
    supply_house_t = None  # should be an array with 24h entries

    def __init__(self, name, clearing_price_grid_buy, clearing_price_sell_grid):
        self.householdName = name  # name of household
        self.energy_balance_t = None  # if positive -> more power than needed
        self.energy_transanction_p2p = 0 # traded energy in p2p -> if negative energy was sold, if positive, energy was bought
        self.energy_transaction_grid = 0 # traded energy with grid -> if negative energy was sold, if positive, energy was bought
        self.clearing_price_p2p = [] # price of household
        self.clearing_price_grid_buy = clearing_price_grid_buy # price to buy power from grid for each household
        self.clearing_price_sell_grid = clearing_price_sell_grid # price household gets to sell to grid
        self.previous_p2p_bid_est = (self.clearing_price_grid_buy + self.clearing_price_sell_grid)/2 # here initial price is half of price span (will be changed)
        self.clearing_price_p2p_estimate_t = None; # estimated clearing price based on RLS
        self.learning_RLS = 0.2; # default 0.5, can be changed
        self.ave_clearing_price = None # average of all clearing prices (for calculation of RLS)

    """def __init__(self, Household_APS=Household_APS):
        householdName = Household_APS.householdName  # name of household
        energy_balance_t = 0  # if positive -> more power than needed
        energy_transanction_p2p = 0  # traded energy in p2p -> if negative energy was sold, if positive, energy was bought
        energy_transaction_grid_t = 0  # traded energy with grid -> if negative energy was sold, if positive, energy was bought
        clearing_price_p2p_t = None  # price of household
        clearing_price_grid_buy = Household_APS.grid_selling_price # price to buy power from grid for each household
        clearing_price_sell_grid = Household_APS.grid_buying_price  # price household gets to sell to grid
        previous_p2p_bid_est = (clearing_price_grid_buy - clearing_price_sell_grid) / 2
        clearing_price_p2p_estimate_t = None;  # estimated clearing price based on RLS
        self.learning_RLS = Household_APS.learning_APS"""

    def __repr__(self):
       # return str(self.householdName , " Balance: ", str(self.energy_balance_t))

       # letsString = str(self.householdName), " balance: ", str(abs(self.energy_balance_t)), " pricing: ", str(self.clearing_price_p2p_estimate_t)

        return str(self.householdName)