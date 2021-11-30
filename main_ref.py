import RLS
import Household_APS
import Bidders
import Clearing_price
import operator
from random import randint
import csv
from datetime import datetime

header = ['period', 'name', 'bill', 'energy_balance', 'ave_clearing_price', 'pv_supply', 'demand_load', 'transactions', 'clearing est now', 'clearing price est before']
# open the file in the write mode
with open('example_clearing_ref.csv', 'w', encoding='UTF8', newline='') as f:


    # create the csv writer
    writer = csv.writer(f)

    # write a row to the csv file
    writer.writerow(header)

# close the file
# f.close()

pv_prod_HH = []
load_HH = []
with open('Hamburg_Juli_2021_pleasemultiplyby4.csv', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        if row[6] == "Solar Production":
            continue
        else:
            pv_prod_HH.append(float(row[6]))

        if row[6] == "Household Load":
            continue
        else:
            load_HH.append(float(row[7]))
        #print(row[6])
print("PV Prod loaded: ", pv_prod_HH)
"""
TODO: sorting of bidders
"""

print("PLS: ",RLS.rls(0.5,2,1))

house1 = Household_APS.Household_APS("H1", 1, 5)
house2 = Household_APS.Household_APS("H2", 4, 18)
house3 = Household_APS.Household_APS("H3", 3, 0)
house4 = Household_APS.Household_APS("H4", 3, 0)
house4.grid_selling_price = 0.00012
households_test = [house1, house2, house3, house4]

def clearing (bidders_t_minus_1, households_t):
    """
    real_clearing_price_t_minus_1 needs to be substituted with a list of the participants from before to calculate each
    previuos price
    """

    bidders = []
    seller_PV = [] # list of PV sellers
    buying_PV = [] # list of PV buyers
    grid_balance = 0 # all balances added. If positive: more PV than demand
    pv_surplus = 0;
    # Determine bids of household using RLS
    for house in households_t:
        # print(type(house))
        # house_bidder = Bidders.Bidders(house)
        # find_old_clearing(house,bidders_t_minus_1)
        house_bidder = Bidders.Bidders(house.householdName,house.grid_buying_price,house.grid_selling_price)
        house_bidder.energy_balance_t = round(house.supply_house_t - house.demand_house_t)
        house_bidder.demand_house_t = house.demand_house_t
        house_bidder.supply_house_t = house.supply_house_t
        grid_balance += house_bidder.energy_balance_t
        # house_bidder.clearing_price_grid_buy = house.grid_buying_price # price to buy power from grid for each household
        # house_bidder.clearing_price_sell_grid = house.grid_selling_price # price household gets to sell to grid
        # ave_clear_t_m_1 = ave_clearing_t_minus_1(house_bidder)
        if (isinstance(bidders_t_minus_1, float)):
            clearing_est_t = RLS.rls(house_bidder.learning_RLS, house_bidder.previous_p2p_bid_est,
                                     bidders_t_minus_1)
            print("TEST: ", clearing_est_t)
            print("Learning: ", house_bidder.learning_RLS)
            print("house_bidder.previous_p2p_bid_est: ", house_bidder.previous_p2p_bid_est)
            print("Bidder_t_minus_1: ", bidders_t_minus_1)
        else:
            clearing_est_t = RLS.rls(house_bidder.learning_RLS, find_previous_est (house, bidders_t_minus_1), find_old_clearing(house,bidders_t_minus_1))
            """if clearing_est_t > house_bidder.clearing_price_grid_buy:
                clearing_est_t = house_bidder.clearing_price_grid_buy
            elif clearing_est_t < house_bidder.clearing_price_sell_grid:
                clearing_est_t = house_bidder.clearing_price_sell_grid"""

        house_bidder.clearing_price_p2p_estimate_t = clearing_est_t
        print("preavius est. from " , house_bidder, ": ", house_bidder.previous_p2p_bid_est)
        print("est. clearing price from ", house_bidder, ": ", house_bidder.clearing_price_p2p_estimate_t)
        bidders.append(house_bidder)
        house_bidder.previous_p2p_bid_est = clearing_est_t
        print("Household has been added. new bidders: " , bidders, " Grid balance: ", grid_balance)
        if(house_bidder.energy_balance_t > 0):
            house_bidder.selling_PV = True
            seller_PV.append(house_bidder)
            pv_surplus += house_bidder.energy_balance_t
        else:
            buying_PV.append(house_bidder)
    if(grid_balance == 0):

        sorted_bidders_price = sorted(bidders, key=lambda  x: x.clearing_price_p2p_estimate_t, reverse = True)
        clearing_price_t = sorted_bidders_price[0].clearing_price_p2p_estimate_t

        offers_allocation = sort_seller_too_much_PV(seller_PV)
        """offers_allocation = sorted(sorted(seller_PV, key=lambda  x: x.clearing_price_p2p_estimate_t , reverse = True), key = lambda x: x.energy_balance_t, reverse = True)# selling PV"""
        bids_allocation = sort_buyers_P2P(buying_PV)
        """bids_allocation = sorted(sorted(buying_PV, key=lambda  x: x.clearing_price_p2p_estimate_t, reverse = True), key = lambda x: x.energy_balance_t, reverse = False) # selling PV"""
        grid_balance_allocation = pv_surplus #power will be assigned to highest bidder
        priced_list = []
        for seller in offers_allocation:
            # seller.clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, -seller.energy_balance_t, None])
            # seller_clearing_price = clearing_price_t
            allo_buyers = allocate_buyers(seller, bids_allocation )

            if(seller.energy_balance_t >= 0): # sells energy
                #seller prizing
                seller.bill = -(seller.clearing_price_p2p_estimate_t * max(0,seller.energy_balance_t))
                print(seller, " PRICE of seller: ", seller.clearing_price_p2p_estimate_t)
                print(seller, " bill of seller: ", seller.bill)
                # grid_balance_allocation -= seller.energy_balance_t

                #buyers pricing
                for buyer in allo_buyers:
                    buyer[0].clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, buyer[1],buyer[2]])
                    seller.clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, -buyer[1], buyer[0]])
                    print("buying prices: ", buyer[0].clearing_price_p2p)
                    buyer[0].energy_balance_t -= buyer[1]
                    buyer[0].bill += (seller.clearing_price_p2p_estimate_t * buyer[1])

            priced_list.append(seller)
            """elif(seller.energy_balance_t < 0): # buys energy
                buying_p2p = min(grid_balance_allocation, -(seller.energy_balance_t))
                buying_grid = -(seller.energy_balance_t) - buying_p2p
                seller.bill = (buying_p2p*clearing_price_t + buying_grid*seller.clearing_price_grid_buy)
                #grid_balance_allocation += bidder.energy_balance_t
                print(seller , " bill of buyer: ", seller.bill)"""

        return_list = priced_list + bids_allocation
        ave_clearing_t_minus_1(return_list)
        print("______________", return_list, "_____________")
        return return_list
    elif (grid_balance > 0):
        print("grid balance too much PV")
        sorted_bidders_price = sorted(bidders, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True)
        clearing_price_t = sorted_bidders_price[0].clearing_price_p2p_estimate_t
        print("Line 83: ", clearing_price_t)

        offers_allocation = sort_seller_too_much_PV(seller_PV)
        """offers_allocation = sorted(sorted(seller_PV, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True),
                                   key=lambda x: x.energy_balance_t, reverse=True)  # selling PV"""
        offers_allocation_new = sorted(sorted(seller_PV, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True),
                                   key=lambda x: x.energy_balance_t, reverse=True)  # selling PV
        bids_allocation = sort_buyers_P2P(buying_PV)
        """bids_allocation = sorted(sorted(buying_PV, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True),
                                 key=lambda x: x.energy_balance_t, reverse=False)  # s"""

        print("offers Allo: ", offers_allocation)
        print("Bids Allo", bids_allocation )
        print("Grid balance: ", grid_balance)
        # sold to the grid
        for seller in offers_allocation:
            print("Seller Balance: ", seller.energy_balance_t)
            if (seller.energy_balance_t >= grid_balance):
                seller.clearing_price_p2p.append([seller.clearing_price_sell_grid,-grid_balance, None])
                seller.bill -= grid_balance * seller.clearing_price_sell_grid
                print("____if Bill:", seller, seller.bill)
                print(grid_balance * seller.clearing_price_sell_grid)
                seller.energy_balance_t -= grid_balance
                grid_balance = 0
                print("_____ ", seller, " ", seller.clearing_price_p2p)
                # break
            elif(grid_balance == 0):
                break
            else:
                print("___ELSE of too little PV")
                seller.clearing_price_p2p.append([seller.clearing_price_sell_grid, -seller.energy_balance_t, None])
                seller.bill -= seller.energy_balance_t * seller.clearing_price_sell_grid
                print("ELSE Bill:" , seller, seller.bill)
                grid_balance -= seller.energy_balance_t
                seller.energy_balance_t = 0
                offers_allocation_new.remove(seller)
                bids_allocation.append(seller)


        # now P2P clearing
        return clearing_P2P(offers_allocation_new, bids_allocation)

    elif (grid_balance < 0):
        print("gridd has not enough PV")
        sorted_bidders_price = sorted(bidders, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True)
        clearing_price_t = sorted_bidders_price[0].clearing_price_p2p_estimate_t
        print("Line 83: ", clearing_price_t)
        offers_allocation = sorted(sorted(seller_PV, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True),
                                   key=lambda x: x.energy_balance_t, reverse=True)  # selling PV
        bids_allocation = sort_buyers_less_PV(buying_PV)
        """bids_allocation = sorted(buying_PV, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=False)# lowest load with lowest bid needs to pay the most
        for i in range(len(bids_allocation)-1):
            if (round(bids_allocation[i].clearing_price_p2p_estimate_t,6) == round(bids_allocation[i+1].clearing_price_p2p_estimate_t,6) ):
                if abs(bids_allocation[i].energy_balance_t) > abs(bids_allocation[i+1].energy_balance_t):
                    print("SWITCHING i for i+1")
                    temp = bids_allocation[i+1]
                    bids_allocation[i+1] = bids_allocation[i]
                    bids_allocation[i] = temp"""

        print("Bids Allo_test", bids_allocation)

        # consumers pricing -> price from grid
        # sold to the grid
        for buyer in bids_allocation:
            print("ENERGY_BANCE", buyer.energy_balance_t)
            print("GRID_BALANCE", grid_balance)
            print("BID: ", buyer.clearing_price_p2p_estimate_t)
            if (buyer.energy_balance_t <= grid_balance):
                buyer.clearing_price_p2p.append([buyer.clearing_price_grid_buy, -grid_balance, None])
                buyer.bill += -grid_balance * buyer.clearing_price_grid_buy
                buyer.energy_balance_t += -grid_balance
                grid_balance = 0
                print("_____ ",buyer, " ", buyer.energy_balance_t)
                break
            else:
                buyer.clearing_price_p2p.append([buyer.clearing_price_grid_buy, -buyer.energy_balance_t, None])
                buyer.bill += -buyer.energy_balance_t * buyer.clearing_price_grid_buy
                grid_balance += -buyer.energy_balance_t
                buyer.energy_balance_t = 0
                print("HHAAaaaaaallloooo")

        bids_allocation = sort_buyers_P2P(buying_PV)
        """bids_allocation = sorted(sorted(buying_PV, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True),
                                 key=lambda x: x.energy_balance_t,
                                 reverse=False)  # for the P2P network"""

        # now P2P clearing
        return clearing_P2P (offers_allocation, bids_allocation)

def allocate_buyers (seller, buyers):

    pv_overprod = seller.energy_balance_t
    allocation = []
    transaction = 0
    for buyer in buyers:
        if (pv_overprod >= -(buyer.energy_balance_t)):
            transaction += -buyer.energy_balance_t
            allocation.append([buyer,-buyer.energy_balance_t, seller])
            pv_overprod += buyer.energy_balance_t
            print("ALLOCATED", -buyer.energy_balance_t)
        else:
            transaction += pv_overprod
            pv_overprod = 0
            allocation.append([buyer, transaction, seller])
    print(seller, " sells to: ", allocation)
    return allocation

def ave_clearing_t_minus_1(bidders):

    for bidder in bidders:
        sum_prices = 0
        sum_consumption = 0
        for price in bidder.clearing_price_p2p:
            sum_prices += price[0] * abs(price[1])
            sum_consumption += abs(price[1])
        if(sum_consumption == 0 and (len(bidder.clearing_price_p2p) != 0)):
            bidder.ave_clearing_price = sum_prices / len(bidder.clearing_price_p2p)
        elif (sum_consumption == 0 and (len(bidder.clearing_price_p2p) == 0)):
            bidder.ave_clearing_price = (bidder.clearing_price_grid_buy + bidder.clearing_price_sell_grid)/2
        else :
            bidder.ave_clearing_price = sum_prices / sum_consumption
    return bidders

def find_old_clearing(house,bidders_t_minus_1):

    for bidder in bidders_t_minus_1:
        if (bidder.householdName == house.householdName):
            print("OLD clearing PRICE: ", bidder.ave_clearing_price)
            return bidder.ave_clearing_price

def find_previous_est (house, bidders_t_minus_1):

    for bidder in bidders_t_minus_1:
        if (bidder.householdName == house.householdName):
            print("previous est: ", bidder.previous_p2p_bid_est)
            return bidder.previous_p2p_bid_est

def sort_buyers_less_PV(buying_PV):
    bids_allocation = sorted(buying_PV, key=lambda x: x.clearing_price_p2p_estimate_t,
                             reverse=False)  # lowest load with lowest bid needs to pay the most
    for i in range(len(bids_allocation) - 1):
        if (round(bids_allocation[i].clearing_price_p2p_estimate_t, 6) == round(
                bids_allocation[i + 1].clearing_price_p2p_estimate_t, 6)):
            if abs(bids_allocation[i].energy_balance_t) > abs(bids_allocation[i + 1].energy_balance_t):
                print("SWITCHING i for i+1")
                temp = bids_allocation[i + 1]
                bids_allocation[i + 1] = bids_allocation[i]
                bids_allocation[i] = temp

    return bids_allocation


def sort_buyers_P2P(buying_PV):
    bids_allocation = sorted(buying_PV, key=lambda x: x.clearing_price_p2p_estimate_t,
                             reverse=True)
    for i in range(len(bids_allocation) - 1):
        if (round(bids_allocation[i].clearing_price_p2p_estimate_t, 6) == round(
                bids_allocation[i + 1].clearing_price_p2p_estimate_t, 6)):
            if abs(bids_allocation[i].energy_balance_t) < abs(bids_allocation[i + 1].energy_balance_t):
                print("SWITCHING i for i+1")
                temp = bids_allocation[i + 1]
                bids_allocation[i + 1] = bids_allocation[i]
                bids_allocation[i] = temp

    return bids_allocation
def sort_seller_too_much_PV(seller_PV):
    offers_allocation = sorted(seller_PV, key=lambda x: x.clearing_price_p2p_estimate_t,
                             reverse=True)  # lowest load with lowest bid needs to pay the most
    for i in range(len(offers_allocation) - 1):
        if (round(offers_allocation[i].clearing_price_p2p_estimate_t, 6) == round(
                offers_allocation[i + 1].clearing_price_p2p_estimate_t, 6)):
            if abs(offers_allocation[i].energy_balance_t) < abs(offers_allocation[i + 1].energy_balance_t):
                print("SWITCHING i for i+1")
                temp = offers_allocation[i + 1]
                offers_allocation[i + 1] = offers_allocation[i]
                offers_allocation[i] = temp

    return offers_allocation

def clearing_P2P (offers_allocation, bids_allocation):

    # clearing(real_clearing_price_t_minus_1, (offers_allocation + bids_allocation))
    priced_list = []
    for seller in offers_allocation:
        # seller.clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, -seller.energy_balance_t, None])
        # seller_clearing_price = clearing_price_t
        allo_buyers = allocate_buyers(seller, bids_allocation)
        print("allo_buyers: ", allo_buyers)

        if (seller.energy_balance_t >= 0):  # sells energy
            # seller prizing
            seller.bill = -(seller.clearing_price_p2p_estimate_t * max(0, seller.energy_balance_t))
            print(seller, " PRICE of seller: ", seller.clearing_price_p2p_estimate_t)
            print(seller, " bill of seller: ", seller.bill)
            # grid_balance_allocation -= bidder.energy_balance_t

            # buyers pricing
            for buyer in allo_buyers:
                print("THIS BUYER:", buyer[1])
                buyer[0].clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, buyer[1], buyer[2]])
                seller.clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, -buyer[1], buyer[0]])
                print("buying prices: ", buyer[0].clearing_price_p2p)
                buyer[0].energy_balance_t -= buyer[1]
                buyer[0].bill += (seller.clearing_price_p2p_estimate_t * buyer[1])

        priced_list.append(seller)
        """elif(seller.energy_balance_t < 0): # buys energy
            buying_p2p = min(grid_balance_allocation, -(seller.energy_balance_t))
            buying_grid = -(seller.energy_balance_t) - buying_p2p
            seller.bill = (buying_p2p*clearing_price_t + buying_grid*seller.clearing_price_grid_buy)
            #grid_balance_allocation += bidder.energy_balance_t
            print(seller , " bill of buyer: ", seller.bill)"""

    return_list = priced_list + bids_allocation
    ave_clearing_t_minus_1(return_list)
    print("______________", return_list, "_____________")
    return return_list

test_caculation = clearing(0.00015,households_test)
for house in test_caculation:
    print("NAME: ", house.householdName)
    print("bill: ", house.bill)
    print("Clearingprice/amount: " , house.clearing_price_p2p)

minute = 0
hour = 0
day = 1

'multiple times'
for i in range(1,967):
    print("########## ITERATION ", datetime(2021, 7, day, hour=hour, minute=minute, tzinfo=None,  fold=0 ), "################  ")
    # all in Wh
    house1 = Household_APS.Household_APS("H1", int(load_HH[i+288]), 0)
    house2 = Household_APS.Household_APS("H2", int(load_HH[i+384]), 0)
    house3 = Household_APS.Household_APS("H3", int(load_HH[i+96]), int(round(pv_prod_HH[i]/4)))
    house4 = Household_APS.Household_APS("H4", int(load_HH[i]), int(round(pv_prod_HH[i]/3)))
    house4.grid_selling_price = 0.00012
    print("Household inputs:")
    print(house1.householdName , house1.demand_house_t, house1.supply_house_t)
    print(house2.householdName, house2.demand_house_t, house2.supply_house_t)
    print(house3.householdName, house3.demand_house_t, house3.supply_house_t)
    print(house4.householdName, house4.demand_house_t, house4.supply_house_t)
    households_test_1 = [house1, house2, house3, house4]
    test_caculation = clearing(test_caculation, households_test_1)
    pv_prod = 0
    for house in test_caculation:

        print("NAME: ", house.householdName)
        print("bill: ", house.bill)
        print("Clearingprice/amount: " , house.clearing_price_p2p)

        # open the file in the write mode
        with open('example_clearing_ref.csv', 'a', encoding='UTF8', newline='') as f:

            # create the csv writer
            writer = csv.writer(f)

            # write a row to the csv file
            writer.writerow([datetime(2021, 7, day, hour=hour, minute=minute, tzinfo=None,  fold=0),house.householdName,house.bill, (house.supply_house_t - house.demand_house_t), house.ave_clearing_price, house.supply_house_t, house.demand_house_t, house.clearing_price_p2p, house.clearing_price_p2p_estimate_t, house.previous_p2p_bid_est])
        print(datetime(2021, 7, day, hour=hour, minute=minute, tzinfo=None,  fold=0))
    minute += 15

    if minute == 60:
        minute = 0
        hour += 1
    if hour == 24:
        hour = 0
        day += 1