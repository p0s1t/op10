# Program Name: op10

# Program Author: Chris Aggeles

# First Compile Date: yet to be compiled

# Program Purpose: to create and analyze supports and resistances of a stock's price, its anticipated and reported earnings,
# and the sentiments leading up to and following those reports. Time frame is 180 days (90 days before and 90 days after earnings report)


import sys 
import subprocess
import time as t
import pandas as p
from pandas.tseries.offsets import BDay as b

import csv as c

import requests as r

import random as ran

import datetime as d
from datetime import timedelta
 
import json as j

import urllib as u

import sqlite3 as s

import io


def iDB(path, date, tableName, colVector, dataTypes):
    
    conn = s.connect(path)
    sc = conn.cursor()
    
    command = 'CREATE TABLE ' + tableName + '(' + 'date ' + 'text' + ' PRIMARY KEY '
    
    # iterate through column names and data types and build command
    for c in colVector and d in dataTypes:
        # for all other database commands, add col name and datatype to executable statement
        if c == 'symbol' or c == 'sector':
            command += ', ' + c + ' ' + d + ' NOT NULL '
        else:
            command += ', ' + c + ' ' + d + '  NOT NULL UNIQUE '
        
    command += ');'
    
    # build table 
    sc.execute(command)
    
    # commit and close connection
    conn.commit()
    conn.close()
    
    print("table built for: " + path)
    return;

# end makeDB()
   
def addRow(path, date, tableName, colVector, rowVector):
    
    # open database connection
    conn = s.connect(path)
    sc = conn.cursor()
    
    # the primary key is the date, so create row string with the date as the first col name and value
    colNames = "Date "
    rowVals = date + "  "
 
    # concatenate all col names and their respective values into one string
    for cv in colVector and r in rowVector:
        
          colNames += "," + cv
          rowVals += "," + r
        
    # build command
    execStatement = "INSERT INTO" + tableName + "(" + colNames + ")" + "VALUES (" + rowVals + ");"     
    
    # insert row
    sc.execute(execStatement)
    
    # commit and close connection
    conn.commit()
    conn.close()
    
    return True;

# end addRow()

# gets csv data, writes it to disk as a csv file and then returns a pandas dataframe of it
def getDailyData(symbol):
    
    apikey = "1J9ADFHPWRABQJP"
    
    function = "TIME_SERIES_DAILY_ADJUSTED"
    
    datatype = "csv"
    
    dataPath = "https://www.alphavantage.co/query?function="+ function + "&symbol="\
    + symbol + "&apikey=" + apikey + "&datatype=" + datatype
    
    # use http request to get csv
    download = r.get(dataPath)
    
    outPath = symbol + '.dailyData.csv'
    
    # write csv file to disk
    with open(outPath, 'w') as f:
        writer = c.writer(f)
        reader = c.reader(download.text.splitlines(delimiter = ',', quotechar=','))
       
        for row in reader:
            writer.writerow(row)
            
    # make a dataframe from the csv data returned by the http request
    df = p.read_csv(io.StringIO(download.text))
    
    # return dataframe
    return df;  

# end getDailyData()

def getEarningsIndex(dailyData, earningsDate):
    
    index = len(dailyData)
    finished = False
    while not(finished):
        row = dailyData.iloc[[index]]
        index -= 1
        if earningsDate == row['Date']:
            finished = True
    
    return index;

# end getEarningsIndex()

# finds difference between two dates in business days
def dayDiff(date1, date2):
    
    d1 = p.datetime.strptime(date1, "%Y-%m-%d")
    d2 = p.datetime.strptime(date2, "%Y-%m-%d")

    
    p.date_range(d1, d2, freq=b) # TODO: check this is working

    return abs((d2-d1).days);

# end dayDiff()

# returns present date in YYYY-MM-DD format    
def getToday():

    date = d.now()
    
    newDate = date.year + '-' + date.month + '-' + date.day 
    
    return newDate;

# end getNow()
    
# returns n multiples and divisions of phi and some given value of an equity on its earnings report date  
def getPhi(n, rOrS, dailyData, colName, earningsDate, earningsVal):
    
    phi = [] # TODO: look into declaring length of array

    today = getToday()
    
    earningsIndex = getEarningsIndex(dailyData, earningsDate)
    
    #calculate distance from earnings report in business days  
    working_days = dayDiff(today, earningsDate)
    
    # initialize data structures that will hold the metrics related to the earnings date closing price
    # and the various multiples and divisions of phi
    if rOrS:
        rDates = p.DataFrame(columns=['Date'], dtype=str)
        resistances = p.DataFrame(index=['Date'], columns=['eToPhi'], dtype=float)  
        ints = p.DataFrame(index=['Date'], columns=['phiIndex', 'dEarnings'], dtype=int)
        res = p.concat([rDates, resistances, ints], axis=1)
    else:
        sDates = p.DataFrame(columns=['Date'], dtype=str)
        supports = p.DataFrame(index=['Date'], columns=['eToPhi', 'dPrice'], dtype=float) 
        ints = p.DataFrame(index=['Date'], columns=['phiIndex', 'dEarnings'], dtype=int)
        sup = p.concat([sDates, supports, ints], axis=1)
    
    # calculate values derived from resistance and support relative to earnings close
    # and its relationship to various multiples and divisions of phi
    for i in range(n): # more accurate measurements may be derived by mutating the exponent
        # phi value is 1 plus root i divided by two
        # starts at phi = 1
        phi[i] = ((1 + (i+1)**(1/2.0))/2) 
    
    # scan each day from now to the earnings day and check for supports/resistances
    for i in range(working_days):
        tempRow = dailyData.iloc[[i + earningsIndex]]
        # for each row in the dailyData dataframe
        if tempRow[4] != None:
            
            date = tempRow[0]
        
            for x in range(n):
                # for some phi based multiple of earnings  
                if tempRow[colName] >= (phi[x] * earningsVal):
                
                    # add values to resistances dataframe
                    if rOrS:
                        res['Date'] = date
                        res.loc[date]['phiIndex'] = x # what multiple of phi is this?
                        res.loc[date]['eToPhi'] = ( phi[x] * earningsVal ) # relationship of multiple of phi and price
                        res.loc[date]['dPrice'] = abs( (phi[x] * earningsVal) - tempRow[colName] ) # absolute distance from price
                        res.loc[date]['dEarnings'] = i # how far (in working days) from the earnings report date to present
                
                # for some phi based division of earnings        
                elif tempRow[colName] <= (earningsVal / phi[x]):
                    
                    # add values to supports dataframe
                    if not(rOrS):
                        sup.loc['Date'] = date
                        sup.loc[date]['phiIndex'] = x # what division of phi is this?
                        sup.loc[date]['eToPhi'] = ( earningsVal / phi[x] ) # relationship between division of phi and price
                        sup.loc[date]['dPrice'] = abs( (earningsVal / phi[x]) - tempRow[colName] ) # absolute distance from price
                        sup.loc[date]['dEarnings'] = i # how for (in days) from the earnings report date to present
    
    if rOrS:
        return res;
    else:
        return sup;

# end getPhi()
        
def initPhi(phi, resOrSup, n):
    
    # note: ordering begins at most recent date 
    row = resOrSup.iloc[[n]]
    
    start_date = row[0]
    pIndex = row[1]
    eToPhi = row[2]
    dPrice = row[3]
    dEarnings = row[4]
    
    phi['start_date'] = start_date
    phi[start_date]['end_date'] = start_date
    
    phi[start_date]['phiIndex'] = pIndex
    phi[start_date]['phiCount'] = 1
    
    phi[start_date]['minValue'] = eToPhi
    phi[start_date]['maxValue'] = eToPhi
    phi[start_date] ['avValue'] = eToPhi
    
    phi[start_date]['minDEarn'] = dPrice
    phi[start_date]['maxDEarn'] = dPrice
    phi[start_date]['avDEarn'] = dPrice
    
    phi[start_date]['dEarnInBound'] = dEarnings
    phi[start_date]['dEarnOutBound'] = dEarnings

    return phi;
    
#get data using metrics recorded in resistances and supports dataframe structure    
def countPhi(resOrSup): 
   
   phiDex = p.DataFrame(columns=['start_date'], dtype=str) 
   phiDates = p.DataFrame(index=['start_date'], columns=['end_date'], dtype=str) 
   phiMetrics = p.DataFrame(index=['start_date'], columns=['maxValue', 'minValue', 'avValue', 'minDPrice', 'maxDPrice', 'avDPrice'], dtype=float) 
   phiCount = p.DataFrame(index=['start_date'], columns = ['phiIndex', 'nPhi', 'dEarnInBound', 'dEarnOutBound'], dtype=int)
    
   phi = p.concat([phiDex, phiDates, phiCount, phiMetrics], axis=1)
   
   start_date = ""
   
   # iterate through each row of the dataframe and calculate phi-metrics
   
   phi = initPhi(phi, resOrSup, 0)
   
   start_date = phi.iloc[0]['Date']
   
   for i in range(len(resOrSup) - 1):
       
           current_row = resOrSup.iloc[[i]]
           next_row = resOrSup.iloc[[i+1]]
           
           # if phi index is the same as the previous row's, increase nPhi and calc metrics
           if current_row['phiIndex'] == next_row['phiIndex']:
                   
               phi.loc[start_date]['nPhi'] += 1
               phi.loc[start_date]['end_date'] = next_row['Date']
               
               # calc max value
               if phi.loc[start_date]['maxValue'] < next_row['eToPhi']:
                   phi.loc[start_date]['maxValue'] = next_row['eToPhi']
               # calc min value
               elif phi.loc[start_date]['minValue'] > next_row['eToPhi']:
                   phi.loc[start_date]['minValue'] = next_row['eToPhi']
                   
               elif phi.loc[start_date]['minDPrice'] > next_row['dPrice']:
                   phi.loc[start_date]['minDPrice'] = next_row['dPrice']
                   
               elif phi.loc[start_date]['maxDPrice'] < next_row['dPrice']:
                   phi.loc[start_date]['maxDPrice'] = next_row['dPrice']
               
               phi.loc[start_date]['avDPrice'] += next_row['dPrice']
               phi.loc[start_date]['avDPrice'] /= phi.loc[start_date]['nPhi']
               # calc average value 
               phi.loc[start_date]['avValue'] += next_row['eToPhi']
               phi.loc[start_date]['avValue'] /= phi.iloc[i]['nPhi']
               # set outer boundary from the date of the earnings report
               phi.loc[start_date]['dEarnOutBound'] = next_row['dEarnings']
           
           else: # if differing phi indices, reset date, start new row in phi dataframe
               phi = (phi, resOrSup, i)
               start_date = resOrSup.iloc[i]['Date']              

   return phi;
    
# end countPhi()    



                    ##################### begin script ######################


# get earnings date from command line argument

eDate = sys.argv[1]

current_date = d.datetime.strptime(eDate, "%Y-%m-%d")

prev_date = current_date - timedelta(days = 1)
prev_90 = prev_date - timedelta(days = 115)
prev_30 = prev_date - timedelta(days = 40)
next_90 = current_date + timedelta(days = 115) # presumes twelve weekends and three holidays 
                                                # between current date and 90 days from current date 
next_30 = current_date + timedelta(days = 40) # presumes four weekends and two holidays

prev_date = prev_date.strftime('%Y-%m-%d')
current_date = current_date.strftime('%Y-%m-%d')

prev_90 = prev_90.strftime('%Y-%m-%d')
next_90 = next_90.strftime('%Y-%m-%d')
prev_30 = prev_30.strftime('%Y-%m-%d')
next_30 = next_30.strftime('%Y-%m-%d')


# intrinio auth data
uname = "e855f3633505c9e54a962d373eefd2af"
pw = "b58ed78efb0f7e161b95e1c18e0fb507"

# paths to server

# base_url = "https://api.intrinio.com"
# request_url = "//surprises/sales"
# sales_url = base_url + request_url

# sales_date = prev_date 

# TODO: note that each json object must be called by a different script

# earnings_url = "https://api.intrinio//securities/surprises/eps"

# earnings_date = current_date

# sales_query_params = {
        
#      'earnings_date' : sales_date
        
#     }

#earnings_query_params = {
        
#       'earnings_date' : earnings_date
        
#      }

# get json data from server

# pause to forgo overworking the server

# earnings_response = r.get(earnings_url, params=earnings_query_params, auth=(uname, pw) )

# temp data structure

# sales_tData = sales_response.json()['data']

# sales_tData = sales_json['data']

# sales_df = p.DataFrame([[d['v'] for d in x['c'] for x in sales_tData['rows']], columns=[d['label'] for d in sales_tData['cols']])

# temp_data = j.normalize(sales_tData)
# sales_df = p.DataFrame(temp_data)
# earnings_tData =  j.loads(earnings_json.read().decode(earnings_json.info().get_param('charset') or 'utf-8' ))

# how much (count) and what (data)

# sCount = sales_json['result_count']

# eData = earnings_tData['data']
# eCount = earnings_tData['result_count']

# enumerate (local!) database paths

# salesPath = "Users/Jay/Documents/db/sdb.sqlite"
# earningsPath = "Users/Jay/Documents/db/edb.sqlite"
sectorPath = "C:/Users/Jay/Documents/db/sectordb.sqlite"
sentimentPath = "C:/Users/Jay/Documents/db/sentimentdb.sqlite"

# enumerate tables' and columns' names 

# salesTable = "sales_table"
# earningsTable = "earnings_table"

sentTable = "sentiment_table"
sectorTable = "sector_table"

# enumerate sales columns

# scol0 = 'ticker'
# scol1 = 'actual'
# scol2 = 'estimate'
# scol3 = 'amt_diff'
# scol4 = 'percent_diff'
# scol5 = 'approx_dev'
# scol6 = 'fisc_yr'


# enumerate earnings columns

# ecol0 = 'ticker'
# ecol1 = 'actual'
# ecol2 = 'estimate'
# ecol3 = 'amt_diff'
# ecol4 = 'percent_diff'
# ecol5 = 'approx_dev'
# ecol6 = 'count_estimate' # number of analysts incorporated into the estimate
# ecol7 = 'fisc_yr'
# ecol8 = 'report_time'
# ecol9 = 'report_desc' # before, during, or after hours


# enumerate sentiment columns for sector and ticker

# TODO: verify this is the correct syntax when creating PRIMARY KEY

# date = 'PRIMARY KEY'

sector = "sector"
ticker = "ticker"

bl1 = "bullish_1wk"
bl4 = "bullish_4wk"
bl12 = "bullish_12wk"

br1 = "bearish_1wk"
br4 = "bearish_4k"
br12 = "bearish_12wk"

sent1 = "sentiment_1wk"
sent4 = "sentiment_4k"
sent12 = "sentiment_12wk"

bz1w4w = "buzz_1w4w"
bz1w12w = "buzz_1w12w"
bz4w12w = "buzz_4w12w"

sentimentIndex = p.DataFrame(columns=['eDate'], dtype=str)
sentimentSector = p.DataFrame(columns=['ticker', 'sector'], dtype = str)
sentimentBullish = p.DataFrame(columns=['bullish_1wk', 'bullish4wk', 'bullish12wk'], dtype=int)
sentimentBearish = p.DataFrame(columns =['bearish_1wk', 'bearish_4wk', 'bearish_12wk'], dtype=int)
sentimentSentiments = p.DataFrame(columns=['sentiment_1wk', 'sentiment_4wk', 'sentiment_12wk'], dtype=int)
sentimentBuzz = p.DataFrame(columns=['buzz_1w4w', 'buzz_1w12w', 'buzz_4w12w'], dtype=float)
sentimentDF = p.concat([sentimentIndex, sentimentSector, sentimentBullish, sentimentBearish, sentimentSentiments, sentimentBuzz], axis=1)

sectorIndex = p.DataFrame(columns=['eDate'], dtype=str)
sectorName = p.DataFrame(columns=['sector'], dtype=str)
sectorBullish = p.DataFrame(columns=['bullish_1wk', 'bullish4wk', 'bullish12wk'], dtype=int)
sectorBearish = p.DataFrame(columns =['bearish_1wk', 'bearish_4wk', 'bearish_12wk'], dtype=int)
sectorsectors = p.DataFrame(columns=['sector_1wk', 'sector_4wk', 'sector_12wk'], dtype=int)
sectorBuzz = p.DataFrame(columns=['buzz_1w4w', 'buzz_1w12w', 'buzz_4w12w'], dtype=float)
sectorDF = p.concat([sectorIndex, sectorBullish, sectorBearish, sectorsectors, sectorBuzz], axis=1)


#create vectors of column names

# salesColVec = {scol0, scol1, scol2, scol3, scol4, scol5, scol6}
# earningsColVec = {ecol0, ecol1, ecol2, ecol3, ecol4, ecol5, ecol6, ecol7, ecol8, ecol9}


#sentimentNameDF = p.DataFrame(index='ticker', columns=[sector, bl1, bl4, bl12, br1, br4, br12, sent1, sent4, sent12, bz1w4w, bz1w12w, bz4w12w], dtype=str)
#sectorNameDF = p.DataFrame(index='sector', columns=[bl1, bl4, bl12, br1, br4, br12, sent1, sent4, sent12, bz1w4w, bz1w12w, bz4w12w], dtype=str)


# create tables within databases 

#iDB(salesPath, prev_date, salesTable, salesColVec, salesUnique)
#iDB(earningsPath, current_date, earningsTable, earningsColVec, earningsUnique)
# iDB(sentimentPath, prev_date, sentTable, sentimentColVec, sent_data_types)
# iDB(sectorPath, prev_date, sectorTable, sectorColVec, sector_data_types)

symbol = "AAPL" 
sector = ""
sector0 = "Consumer Discretionary"
sector1 = "Consumer Staples"
sector2 = "Energy"
sector3 = "Financials"
sector4 = "Health Care"
sector5 = "Industrials"
sector6 = "Information Technology"
sector7 = "Materials"
sector8 ="Real Estate"
sector9 = "Telecommunication Services"
sector10 = "Utilities"
# add rows of data to sales database

# for i in range(sCount):
    
#    data = sData[i]
     
#    symbol = data['ticker'] # text
#    sActual = data['sales_actual'] # integer    
#    sEstimatedDiff = ['sales_mean_estimate'] # integer
#    sAmountDiff = data['sales_amount_diff'] # integer
#    sPercentDiff = data['sales_percent_diff'] # real
#    sDev = data['sales_std_dev_estimate'] # integer
#    sReportDate = d.date(data['actual_reported_date']) # text/datetime object
  
#    sRowVec = {symbol, sActual, sEstimatedDiff, sAmountDiff, sPercentDiff, sDev}
    
#    addRow(salesPath, sReportDate, salesTable, salesColVec, sRowVec)
      

# add rows of data to earnings datebase   

#for i in range(eCount):
    
#    data = eData[i] # holds all of the following data
    
#    symbol = data['ticker'] # text
#    eActual = data['eps_actual'] # integer    
#    eEstimatedDiff = ['eps_mean_estimate'] # integer
#    eAmountDiff = data['eps_amount_diff'] # integer
#    ePercentDiff = data['eps_percent_diff'] # real
#    eDev = data['eps_std_dev_estimate'] # integer
#    eCount = data['eps_count_estimate'] # integer
#    eFiscYr = data['fiscal_year'] # text
#    eReportDate = d.date(data['actual_reported_date']) # text/datetime object
#    eReportTime = data['actual_reported_time'] # text
#    eReportDesc = data['actual_reported_desc'] # text
  
#    eRowVec = {symbol, eActual, eEstimatedDiff, eAmountDiff, ePercentDiff, eDev, eCount, eFiscYr,\
#               eReportTime, eReportDesc}
    
#    addRow(earningsPath, eReportDate, earningsTable, earningsColVec, eRowVec)  





    ################ get sentiment data ###################
  

sentPath = "https://api.intrinio.com/news_sentiments"
  
sent_params = {     
        
        'identifier':symbol,
        'start_date':prev_90,
        'end_date':next_90,
        'page_size':90,
        'source':'tip-ranks'
    
            }

sentiment_response = r.get(sentPath, params=sent_params, auth=(uname, pw) )
if sentiment_response.status_code == 401: print("Null sales query, please check user name and password"); exit()

sentiment_json = sentiment_response.json()
sentCount = sentiment_json['result_count']
sentimentData = sentiment_json['data']
    
    # get sentiment data for a 90 day radius of earnings for ticker and sector

    ################ ticker sentiment ##################
print(sentCount)
    
for i in range( sentCount ):
        
    data = sentimentData[i] 
    
    sentimentDF.loc[i, 'eDate'] = data['date']

    sector = data['sector']
    sentimentDF.loc[i,'ticker'] = symbol
    sentimentDF.loc[i,'sector'] = data['sector']
    sentimentDF.loc[i, 'blw1'] = data['bullish_1w']
    sentimentDF.loc[i, 'blw4'] = data['bullish_4w']
    sentimentDF.loc[i, 'blw12'] = data['bullish_12w']
        
    sentimentDF.loc[i, 'brw1'] = data['bearish_1w']
    sentimentDF.loc[i, 'brw4'] = data['bearish_4w']
    sentimentDF.loc[i, 'brw12'] = data['bearish_12w']
        
    sentimentDF.loc[i, 'bzw1w4'] = data['buzz_1w4w']
    sentimentDF.loc[i, 'bzw1w12'] = data['buzz_1w12w']
    sentimentDF.loc[i, 'bzw4w12'] = data['buzz_4w12w']
        
    # sentimentRowVec = [symbol, sector, blw1, blw4, blw12, brw1, brw4, brw12, bz1w4w, bz1w12w, bz4w12w]
    # addRow(sentimentPath, date, sentTable, sentimentColVec, sentimentRowVec)  


        ############### sector sentiment #####################
   
sector_params = {
                
            'sector':sector,
            'start_date':prev_90,
            'end_date':next_90,
            'source':'tip-ranks'
                
            }
    
sector_response = r.get(sentPath, params=sector_params, auth=(uname, pw) )
if sector_response.status_code == 401: print("Null sector query, please check user name and password"); exit()
    
sectorSentiments = sector_response.json()
sectorData = sectorSentiments['data']    
count = sectorSentiments['result_count']
print(count)   
    
for dex in range( count ):
        
    sData = sectorData[dex]
    date = sData['date']
        
    sectorDF.loc[dex, 'eDate'] = date
    
    sectorDF.loc[dex, 'sector'] = sData['sector']    
    sectorDF.loc[dex, 'blw1'] = sData['bullish_1w']
    sectorDF.loc[dex, 'blw4'] = sData['bullish_4w']
    sectorDF.loc[dex, 'blw12'] = sData['bullish_12w']
        
    sectorDF.loc[dex, 'brw1'] = sData['bearish_1w']
    sectorDF.loc[dex, 'brw4'] = sData['bearish_4w']
    sectorDF.loc[dex, 'brw12'] = sData['bearish_12w']
        
    sectorDF.loc[dex, 'bzw1w4'] = sData['buzz_1w4w']
    sectorDF.loc[dex, 'bzw1w12'] = sData['buzz_1w12w']
    sectorDF.loc[dex, 'bzw4w12'] = sData['buzz_4w12w']
   
        # sectorRowVec = [sector, blw1, blw4, blw12, brw1, brw4, brw12, bz1w4w, bz1w12w, bz4w12w]
        # addRow(sectorPath, date, sectorTable, sectorColVec, sectorRowVec) 
        
        #TODO: join sentiment results based on date, sector and ticker, also, look for leading sentiment changes
        # from sector to ticker, and lagging sector changes if/when ticker makes large move on earnings day
        
    
    ########### all dataframes should now be made ###############
        

    # get daily OHLC data for resistance and support calculations and sentiment correlation comparisons
        
    dailyData = getDailyData(symbol)
            
    # range is beteen 5 and 30 supports and resistances 
        
    x = ran.randint(5, 30)
            
    # binary variation between reistances and supports for when the phi data structures are made
        
    isRes = True
    isSup = False
            
    # enumerate column values
       
    opn = "Open"
    hi = "High"
    lo = "Low"
    cls = "Close"
        
    # calculate phi values based on n resistances/supports and earnings value of given column
        
    res = getPhi(x, isRes, dailyData, cls, eDate, cls)
    sup = getPhi(x, isSup, dailyData, cls, eDate, cls)
      
    # write the raw resistance and support dataframes to csv
        
    resOut = "Users/Jay/Documents/phiData/" + symbol + ".rawResData.csv"
    supOut = "Users/Jay/Documents/phiData/" + symbol + ".rawSupData.csv"
        
    resOut.to_csv(resOut, sep=',', encoding='utf-8')
    supOut.to_csv(supOut, sep=',', encoding='utf-8')
        
    # count relevant stats for each phi data structure
        
    rPhi = countPhi(res)
    sPhi = countPhi(sup)
        
    # write the stats to a csv
        
    rOut = "Users/Jay/Documents/phiData/" + symbol + ".resistanceData.csv"
    sOut = "Users/Jay/Documents/phiData/" + symbol + ".supportData.csv"
        
    rPhi.to_csv(rOut, sep=',', encoding='utf-8')
    sPhi.to_csv(sOut, sep=',', encoding='utf-8')
                

    ################ all support and resistance data now calculated and written #########################
        
    # TODO: calculate correlation between sentiment data for symbol, sector and corresponding
    # phi-based price supports and resistance values 90 days before and after earnings date. 
    # look for signals in sales data for magnitude of earnings price change
            
    