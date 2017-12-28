#!/usr/bin/python
import time
import json
import sys, os
import ConfigParser
from WrapperCryptopia import Cryptopia


cfgloc = os.path.join(sys.path[0], 'config', 'Interface.ini')
config = ConfigParser.ConfigParser()
config.read(cfgloc)
ConfDict = {}
for section in config.sections():
    ConfDict[section] = {}
    for option in config.options(section):
        ConfDict[section][option] = config.get(section, option)

if (len(ConfDict) == 0):
    print " "
    print " !!! ERROR !!!"
    print " Interface.ini not found in 'config' directory!"
    exit()

TimeInterval = int(ConfDict['Main_Settings']['sleep_on_error'])
repeats = int(ConfDict['Main_Settings']['repeats_on_error'])


class Api:

    def __init__(self, Action, ActionData, OutputFormat):
        self._action = Action
        self._data = ActionData
        self.FormatedList = {}
        self.OutputFormat = OutputFormat # R = raw, F = formated
        self.timestamp = timestr = time.strftime("%Y") + "-" + time.strftime("%m") + "-" + time.strftime("%d") + " " + time.strftime("%H") + ":" + time.strftime("%M") + ":" + time.strftime("%S")



    def Cryptopia(self):
        PublicKey = str(ConfDict['Cryptopia']['public_key']) 
        PrivateKey = str(ConfDict['Cryptopia']['private_key']) 
                
        def respond():
            repeat = 0
            while repeat <= repeats :
                print self.timestamp, "/ Interface / Cryptopia:", str(self._action),
                y = Cryptopia(PublicKey, PrivateKey)
                ExchangeData = request(y)
                json_data = json.loads(ExchangeData)
                #print json_data
                if (isinstance(json_data, (dict)) == True):
                    try:
                        if ( str(json_data['Success']) == "True" ):
                            repeat = repeats
                            print ("/ Success:"), json_data['Success']
                            return json_data
                        else:
                            repeat = repeat + 1
                            print ("/ Success:"), json_data['Success'], (", try Task again in"), TimeInterval, ("sec.")
                            print str(json_data)
                            time.sleep(TimeInterval)
                    except KeyError, e:
                        repeat = repeat + 1
                        print ("/ Success: no, try Task again in"), TimeInterval, ("sec.")
                        print "JSON", e, "->", str(ExchangeData), "<-"
                        time.sleep(TimeInterval)                        
                else:
                    repeat = repeat + 1
                    print ("/ Success: no, try Task again in"), TimeInterval, ("sec.")
                    print "no JSON data provided: ->", str(ExchangeData), "<-"
                    time.sleep(TimeInterval)

        ##### public access
        if ( self._action == "GetCurrencies" ):
            def request(y):
                ExchangeData = y.GetCurrencies()
                return ExchangeData
            if ( self.OutputFormat == "R"):
                return respond()
            elif ( self.OutputFormat == "F"):
                ApiString = respond()
                self.FormatedList.update({'Currencies':[]})
                for element in ApiString['Data']:
                    self.FormatedList['Currencies'].append([ str(element['Symbol']), int(element['Id']), str(element['Name']) ])
                return self.FormatedList
        if ( self._action == "GetTradePairs" ):
            def request(y):
                ExchangeData = y.GetTradePairs()
                return ExchangeData
            return respond()
        if ( self._action == "GetMarkets" ):
            def request(y):
                ExchangeData = y.GetMarkets()
                return ExchangeData
            return respond()
        if ( self._action == "GetMarketSummaries" ):
            def request(y):
                ExchangeData = y.GetMarkets()
                return ExchangeData
            if ( self.OutputFormat == "R"):
                return respond()
            elif ( self.OutputFormat == "F"):
                ApiString = respond()
                self.FormatedList.update({'MarketSummaries':{}})
                for element in ApiString['Data']:
                    self.FormatedList['MarketSummaries'].update({str(element['TradePairId']):[str(element['Label']), float(element['AskPrice']), float(element['BidPrice'])]})
                return self.FormatedList

        if ( self._action == "GetMarketSummary" ):
            def request(y):
                ExchangeData = y.GetMarket(self._Id)
                return ExchangeData
            return respond()
        if ( self._action == "GetOrderbook" ):
            def request(y):
                ExchangeData = y.GetMarketOrders(self._data[0], self._data[1])
                return ExchangeData
            if ( self.OutputFormat == "R"):
                return respond()
            elif ( self.OutputFormat == "F"):
                ApiString = respond()
                self.FormatedList.update({'BuyOrderbook':[],'SellOrderbook':[]})
                count = 1
                for element in ApiString['Data']['Buy']:
                    if (count <= self._data[1]):
                        self.FormatedList['BuyOrderbook'].append([ float(element['Price']), float(element['Volume']), float(float(element['Volume']) * float(element['Price'])) ])
                    count = count + 1
                count = 1
                for element in ApiString['Data']['Sell']:
                    if (count <= self._data[1]):
                        self.FormatedList['SellOrderbook'].append([ float(element['Price']), float(element['Volume']), float(float(element['Volume']) * float(element['Price'])) ])       
                    count = count + 1
                return self.FormatedList
        ##### public access
        if ( self._action == "SubmitOrder" ):
            def request(y):
                ExchangeData = y.SubmitTrade(self._data[0], self._data[1], round(self._data[2], 8), round(self._data[3], 8)) #0=Id, 1=Type, 2=Price, 3=Amount
                return ExchangeData
            return respond()
        if ( self._action == "SubmitTip" ):
            def request(y):
                ExchangeData = y.Tip(self._data[0], self._data[1], round(self._data[2], 8))
                return ExchangeData
            return respond()
        if ( self._action == "GetBalances" ):
            def request(y):
                ExchangeData = y.GetBalance(self._data)
                return ExchangeData
            if ( self.OutputFormat == "R"):
                return respond()
            elif ( self.OutputFormat == "F"):
                ApiString = respond()
                self.FormatedList.update({'Balances':{}})
                for element in ApiString['Data']:
                    self.FormatedList['Balances'].update({str(element['Symbol']):[float(element['Available']), float(element['Total'])]})
                return self.FormatedList
