# -*- coding: utf-8 -*-
"""
Created on Thu Jul  1 13:27:23 2021

@author: maxal
"""


import numpy as np                          # numpy for ranges and maxima and minima
import matplotlib.pyplot as plt             # matplotlib for 2D plotting
import datetime as d                        # datetime for analyses over course of the year
from scipy.interpolate import CubicSpline   # Cubic Spline for Interpolation over course of the year
import pickle as p                          # pickle for data saving
import time                                 # time for keeping track of calculation time
from Retail import *                        # import custom made classes and functions


'''======== Opening File and sorting all purchases to their respective customers ======='''

# convert the csv file into a data array
f= open('online_retail_II.csv','r')
data=f.readlines()
f.close()

for i in range(len(data)):
    data[i]=data[i][:-1].split(sep=',')

print('Start sorting into customers')

# similar principal to sorting invoices and products described in functions above
# creates a List of all customers with all their respective purchases

customer_id=[]
customer_L=[]

# going threw all purchases
for line in data[1:]:
    curr_cust_id=line[-2]
    
    # as the length of list entries dedicated to product name might change, some parts of the list have to be taken from the backend of the line
    current = invoice(line[0], line[-4]) # build current invoice
    productL=line[2:len(line)-5] # find all lines that make up the product name
    product=productL[0]
    if len(product)==0: # fail safe if product Name is empty due to missing data
        product='NoNAME'
    product=cut_waste(product) # shorten first part of product name



    # if product consists of multiple entries, separate them distinctly and remove waste
    if len(productL)>1:
        if len(product)>0:
            product+='***'
        for word in productL[1:]:
            product+=' '+cut_waste(word)
    if len(product)==0:     # second fail save
        product='NoNAME'
    product=cut_waste(product)
    current.add_product(product, line[-3], line[3]) # add product to current provisorial invoice

    # if the customer was not yet encountered
    if curr_cust_id not in customer_id:
        customer_id.append(curr_cust_id) # add id to list for future reference
        curr_cust = customer(curr_cust_id, line[-1]) #c reate new customer
        customer_L.append(curr_cust)
        i = len(customer_L)-1

    else:
        i = customer_id.index(curr_cust_id)

    customer_L[i].add_purchase(current) # add pruchase to correct customer




''' --------------------- TASK 1------------------------'''

print('============== START TASK 1 ===================')

# initiate figure
plt.figure(figsize = [10,8])
# the purchases are ordered chronologically, thus t0 is the day of the first line
t0=d.date.fromisoformat(data[1][4].split()[0])

# initiate a list of all dates
tL=[t0]
inL=[0] # initiate a list with the income on individual days

# not using the customer list here, as only day and price of the product matter
for line in data[1:]:
    i=-4
    # get current date
    a=line[i].split()  # date includes daytime, only day is required
    tcurr=d.date.fromisoformat(a[0]) 
    price=float(line[i+1])
    # as before, either append (increase) price for the correct date or append a new entry if day was not yet coverd
    if tcurr in tL: 
        j=tL.index(tcurr)
        inL[j]+=price
    else:
        tL.append(tcurr)
        inL.append(price)

# sort the income into calender weeks
# same principle as before
tL[0].isocalendar()[1]
weeks=[]
weekly_in=[]
for i in range(len(tL)):
    curr_week=tL[i].isocalendar()[1]
    if curr_week in weeks:
        j=weeks.index(curr_week)
        weekly_in[j].append(inL[i])
    else:
        weeks.append(curr_week)
        weekly_in.append([inL[i]])

# take the median for each week to exclude very irregular days
weekly_median=[np.median(week) for week in weekly_in]


# since the count starts in december, the first four weeks are moved to the back, so the list starts at week 1
first4weeks=weeks[:4]
weeks=weeks[4:]
for day in first4weeks:
    weeks.append(day)
first4weeks=weekly_median[:4]

weekly_median=weekly_median[4:]
for day in first4weeks:
    weekly_median.append(day)

# plot weekly median
plt.plot(weeks, weekly_median, linestyle='--',linewidth=3, label='Weekly Median per calendar Week')

# take the moving average over each month (specifically a four week period)
monthly_mean=[np.mean([weekly_median[0],weekly_median[1], weekly_median[-1], weekly_median[2]])]
month_weeks=[weeks[1]]
for i in range(3,48,4): # loop over every fourth week, taking the average of the next four weeks and appending them linked to the middle
    average=np.mean([weekly_median[i],weekly_median[i+1], weekly_median[i+2], weekly_median[i+3]])
    monthly_mean.append(average)
    month_weeks.append(weeks[i+2])

# append the first point at the end again to create a closed loop
monthly_mean.append(monthly_mean[0])
month_weeks.append(month_weeks[0]+52)

#create a periodic Cubic spline
fit=CubicSpline(month_weeks,monthly_mean, bc_type='periodic')
# plot the expected income of each day, 
# to get the expected income of a given week, sum over all days 
# remember, that if day1= k in Z, than the next days are all in intervalls of 1/8
days=np.linspace(0,weeks[-1]+3,365)
plt.plot(days, fit(days),linewidth=5, label='Continous Model')

# plotting stuff
plt.legend()
plt.grid()
plt.xlabel('Calendar Week')
plt.ylabel('Weekly Income [pounds]')
plt.title('Model estimating total weekly sales based on previous two years')
plt.savefig('Weekly_income.png')
plt.clf() # reset figure


''' --------------------- TASK 2------------------------'''
print('============== START TASK 2 ===================')
# customers are sorted into two groups, 
# those that return the next quarter after a purchase
# and those who either skipped at least one quarter or did not return an all
# in addition, two sets of lists are created

next_q_invoice=[]
not_next_q_invoice=[]
next_q_date=[]
not_q_date=[]
# loop over all customers
for cust in customer_L:
#    quartal=False
    # set current date as beginning of 1900, so that the first one is definitly different
    curr_day='1900-01-01'
    # go over all invoices of the current customer
    for i in range(len(cust.invoice_L)-1):
        date1=cust.invoice_L[i].date # date of the current invoice
        
        # check if the invoice is not on the same day as the previous
        if date1==curr_day:
            date_append=False
        else:
            date_append=True
            curr_day=date1
        # mark that the current invoice has currently no corresponding purchases in the next quarter
        this_one=False
        # loop over all other invoices, as they are chronologically ordered, only indices larger than i have to be considered
        for j in range(i+1, len(cust.invoice_L)):
            date2=cust.invoice_L[j].date
            if next_quartal(date1,date2):
                # if a purchase in the next quarter was detected, add date and invoice to their corresponding lists
                next_q_invoice.append(cust.invoice_L[i])
                if date_append:
                    next_q_date.append(date1)
                quartal=True
                this_one=True
                # break as their might be several purchases the next month and the invoice only needs to be appended once
                break
        # should the invoice did not trigger a purchase the next quarter, it is added to the reference lists
        if not this_one:
            not_next_q_invoice.append(cust.invoice_L[i])
            if date_append:
                not_q_date.append(date1)


print('Finished sorting by next quarter purchases.')
# loop over both the purchases next quarter and not next quarter and write down all the products from the respective lists
next_q=[]
not_next_q=[]
for invoice in next_q_invoice:
    prodL=invoice.product_L
    for product in prodL:
        if '***' in product:
            product=product.split(sep='***')[0]
        next_q.append(product)

for invoice in not_next_q_invoice:
    prodL=invoice.product_L
    for product in prodL:
        if '***' in product:
            product=product.split(sep='***')[0]
        not_next_q.append(product)



# find all individual product names
prod_names=[]
for prod in next_q:
    if prod not in prod_names:
        prod_names.append(prod)
for prod in not_next_q:
    if prod not in prod_names:
        prod_names.append(prod)

# for each product, count them inside both those that trigger the next quarter and those that did not
ratio=[]
for prod in prod_names:
    next_count=next_q.count(prod)
    # should it not be counted in those for the next quarter write 0 without divison to avoid error
    if next_count<1:
        ratio.append(0)
    else:
        # ratio is the compared to the total number of purchases
        ratio.append((next_count/(next_count+not_next_q.count(prod))))

# List of all ratios and the total count of all products for better reference of their statistical significance
all100=[[prod_names[i],next_q.count(prod_names[i]), 100*ratio[i]] for i in range(len(prod_names))]
all100=Sort(all100)

# just for this examplery run, print the most frequent purchases and their return chance
print(all100[-50:])

print('\n\n')
print('Sorting by individual words')

# start a list for words
words=[]

# go over all products and 
for name in prod_names:
    for word in name.split():
        if (word not in words) and (len(word)>2):
            words.append(word)


ratio_per_type=[]
for product in words:
    sum=0
    ratio=0
    for line in all100:
        if product in line[0]:
            sum+=line[1]
            ratio+=line[2]*line[1]
    if sum!=0:
        ratio/=sum
    else: 
        ratio=0
    ratio_per_type.append([product, sum, ratio])
ratio_per_type=Sort(ratio_per_type)
print(ratio_per_type[-50:])

print('Return chance based on purchase date')
# change dates into their respective calendar weeks
next_q_date=[d.date.fromisoformat(day.split()[0]).isocalendar()[1] for day in next_q_date]
not_q_date=[d.date.fromisoformat(day.split()[0]).isocalendar()[1] for day in not_q_date]


plt.figure(figsize=[10,8])

weeks_ratio=[]
abs_weeks=[]
weeks_all=range(1,53) # list of all week numbers
for n in weeks_all:
    # count the amount of dates that fall into the respective calendar weeks
    yes=next_q_date.count(n)
    no=not_q_date.count(n)
    # weeks_ratio tracks the return percentage for each week
    weeks_ratio.append(100*(yes/(yes+no)))
    # abs_weeks as the name suggests the absolute number of potentially returning pruchases
    abs_weeks.append(yes)



# as above this time looping over four weeks at once to get a monthly average
monthly_ratio=[]
weeks=[]
abs_counts=[]
for i in range(1,53,4):
    yes=no=0
    weeks.append(i+2.5)
    for j in range(4):
        yes+=next_q_date.count(i+j)
        no+=not_q_date.count(i+j)
    monthly_ratio.append(100*yes/(yes+no))
    abs_counts.append(yes/4) # absolute count is divided by four to account for four weeks
    
    
    
# for both sets, fit spline and create plots
    
plt.figure(figsize = [10,8])
weeks.append(weeks[-1]+4)
monthly_ratio.append(monthly_ratio[0])
fit=CubicSpline(weeks,monthly_ratio, bc_type='periodic')
days=np.linspace(0,53,365)


plt.plot(weeks_all,weeks_ratio,label='Weekly Percentage', linewidth=3, linestyle='--')
plt.plot(days, fit(days),label='Continous Fit', linewidth=5)
plt.title('Probability of Customer to return the next quarter')
plt.xlabel('Calendar Week')
plt.ylabel('Return Chance [%] of single purchase')
plt.grid()
plt.savefig('return_chance.png')
plt.clf()

plt.figure(figsize=[10,8])

abs_counts.append(abs_counts[0])
fit=CubicSpline(weeks,abs_counts, bc_type='periodic')
plt.plot(weeks_all,abs_weeks, label='Absolute Number', linewidth=3, linestyle='--')
plt.plot(days, fit(days), label='Continous fit', linewidth=5)
plt.title('Number of Customer to return the next quarter')
plt.xlabel('Calendar Week')
plt.ylabel('Absolute Number of returning customers')
plt.grid()
plt.legend()
plt.savefig('return_chance_abs.png')
plt.clf()



print('============== START TASK 3 ===================')

# get number of products from list of product names
n_prods=len(prod_names)

# basket creates an array storing the individual ratios each product was purchased in combination with each other product
basket=np.zeros([n_prods,n_prods])

# create a list of all invoices
all_invoices=[]
for cust in customer_L:
    for invoice in cust.invoice_L:
        all_invoices.append(invoice.product_L)

# threshhold is for tracking progress
threshhold=0
t_start=time.time()
for i in range(n_prods):
    prod=prod_names[i]
    invoice_indices=[]
    # find all invoices that contain the given product

    for k in range(len(all_invoices)):
        invoice=all_invoices[k]
        if prod in invoice:
            invoice_indices.append(k)
    # total number this product was bought is the length of this list
    all_p=len(invoice_indices)
    # go over all other product to compare the frequency of them being together
    for j in range(n_prods):
        if i!=j:
            sec_prod=prod_names[j]
            together=0
            # for this go over all indices of the individual invoices that were marked previously
            for k in invoice_indices:
                if sec_prod in all_invoices[k]:
                    together+=1 # track how many contain the second product as well
            if all_p==0: # fail save
                if together!=0:
                    print('Error at i=',i,', j=',j)
                all_p+=1
            # store the corresponding ratio is the basket
            basket[i,j]=together/all_p
    # store the total number this product was bought
    basket[i,i]=-all_p # negative so it will always be lowest number
    
    # keeping track of progress and creating back up saves
    if i/n_prods>threshhold:
        print(100* i/n_prods, '% completed')
        p.dump( basket, open( "provi_basket.p", "wb" ) )
        t_now=time.time()
        t_diff=t_now-t_start
        print('First Percent took', t_diff, 'Seconds=', t_diff/60, 'Minutes')
        threshhold+=0.01

# save all via pickle
p.dump( basket, open( "provi_basket.p", "wb" ) )

# link basket and products
full_basket=dict(zip(prod_names, basket))
p.dump( full_basket, open( "basket.p", "wb" ) )
