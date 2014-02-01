#! /usr/bin/python

from bs4 import BeautifulSoup
import requests
import pickle
import logging
import datetime
import datetime
import pprint


PRICE_REQ_URL = 'https://online.murrayscoaches.com.au/MurraysCoaches/MOProcessQueryString.aspx?Origin={origin}&Destination={dest}&DepartureDate={date}&ReturningDate=&Adult=1&Concession=0&Senior=0&Pensioner=0&Student=0&Child=0'

PRICE_TABLE_ID = 'ctl00_ContentPlaceHolder1_{}|1'

TRIPS = [('JOLI', 'EDDY'), ('EDDY', 'JOLI')]

PICKLE_FILE = 'pmurrays.pickle'

PICKLE_DATA = 'pmurrays_stats.pickle'

SWEEP_DAYS_AHEAD = 28

DAYS_OF_WEEK = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

EMPTY_STATS = {
        'avg_prices': {
            'alltime': [0, 0], 
            'days': [[0, 0] for i in range(len(DAYS_OF_WEEK))],
            'depart_time': [[0, 0] for i in range(24)]
            },
        'min_prices': {
            'alltime': [0, 9999], 
            'days': [[0, 9999] for i in range(len(DAYS_OF_WEEK))],
            'depart_time': [[0, 9999] for i in range(24)]
            },
        'max_prices': {
            'alltime': [0, 0], 
            'days': [[0, 0] for i in range(len(DAYS_OF_WEEK))],
            'depart_time': [[0, 0] for i in range(24)]
            },
        'avg_price_day_ahead': [[0,0] for i in range(SWEEP_DAYS_AHEAD)]
        }

def getPricing(origin, dest, date):
    logger = logging.getLogger('getpricing') 
    ret = []

    logger.debug('Requesting {}'.format(PRICE_REQ_URL.format(origin=origin, dest=dest, date=date)))
    s = requests.Session()
    resp = s.get(PRICE_REQ_URL.format(origin=origin, dest=dest, date=date))
    
    if not resp or resp.status_code != 200:
        logger.error('Cannot get pricing')
        return ret

    murrarySoup = BeautifulSoup(resp.content)

    for i in range(1, 40):
        priceTable = murrarySoup.find(id=PRICE_TABLE_ID.format(i))
        if priceTable:
            departTime = priceTable.contents[4].text.strip()
            price      = priceTable.contents[6].text.strip()
            logger.debug('Found {} = {}'.format(departTime, price))
            ret.append((departTime,price))
    return ret

def dateGen(number):
    today = datetime.datetime.today()
    for i in range(1, number+1):
        yield today.strftime('%d/%m/%Y')
        today += datetime.timedelta(days=1)

def priceSweep():
    pricedata = {'starttime': datetime.datetime.today()}
    for origin, dest in TRIPS:
        tripname = '{}:{}'.format(origin, dest)
        pricedata[tripname] = {}
        for date in dateGen(SWEEP_DAYS_AHEAD):
            priceData = getPricing(origin, dest, date)
            if priceData:
                pricedata[tripname][date] = priceData
    pricedata['endtime'] = datetime.datetime.today()
    return pricedata

def priceStr2Float(prices):
    if isinstance(prices, list) or isinstance(prices, tuple):
        return [float(str(p.strip('$ '))) for p in prices if p != '']
    else:
        if prices != '':
            return float(str(prices.strip('$ ')))
        else:
            return None

def calAllTimeStats(todaysdata, stats):
    prices = []
    minpricecount, minpriceval = stats['min_prices']['alltime']
    maxpricecount, maxpriceval = stats['max_prices']['alltime']
    avgcount, avgprice = stats['max_prices']['alltime']

    for origin, dest in TRIPS:
        tripname = '{}:{}'.format(origin, dest)
        for date in todaysdata[tripname].keys():
            t, price = zip(*todaysdata[tripname][date])
            price = priceStr2Float(price)
            prices.extend(price)
            if minpriceval > min(price):
                minpriceval = min(price)
            if maxpriceval < max(price):
                maxpriceval  = max(price)

    avgcount      += len(prices)
    minpricecount += len(prices)
    maxpricecount += len(prices)

    stats['min_prices']['alltime'] = [minpricecount, minpriceval]
    stats['max_prices']['alltime'] = [maxpricecount, maxpriceval]
    stats['avg_prices']['alltime'] = [avgcount, avgprice + sum(prices)/avgcount]

def calDaysStats(todaysdata, stats):
    prices = [[] for i in range(len(DAYS_OF_WEEK))]
    avgdays = stats['avg_prices']['days']
    mindays = stats['min_prices']['days']
    maxdays = stats['max_prices']['days']
    for origin, dest in TRIPS:
        tripname = '{}:{}'.format(origin, dest)
        for date in todaysdata[tripname].keys():
            dayid = datetime.datetime.strptime(date, '%d/%m/%Y').weekday()

            t, price = zip(*todaysdata[tripname][date])
            price = priceStr2Float(price)
            # avgs
            prices[dayid].extend(price)
            # min
            mindays[dayid][0] += len(price)
            maxdays[dayid][0] += len(price)
            if mindays[dayid][1] > min(price):
                mindays[dayid][1] = min(price)
            # max
            if maxdays[dayid][1] < max(price):
                maxdays[dayid][1] = max(price)

    stats['min_prices']['days'] = mindays
    stats['max_prices']['days'] = maxdays
   
    # update avgs
    for i in range(len(DAYS_OF_WEEK)):
        count = len(prices[i])
        avgdays[i][0] += count
        avgdays[i][1] += sum(prices[i])/avgdays[i][0]
    stats['avg_prices']['days'] = avgdays

def calDepartStats(todaysdata, stats):
    prices = [[] for i in range(24)]
    avgdepart = stats['avg_prices']['depart_time']
    mindepart = stats['min_prices']['depart_time']
    maxdepart = stats['max_prices']['depart_time']
    for origin, dest in TRIPS:
        tripname = '{}:{}'.format(origin, dest)
        for date in todaysdata[tripname].keys():
            for time, price in todaysdata[tripname][date]:
                timeid = datetime.datetime.strptime(time, '%I:%M%p').hour
                price = priceStr2Float(price)
                if price:
                    # avgs
                    prices[timeid].append(price)
                    # min
                    mindepart[timeid][0] += 1
                    maxdepart[timeid][0] += 1
                    if mindepart[timeid][1] > price:
                        mindepart[timeid][1] = price
                    # max
                    if maxdepart[timeid][1] < price:
                        maxdepart[timeid][1] = price

    stats['min_prices']['depart_time'] = mindepart
    stats['max_prices']['depart_time'] = maxdepart
    for i in range(24):
        count = len(prices[i])
        avgdepart[i][0] += count
        if avgdepart[i][0]:
            avgdepart[i][1] += sum(prices[i])/avgdepart[i][0]
    stats['avg_prices']['depart_time'] = avgdepart

def calDaysAheadStats(todaysdata, stats):
    prices = [[] for i in range(SWEEP_DAYS_AHEAD)]
    avgdaysahead = stats['avg_price_day_ahead']
    today = todaysdata['starttime']
    for origin, dest in TRIPS:
        tripname = '{}:{}'.format(origin, dest)
        for date in todaysdata[tripname].keys():

            t, price = zip(*todaysdata[tripname][date])
            price = priceStr2Float(price)

            d = datetime.datetime.strptime(date, '%d/%m/%Y')
            daysahead = (d - today).days

            if daysahead >= 0:
                prices[daysahead].extend(price)

    for i in range(SWEEP_DAYS_AHEAD):
        count = len(prices[i])
        avgdaysahead[i][0] += count
        if avgdaysahead[i][0]:
            avgdaysahead[i][1] += sum(prices[i])/avgdaysahead[i][0]
    stats['avg_price_day_ahead'] = avgdaysahead

def updateStats(todaysdata):

    with open(PICKLE_DATA, 'w+') as f:
        try: stats = pickle.load(f)       
        except EOFError:stats = EMPTY_STATS 

        calAllTimeStats(todaysdata, stats)
        calDaysStats(todaysdata, stats)
        calDepartStats(todaysdata, stats)
        calDaysAheadStats(todaysdata, stats)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(stats)


def controller():
   # todaysdata = priceSweep()
   # with open(PICKLE_FILE, 'w+') as f:
   #     pickle.dump(todaysdata, f)
    
    with open(PICKLE_FILE, 'r') as f:
        todaysdata = pickle.load(f)
        updateStats(todaysdata)

def main():
	controller()

if __name__ == '__main__':
	main()
