#!/usr/bin/python

import json, os, sys, time
from .WrapperCryptopia import CryptopiaWrapper
from . import six

cfgloc = os.path.join(sys.path[0], 'config', 'Interface.ini')
assert os.path.isfile(cfgloc), '' \
        + ' !!! ERROR !!!' \
        + ' config/Interface.ini not found.'

config = six.moves.configparser.ConfigParser()
config.read(cfgloc)
ConfDict = config.__dict__['_sections']

TimeInterval = int(ConfDict['Main_Settings']['sleep_on_error'])
repeats = int(ConfDict['Main_Settings']['repeats_on_error'])

class Api:

    def __init__(self, Action, ActionData, OutputFormat):
        self._action = Action
        self._data = ActionData
        self.FormatedList = {}
        self.OutputFormat = OutputFormat # R = raw, F = formated

    def Cryptopia(self):
        PublicKey   = ConfDict['Cryptopia']['public_key']
        PrivateKey  = ConfDict['Cryptopia']['private_key']

        def respond(callback_req):
            repeat = 0
            while repeat <= repeats :
                six.print_(time.strftime('%Y-%m-%d %H:%M:%S'), "/ Interface / Cryptopia:", self._action, end=' ', flush=True)
                y = CryptopiaWrapper(PublicKey, PrivateKey)
                ExchangeData = callback_req(y)
                json_data = json.loads(ExchangeData)
                if (isinstance(json_data, (dict)) == True):
                    try:
                        if ( str(json_data['Success']) == "True" ):
                            repeat = repeats
                            six.print_("/ Success:", json_data['Success'])
                            return json_data
                        else:
                            repeat = repeat + 1
                            six.print_("/ Success:", json_data['Success'], ", try Task again in", TimeInterval, "sec.")
                            six.print_(str(json_data))
                            time.sleep(TimeInterval)
                    except KeyError as e:
                        repeat = repeat + 1
                        six.print_("/ Success: no, try Task again in", TimeInterval, "sec.")
                        six.print_("JSON", e, "->", str(ExchangeData), "<-")
                        time.sleep(TimeInterval)
                else:
                    repeat = repeat + 1
                    six.print_("/ Success: no, try Task again in", TimeInterval, "sec.")
                    six.print_("no JSON data provided: ->", str(ExchangeData), "<-")
                    time.sleep(TimeInterval)

        ##### public access
        if ( self._action == "GetCurrencies" ):
            def request(y):
                ExchangeData = y.GetCurrencies()
                return ExchangeData
            if ( self.OutputFormat == "R"):
                return respond(request)
            elif ( self.OutputFormat == "F"):
                ApiString = respond(request)
                self.FormatedList.update({'Currencies':[]})
                for element in ApiString['Data']:
                    self.FormatedList['Currencies'].append([ str(element['Symbol']), int(element['Id']), str(element['Name']) ])
                return self.FormatedList
        if ( self._action == "GetTradePairs" ):
            def request(y):
                ExchangeData = y.GetTradePairs()
                return ExchangeData
            return respond(request)
        if ( self._action == "GetMarkets" ):
            def request(y):
                ExchangeData = y.GetMarkets()
                return ExchangeData
            return respond(request)
        if ( self._action == "GetMarketSummaries" ):
            def request(y):
                ExchangeData = y.GetMarkets()
                return ExchangeData
            if ( self.OutputFormat == "R"):
                return respond(request)
            elif ( self.OutputFormat == "F"):
                ApiString = respond(request)
                self.FormatedList.update({'MarketSummaries':{}})
                for element in ApiString['Data']:
                    self.FormatedList['MarketSummaries'].update({str(element['TradePairId']):[str(element['Label']), float(element['AskPrice']), float(element['BidPrice'])]})
                return self.FormatedList

        if ( self._action == "GetMarketSummary" ):
            def request(y):
                ExchangeData = y.GetMarket(self._Id)
                return ExchangeData
            return respond(request)
        if ( self._action == "GetOrderbook" ):
            def request(y):
                ExchangeData = y.GetMarketOrders(self._data[0], self._data[1])
                return ExchangeData
            if ( self.OutputFormat == "R"):
                return respond(request)
            elif ( self.OutputFormat == "F"):
                ApiString = respond(request)
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
            return respond(request)
        if ( self._action == "SubmitTip" ):
            def request(y):
                ExchangeData = y.Tip(self._data[0], self._data[1], round(self._data[2], 8))
                return ExchangeData
            return respond(request)
        if ( self._action == "GetBalances" ):
            def request(y):
                ExchangeData = y.GetBalance(self._data)
                return ExchangeData
            if ( self.OutputFormat == "R"):
                return respond(request)
            elif ( self.OutputFormat == "F"):
                ApiString = respond(request)
                self.FormatedList.update({'Balances':{}})
                for element in ApiString['Data']:
                    self.FormatedList['Balances'].update({str(element['Symbol']):[float(element['Available']), float(element['Total'])]})
                return self.FormatedList
