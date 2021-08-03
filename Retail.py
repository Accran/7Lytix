# -*- coding: utf-8 -*-
"""
Created on Tue Aug  3 10:01:02 2021

@author: maxal

Modul containing Classes and functions for retail Data analysis
"""
import datetime as d                        # datetime for analyses over course of the year
import pickle as p                          # pickle for data saving


'''Declaration of Classes
Two different classes are used: customer, which sorts by customer ID, assigning all invoices and their respective products to a given customer.
And invoice, representing an individual pruchase by a customer with multiple products in one invoice'''


class customer:
    '''Class defines an individual customer and tracks all their purchases and their location.
    Requires to initialize:
        ID       - differentiate a customer, used to assign future purchases to this customer
        location - home country of customer, currently not used in analysis as UK is heavily overrepresented
    
    it features:
        invoice_L   - List with elements being of the "invoice" class
        invoice_id  - List with elements being of type string, used to keep track which invoice is already assigned to this customer
    '''

    def __init__(self, ID, location):
        self.id = ID              # each customer is represented via an unique ID given in the dataset
        self.invoice_L = []       # They may purchase multiple times over the 2 year periode, all invoices are stored here
        self.invoice_id =[]       # to differentiate the individual invoicesm their respective invoice ID is used
        self.location = location

    def add_purchase(self, invoice):
        ''' Adds a purchase in the form of a single product (or multiple instances of the same product) to the customer.
        This creates a new entry in its invoice list, if the ID of the invoice was not stored for this customer before.
        Otherwise the respective entry is appended.
        Requires an "invoice" class to append
        '''
        if invoice.id not in self.invoice_id:  # if no purchase of this invoice was recorded before, create a new entry
            self.invoice_L.append(invoice)
            self.invoice_id.append(invoice.id) # track its ID to append future purchases to the correct invoice even if these are added non-chronologicaly
        else:                                  # if the invoice is already present, find its index and use this to append the item to its invoice.
            i=self.invoice_id.index(invoice.id)
            for j in range(len(invoice.product_L)):
                self.invoice_L[i].add_product(invoice.product_L[j], invoice.price_L[j], invoice.quantity_L[j])



class invoice:
    '''Class defining an individual purchase, tracking invoice, date, product and price.
    Requires to initialize: 
        ID          - differentiate an invoice, used to assign future purchases to this invoice
        date        - Time of purchase; Further studies require that the first part is given as "YYYY-MM-DD", it may contain a daytime as well, but is not required with the current usage of this class
        
    it features the following characteristics:
        product_L   - List storing all products by name
        price_L     - List storing the price of the individual products
        quantity_L  - similar to price_L, thi list stores the amount of a given product that was purchased
                please note that the index of a product links it to the index of its price and quantity in the respective lists.'''
    def __init__(self, ID, date):
        self.id = ID
        self.product_L = []
        self.price_L = []
        self.quantity_L = []
        self.date = date


    def add_product(self, product, price, quantity):
        '''Add a product to an invoice. In this current version, only positive sales are stored.
            A product that has either a negative or no value will be ignored for consistency reasons.'''
        price=float(price) 
        if float(price)>0:
            self.product_L.append(product)
            self.price_L.append(price)
            self.quantity_L.append(quantity)



def next_quartal(date1,date2):
    '''Function to determine if date2 is in the next quartal to date1
    Input is 2 date strings given for examples as objects in invoice.date
    
    Return is a bolean that determines if date2 is in the quartal following date1.'''
    
    # determine the month and the year for both dates, this is done with the datetime module
    date1=d.date.fromisoformat(date1.split()[0])
    date2=d.date.fromisoformat(date2.split()[0])
    month1=date1.month
    month2=date2.month
    year1=date1.year
    year2=date2.year

    # create lists with the monthnumbers
    q1=[1,2,3]      # Jan, Feb, Mar
    q2=[4,5,6]      # Apr, May, Jun
    q3=[7,8,9]      # Jul, Aug, Sep
    q4=[10,11,12]   # Oct, Nov, Dec

    # if both are in the same year, the have to fall into consecutive quarters
    if year1==year2:
        if (month1 in q1 and month2 in q2) or (month1 in q2 and month2 in q3) or (month1 in q3 and month2 in q4):
            return True
        else:
            return False
    # the only other combination is the foruth quarter of one year and the first of the next
    elif year2==year1+1:
        if (month1 in q4 and month2 in q1):
            return True
        else:
            return False
    else:
        return False




# Python code to sort the lists using the second element of sublists
# Inplace way to sort, use of third variable
# Taken from: https://www.geeksforgeeks.org/python-sort-list-according-second-element-sublist/
def Sort(sub_li):
    l = len(sub_li)
    for i in range(0, l):
        for j in range(0, l-i-1):
            if (sub_li[j][1] > sub_li[j + 1][1]):
                tempo = sub_li[j]
                sub_li[j]= sub_li[j + 1]
                sub_li[j + 1]= tempo
    return sub_li


def cut_waste(word):
    '''Cut useless characters at the beginning and end of a word
    word is given in string format. Removes the followinng characters from the beginning or end of the word:  ', "-#!§$%&/()[]{}\+~><|_:;=?-.*   
    if they are present in the middle of the word, they are ignored. 
    The process is repeated, as long as respective characters are still present on either end.'''

    tocut=', "-#!§$%&/()[]{}\+~><|_:;=?-.*'
    tocut+="'"
    while word[0] in tocut:
        word=word[1:]
        # to prevent an error, if the word only contained removable characters, 
        # should the length reach 0, it is returned and the loop interrupted.
        if len(word)==0:
            return word
    # this is not required for the backside loop, as the fact that the frontside loop stopped requires a non removable character.
    while word[-1] in tocut:
        word=word[:-1]
    return word


def search_basket(prod, basket='basket.p'):
    '''Search the basket for the product with the highest frequency of purchase with the given product.
    Also provides the total number of purchases for statistical reference.
    requires a pickled dictionary with product names and a 2D array with all products.
    Total number of products sold is stored on main diagonal as a negative.
    
    Input:
        prod        - STRING: name of the product in prod_names list
        basket      - STRING: Name of basket file
        '''
        
    basket=p.load( open( basket, "rb" ))    # open filled basket
    prod_names=list(basket.keys())          # read prod names out of zipped dictionary
    curr_line=basket[prod]             # get correct line based on product
    # build a list of recommondations
    results=[[prod_names[i],curr_line[i]] for i in range(len(prod_names))]
    # sort the list by frequency
    results=Sort(results)
    # get total amount the product was purchased out of list
    freq=-curr_line[prod_names.index(prod)]    
    # return the top five correspondance
    return results[-5:], freq
