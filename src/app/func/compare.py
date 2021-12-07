import csv
from datetime import datetime

header = ['period', 'name', 'bill', 'energy_balance', 'ave_clearing_price', 'pv_supply', 'demand_load']
# open the file in the write mode
with open('example_clearing.csv', 'r', encoding='UTF8', newline='') as f:


    # create the csv writer
    writer = csv.writer(f)

    # write a row to the csv file
    writer.writerow(header)

# close the file
# f.close()