#! /usr/bin/python

from bs4 import BeautifulSoup
import requests
import pickle
import logging


PRICE_REQ_URL = 'https://online.murrayscoaches.com.au/MurraysCoaches/MOProcessQueryString.aspx?Origin={origin}&Destination={dest}&DepartureDate={date}&ReturningDate=&Adult=1&Concession=0&Senior=0&Pensioner=0&Student=0&Child=0'

PRICE_TABLE_ID = 'ctl00_ContentPlaceHolder1_{}|1'

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

    for i in range(1, 19):
        priceTable = murrarySoup.find(id=PRICE_TABLE_ID.format(i))
        if priceTable:
            departTime = priceTable.contents[4].text.strip()
            price      = priceTable.contents[6].text.strip()
            logger.debug('Found {} = {}'.format(departTime, price))
            ret.append((departTime,price))
    return ret

def controller():
    for i in range(1,30):
        print i
        print getPricing('JOLI', 'EDDY', '{:02}/02/2014'.format(i))

def main():
	controller()

if __name__ == '__main__':
	main()













































