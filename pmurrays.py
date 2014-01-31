#! /usr/bin/python

from bs4 import BeautifulSoup
import requests
import pickle
import logging
import datetime
import datetime


PRICE_REQ_URL = 'https://online.murrayscoaches.com.au/MurraysCoaches/MOProcessQueryString.aspx?Origin={origin}&Destination={dest}&DepartureDate={date}&ReturningDate=&Adult=1&Concession=0&Senior=0&Pensioner=0&Student=0&Child=0'

PRICE_TABLE_ID = 'ctl00_ContentPlaceHolder1_{}|1'

TRIPS = [('JOLI', 'EDDY'), ('EDDY', 'JOLI')]

PICKLE_FILE = 'pmurrays.pickle'

PICKLE_DATA = 'pmurrays_stats.pickle'

SWEEP_DAYS_AHEAD = 28

EMPTY_STATS = {
        'avg_prices': {
            'alltime': [0, 0], 
            'mon': [0,0],
            'tue': [0,0],
            'wed': [0,0],
            'thu': [0,0],
            'fri': [0,0],
            'sat': [0,0],
            'sun': [0,0],
            'depart_time': [0 for i in range(24)]
            },
        'min_prices': {
            'alltime': [0, 0], 
            'mon': [0,0],
            'tue': [0,0],
            'wed': [0,0],
            'thu': [0,0],
            'fri': [0,0],
            'sat': [0,0],
            'sun': [0,0],
            'depart_time': [0 for i in range(24)]
            },
        'max_prices': {
            'alltime': [0, 0], 
            'mon': [0,0],
            'tue': [0,0],
            'wed': [0,0],
            'thu': [0,0],
            'fri': [0,0],
            'sat': [0,0],
            'sun': [0,0],
            'depart_time': [0 for i in range(24)]
            },
        'avg_price_day_ahead': [0 for i in range(SWEEP_DAYS_AHEAD)]
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

def updateStats(todaysdata):

    with open(PICKLE_DATA, 'rw') as f:
        try: stats = pickle.load(f)       
        except EOFError:stats = EMPTY_STATS 

        stats['avg']
            

def controller():
    todaysdata = priceSweep()
    with open(PICKLE_FILE, 'w+') as f:
        pickle.dump(todaysdata, f)
    
    updateStats(todaysdata)

def main():
	controller()

if __name__ == '__main__':
	main()
