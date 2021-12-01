import RLS
import Household_APS
import Bidders
import Clearing_price
import operator
from random import randint
import csv
from datetime import datetime

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

        house_bidder = Bidders.Bidders(house.householdName,house.grid_buying_price,house.grid_selling_price)
        house_bidder.energy_balance_t = round(house.balance_house_t)
        grid_balance += house_bidder.energy_balance_t

        if (isinstance(bidders_t_minus_1, float)):
            clearing_est_t = RLS.rls(house_bidder.learning_RLS, house_bidder.previous_p2p_bid_est,
                                     bidders_t_minus_1)
        else:
            clearing_est_t = RLS.rls(house_bidder.learning_RLS, find_previous_est (house, bidders_t_minus_1), find_old_clearing(house,bidders_t_minus_1))
        house_bidder.clearing_price_p2p_estimate_t = clearing_est_t

        bidders.append(house_bidder)
        house_bidder.previous_p2p_bid_est = clearing_est_t

        if(house_bidder.energy_balance_t > 0):
            house_bidder.selling_PV = True
            seller_PV.append(house_bidder)
            pv_surplus += house_bidder.energy_balance_t
        else:
            buying_PV.append(house_bidder)
    
    if(grid_balance == 0): # the grid is balanced (PV injected in the grid is exactly the same as consumption)

        sorted_bidders_price = sorted(bidders, key=lambda  x: x.clearing_price_p2p_estimate_t, reverse = True)
        clearing_price_t = sorted_bidders_price[0].clearing_price_p2p_estimate_t

        offers_allocation = sort_seller_too_much_PV(seller_PV)
        bids_allocation = sort_buyers_P2P(buying_PV)
        grid_balance_allocation = pv_surplus # power will be assigned to highest bidder
        
        priced_list = []
        
        for seller in offers_allocation:
            # seller.clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, -seller.energy_balance_t, None])
            # seller_clearing_price = clearing_price_t
            allo_buyers = allocate_buyers(seller, bids_allocation )

            if(seller.energy_balance_t >= 0): # sells energy
                #seller prizing
                seller.bill = -(seller.clearing_price_p2p_estimate_t * max(0,seller.energy_balance_t))
                #print(seller, " PRICE of seller: ", seller.clearing_price_p2p_estimate_t)
                #print(seller, " BILL of seller: ", seller.bill)
                # grid_balance_allocation -= seller.energy_balance_t

                #buyers pricing
                for buyer in allo_buyers:
                    buyer[0].clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, buyer[1],buyer[2]])
                    seller.clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, -buyer[1], buyer[0]])
                    #print("buying prices: ", buyer[0].clearing_price_p2p)
                    buyer[0].energy_balance_t -= buyer[1]
                    buyer[0].bill += (seller.clearing_price_p2p_estimate_t * buyer[1])

            priced_list.append(seller)

        return_list = priced_list + bids_allocation
        ave_clearing_t_minus_1(return_list)

        return return_list
    
    elif (grid_balance > 0): # there is too much PV electricity in the microgrid (PV production bigger than sum of all consumptions)

        sorted_bidders_price = sorted(bidders, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True)
        clearing_price_t = sorted_bidders_price[0].clearing_price_p2p_estimate_t

        offers_allocation = sort_seller_too_much_PV(seller_PV)
        
        offers_allocation_new = sorted(sorted(seller_PV, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True),
                                   key=lambda x: x.energy_balance_t, reverse=True)  # selling PV
        bids_allocation = sort_buyers_P2P(buying_PV)

        #print("offers Allo: ", offers_allocation)
        #print("Bids Allo", bids_allocation )
        #print("Grid balance: ", grid_balance)
        # sold to the grid

        for seller in offers_allocation:
            #print("Seller Balance: ", seller.energy_balance_t)
            if (seller.energy_balance_t >= grid_balance):
                
                seller.clearing_price_p2p.append([seller.clearing_price_sell_grid,-grid_balance, None])
                seller.bill -= grid_balance * seller.clearing_price_sell_grid
                seller.energy_balance_t -= grid_balance
                
                grid_balance = 0
                #print("_____ ", seller, " ", seller.clearing_price_p2p)
                
            elif(grid_balance == 0):
                break
            
            else:

                seller.clearing_price_p2p.append([seller.clearing_price_sell_grid, -seller.energy_balance_t, None])
                seller.bill -= seller.energy_balance_t * seller.clearing_price_sell_grid
                
                grid_balance -= seller.energy_balance_t
                seller.energy_balance_t = 0
                offers_allocation_new.remove(seller)
                bids_allocation.append(seller)


        # now P2P clearing
        return clearing_P2P(offers_allocation_new, bids_allocation)

    elif (grid_balance < 0): # PV production smaller than sum of all consumptions

        sorted_bidders_price = sorted(bidders, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True)

        clearing_price_t = sorted_bidders_price[0].clearing_price_p2p_estimate_t

        offers_allocation = sorted(sorted(seller_PV, key=lambda x: x.clearing_price_p2p_estimate_t, reverse=True),
                                   key=lambda x: x.energy_balance_t, reverse=True)  # selling PV
        bids_allocation = sort_buyers_less_PV(buying_PV)

        #print("Bids Allo_test", bids_allocation)

        # consumers pricing -> price from grid
        # sold to the grid
        for buyer in bids_allocation:
            #print("ENERGY_BALANCE", buyer.householdName,":", buyer.energy_balance_t)
            #print("GRID_BALANCE", grid_balance)
            #print("BID: ", buyer.clearing_price_p2p_estimate_t)
            if (buyer.energy_balance_t <= grid_balance):
                
                buyer.clearing_price_p2p.append([buyer.clearing_price_grid_buy, -grid_balance, None])
                buyer.bill += -grid_balance * buyer.clearing_price_grid_buy
                buyer.energy_balance_t += -grid_balance
                
                bought_energy_grid_Wh[buyer.householdName] = bought_energy_grid_Wh[buyer.householdName] - grid_balance
                bought_energy_grid_euro[buyer.householdName] = bought_energy_grid_euro[buyer.householdName] - grid_balance * buyer.clearing_price_grid_buy
                total_energy_balance[buyer.householdName] = total_energy_balance[buyer.householdName] - grid_balance
                
                grid_balance = 0
                
                break
            else:
                buyer.clearing_price_p2p.append([buyer.clearing_price_grid_buy, -buyer.energy_balance_t, None])
                buyer.bill += -buyer.energy_balance_t * buyer.clearing_price_grid_buy
                grid_balance += -buyer.energy_balance_t
                buyer.energy_balance_t = 0

        bids_allocation = sort_buyers_P2P(buying_PV)

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
            seller.energy_balance_t = pv_overprod

            #print("ALLOCATED", -buyer.energy_balance_t)
        else:
            transaction += pv_overprod
            pv_overprod = 0
            allocation.append([buyer, transaction, seller])
    
    #print(seller, " sells to: ", buyer)
    
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
            return bidder.ave_clearing_price

def find_previous_est (house, bidders_t_minus_1):

    for bidder in bidders_t_minus_1:
        if (bidder.householdName == house.householdName):
            return bidder.previous_p2p_bid_est

def sort_buyers_less_PV(buying_PV):
    
    bids_allocation = sorted(buying_PV, key=lambda x: x.clearing_price_p2p_estimate_t,
                             reverse=False)  # lowest load with lowest bid needs to pay the most
    
    for i in range(len(bids_allocation) - 1):
        if (round(bids_allocation[i].clearing_price_p2p_estimate_t, 6) == round(
                bids_allocation[i + 1].clearing_price_p2p_estimate_t, 6)):
            if abs(bids_allocation[i].energy_balance_t) > abs(bids_allocation[i + 1].energy_balance_t):
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

                temp = offers_allocation[i + 1]
                offers_allocation[i + 1] = offers_allocation[i]
                offers_allocation[i] = temp

    return offers_allocation

def clearing_P2P (offers_allocation, bids_allocation):

    priced_list = []

    for seller in offers_allocation:

        allo_buyers = allocate_buyers(seller, bids_allocation)

        if (seller.energy_balance_t >= 0):  # sells energy
            # seller pricing
            seller.bill = -(seller.clearing_price_p2p_estimate_t * max(0, seller.energy_balance_t))
            #print(seller, " PRICE of seller in clearing_P2P: ", seller.clearing_price_p2p_estimate_t)
            #print(seller, " bill of seller: ", seller.bill)
            # grid_balance_allocation -= bidder.energy_balance_t

            # buyers pricing
            for buyer in allo_buyers:
                #print("THIS BUYER:", buyer[1])
                buyer[0].clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, buyer[1], buyer[2]])
                seller.clearing_price_p2p.append([seller.clearing_price_p2p_estimate_t, -buyer[1], buyer[0]])
                #print("buying prices: ", buyer[0].clearing_price_p2p)
                buyer[0].energy_balance_t -= buyer[1]
                buyer[0].bill += (seller.clearing_price_p2p_estimate_t * buyer[1])

        priced_list.append(seller)

    return_list = priced_list + bids_allocation
    ave_clearing_t_minus_1(return_list)

    return return_list

## Running the program for 4 households with:
## - 2 prosumers (1 has EV, the other doesn't)
## - 2 consumers (1 has EV, the other doesn't)

# Creation of the output file in write mode
 
header = ['period', 'name', 'bill', 'energy_balance', 'ave_clearing_price', 'pv_supply', 'transactions']

with open('output.csv', 'w', encoding='UTF8', newline='') as f:

    # create csv writer
    writer = csv.writer(f)

    # write header to the first row of the csv file
    writer.writerow(header)

# Importing load profiles

balance_HH1 = [] # Consumer 1
balance_HH3 = [] # Prosumer 1

with open('Load_Prosumer1_Consumer1.csv', newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        if row[19] == "Consumer":
            continue
        else:
            balance_HH1.append(float(row[19]))

        if row[18] == "Prosumer":
            continue
        else:
            balance_HH3.append(float(row[18]))

f.close()

balance_HH2 = [] # Consumer 2

with open('Consumer2EV.csv', newline='') as f1:
    reader = csv.reader(f1)
    for row in reader:
        balance_HH2.append(float(row[5]))

f1.close()

balance_HH4 = [] # Prosumer 2

with open('Prosumer2EV.csv', newline='') as f2:
    reader = csv.reader(f2)
    for row in reader:
        balance_HH4.append(float(row[6]))

f2.close()

minute = 0
hour = 0
day = 1

# Outputs for analysis

bills = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}    # total amount payed (grid and peers) for the trading period [€]
                                                # all bills are set to 0 in the beginning of the trading period 

total_energy_balance = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}     # control variable [Wh]
                                                                # all entries must correspond to the values in the input files

sold_energy_peers_Wh = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}     # total electricity sold to peers over one trading period [Wh]
                                                                # 0 in the beginning of the trading period

sold_energy_peers_euro = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}       # total earnings made from selling energy to peers over one trading period [€]
                                                                    # 0 in the beginning of the trading period

bought_energy_peers_Wh = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}    # total electricity bought from peers over one trading period [Wh]
                                                                 # 0 in the beginning of the trading period

bought_energy_peers_euro = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}     # total expenses from buying energy from peers over one trading period [€]
                                                                    # 0 in the beginning of the trading period

sold_energy_grid_Wh = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}          # total electricity sold to peers over one trading period [Wh]
                                                                    # 0 in the beginning of the trading period

sold_energy_grid_euro = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}     # total earnings made from selling energy to peers over one trading period [€]
                                                                 # = sold_energy_grid_Wh * grid_selling_price                                          

bought_energy_grid_Wh = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}    # total electricity sold to the grid over one trading period [Wh]
                                                                # 0 in the beginning of the trading period                               

bought_energy_grid_euro = {'H1': 0, 'H2': 0, 'H3': 0, 'H4': 0}    # total electricity bought from the grid over one trading period [€]
                                                                # = bought_energy_grid_euro * grid_buying_price                                       


for i in range(672):

    # all in Wh
    house1 = Household_APS.Household_APS("H1", int(balance_HH1[i]))
    house2 = Household_APS.Household_APS("H2", int(balance_HH2[i]))
    house3 = Household_APS.Household_APS("H3", int(balance_HH3[i]))
    house4 = Household_APS.Household_APS("H4", int(balance_HH4[i]))

    households_list = [house1, house2, house3, house4]
    bidders_list = clearing(0.00015, households_list)

    for house in bidders_list:

        # open the file in the write mode
        with open('output.csv', 'a', encoding='UTF8', newline='') as f:

            # create the csv writer
            writer = csv.writer(f)

            # write a row to the csv file
            writer.writerow([datetime(2021, 7, day, hour=hour, minute=minute, tzinfo=None,  fold=0), house.householdName, house.bill, house.balance_house_t, house.ave_clearing_price, house.balance_house_t, house.clearing_price_p2p])
        
    minute += 15

    if minute == 60:
        minute = 0
        hour += 1
    if hour == 24:
        hour = 0
        day += 1

print(sold_energy_grid_Wh)

print(bought_energy_grid_Wh)

for house in bidders_list:
    print(house.clearing_price_p2p)
    #bills[house.householdName] = sold_energy_grid_euro[house.householdName] + sold_energy_peers_euro[house.householdName] - bought_energy_grid_euro[house.householdName] - bought_energy_peers_euro[house.householdName]

#print(bills)
for i in bidders_list:
    print(i.bill*672)
