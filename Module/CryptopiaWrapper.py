#!/usr/bin/python

import base64, hashlib, hmac, json, requests, sys, time
from . import six

WT = 30

NonceTimeFactor = 3
def NonceValue(NonceTimeFactor):
    Nonce = str( int( time.time() * NonceTimeFactor - 4361732500 ) )
    return Nonce

class CryptopiaWrapper:

    def __init__(self, PublicKey, PrivateKey):
        self._PublicKey = PublicKey
        self._PrivateKey = PrivateKey

    def query(self, method, req = {}):
        time.sleep(1.0 / float(NonceTimeFactor) + 0.01)
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
        else:
            assert False, 'API Method <%s> not defined'%method

        result = r.json()
        assert result['Success'], result['Error']
        return result['Data']

    ##### Public:
    def getCurrencies(self):
        return self.query("GetCurrencies")

    def getMarkets(self):
        return self.query("GetMarkets")

    def getMarket(self, Id):
        return self.query("GetMarket", [ Id ] )

    def getTradePairs(self):
        return self.query("GetTradePairs")

    def getMarketOrders(self, Id, depth):
        return self.query("GetMarketOrders", [ Id, depth ] )

    ##### Private:
    def submitTrade(self, Id, Type, Rate, Amount):
        # Amount is in units of top currency (e.g. if I'm placing a 'buy' order on
        # XVG/BTC at rate 0.00001119, for amount = 10.0, I'm saying I want to buy
        # 10.0 XVG using BTC at exchange rate 0.00002 BTC/XVG. That will cost me
        # 0.0002 BTC. I believe the 0.2% fee comes out of that.
        return self.query("SubmitTrade", {'TradePairId':Id, 'Type':Type, 'Rate':Rate, 'Amount':Amount})

    def getBalance(self, Id):
        return self.query("GetBalance", {'Currency':Id})

    def tip(self, Coin, User, Sum):
        return self.query("SubmitTip", {'Currency':Coin, 'ActiveUsers':User, 'Amount':Sum})

    def getOpenOrders(self, Id):
        return self.query("GetOpenOrders", {'TradePairId': Id})

    def submitTransfer(self, currency, user, amount):
        return self.query("SubmitTransfer", {'Currency':currency, 'Username':user, 'Amount':amount})
