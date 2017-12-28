#!/usr/bin/python

import time
import hmac
import requests
import hashlib
import base64
import sys
import json
from . import six

WT = 30

NonceTimeFactor = 3
def NonceValue(NonceTimeFactor):
    Nonce = str( int( time.time() * NonceTimeFactor - 4361732500 ) )
    return Nonce

class Cryptopia:

    def __init__(self, PublicKey, PrivateKey):
        self._PublicKey = PublicKey
        self._PrivateKey = PrivateKey

    def api_query(self, method, req = None ):
        while True:
            try:
                if not req:
                    req = {}
                time.sleep(float(1) / float(NonceTimeFactor) + float(0.01))
                public_set = set([ "GetCurrencies", "GetTradePairs", "GetMarkets", "GetMarket", "GetMarketHistory", "GetMarketOrders" ])
                private_set = set([ "GetBalance", "GetDepositAddress", "GetOpenOrders", "GetTradeHistory", "GetTransactions", "SubmitTrade", "CancelTrade", "SubmitTip" ])
                if method in public_set:
                    url = "https://www.cryptopia.co.nz/api/" + method
                    if req:
                       for param in req:
                           url += '/' + str( param )
                    r = requests.get( url )

                elif method in private_set:
                    repeat = 3
                    while repeat >= 1:
                        url = "https://www.cryptopia.co.nz/Api/" + method
                        nonce = NonceValue(NonceTimeFactor)
                        post_data = six.b(json.dumps(req))
                        m = hashlib.md5()
                        m.update(post_data)
                        requestContentBase64String = base64.b64encode(m.digest())
                        signature = six.b(self._PublicKey + "POST" + six.moves.urllib.parse.quote_plus( url ).lower() + nonce) + requestContentBase64String
                        hmacsignature = base64.b64encode(hmac.new(base64.b64decode(self._PrivateKey), signature, hashlib.sha256).digest())
                        header_value = "amx " + self._PublicKey + ":" + hmacsignature.decode('utf-8') +  ":" + nonce
                        headers = { 'Authorization': header_value, 'Content-Type':'application/json; charset=utf-8' }
                        r = requests.post( url, data = post_data, headers = headers )
                        if (str(r) == str('<Response [200]>')):
                            repeat = 0
                        elif (str(r) == str('<Response [503]>')):
                            repeat = 2
                            six.print_(r, "The server is currently unavailable.")
                            time.sleep( 60 )
                        elif (str(r) == str('<Response [429]>')):
                            repeat = 0
                            six.print_(r, "Too many requests in a given amount of time.")
                            time.sleep( 5 )
                        else:
                            repeat = repeat - 1
                            six.print_(r)
                            time.sleep( 1 )
            except Exception as e:
                six.print_(e)
                six.print_("try to reconnect in" , WT, "sec.")
                time.sleep(WT)
            else:
                response = r.text
                return response

                break

    ##### Public:
    def GetCurrencies(self):
        return self.api_query("GetCurrencies")
        
    def GetMarkets(self):
        return self.api_query("GetMarkets")

    def GetMarket(self, Id):
        return self.api_query("GetMarket", [ Id ] )

    def GetTradePairs(self):
        return self.api_query("GetTradePairs")

    def GetMarketOrders(self, Id, depth):
        return self.api_query("GetMarketOrders", [ Id, depth ] )

    ##### Private:
    def SubmitTrade(self, Id, Type, Rate, Amount):
        return self.api_query("SubmitTrade", {'TradePairId':Id, 'Type':Type, 'Rate':Rate, 'Amount':Amount})

    def GetBalance(self, Id):
        return self.api_query("GetBalance", {'Currency':Id})

    def Tip(self, Coin, User, Sum):
        return self.api_query("SubmitTip", {'Currency':Coin, 'ActiveUsers':User, 'Amount':Sum})
