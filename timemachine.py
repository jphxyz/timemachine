#!/usr/bin/env python

'''
Copyright (c) 2016, CoinUser
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither Cryptopia nor the names of this code's contributors may be
      used to endorse or promote products derived from this software without
      specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL CoinUser BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

'''
Original code by CoinUser can be found in this forum post:
https://www.cryptopia.co.nz/Forum/Thread/544

Unclear what license to use because none was specified in original forum post,
but their comments suggest something like a BSD 3-clause license, which is what
I'm including here. It's also possible they wanted it to be in the public domain,
but BSD seems more appropriate and not much more restrictive anyway.
'''

import json, os, sys, time
from Module import six
from Module.Interface import Api

### get api data
def Wrapper(Exchange, Action, ActionData):
    # TODO: Don't make a new API object every time!
    GetCoins = Api(Action, ActionData, 'F')
    api_function = getattr(GetCoins, Exchange)
    return api_function()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Dramatic startup messages
zzz = 0.07
six.print_(' ---------------------------------------------------------------------------')
six.print_('')
sys.stdout.write('{:<26}'.format(''))
for letter in 'TIMEMACHINE':
    sys.stdout.write(' ' + letter)
    time.sleep(zzz)
    sys.stdout.flush()
six.print_('\n')
time.sleep(zzz)
six.print_('{:^76}'.format('advanced auto-sell program'))
time.sleep(zzz)
six.print_('{:^76}'.format('for CRYPTOPIA'))
time.sleep(zzz * 7)
six.print_('{:>76}'.format('by CoinUser'))
six.print_(' ---------------------------------------------------------------------------')

### read and validate config file
cfgloc = os.path.join(sys.path[0], 'config', 'timemachine.ini')
assert os.path.isfile(cfgloc), '' \
        + ' !!! ERROR !!!' \
        + ' config/timemachine.ini not found.'

config = six.moves.configparser.ConfigParser()
config.read(cfgloc)
ConfDict        = config.__dict__['_sections']
BuyCoin         = ConfDict['Main_Settings']['coin_to_buy']
SleepInterval   = int(ConfDict['Main_Settings']['sleep_minutes']) * 60
DemoMode        = int(ConfDict['Demo_Mode']['active'])
SellPercent     = float(ConfDict['Main_Settings']['sell_percent_of_available_balance']) * 0.01
Fee             = float(ConfDict['Missing_API_Data']['tradefee'])
BaseTradeMin    = json.loads(ConfDict['Missing_API_Data']['basemintrade'])
Suspended       = list(json.loads(ConfDict['Missing_API_Data']['suspendedmarkets']))
TipActive       = int(ConfDict['Submit_Tip']['active'])
TipCoin         = ConfDict['Submit_Tip']['coin']
TipAmount       = int(ConfDict['Submit_Tip']['tip_amount_per_user'])
TipUsers        = int(ConfDict['Submit_Tip']['to_last_active_users'])
TipMinAmount    = json.loads(ConfDict['Missing_API_Data']['minimumtipamounts'])
SellCoins       = {k.upper(): float(v) for k, v in six.iteritems(ConfDict['Coins_To_SELL_and_Stop_at_Balance']) if k not in ('symbol', '__name__')}

assert BuyCoin.upper() not in SellCoins, '' \
        + ' !!! ERROR !!!' \
        + ' The coin you want to purchase is in the list of coins to sell!\n' \
        + ' Please edit timemachine.ini and erase %s from the list.\n' \
        + ' Or choose a different coin to buy.'

while True:
    ### Get balances and decide how much of what to sell
    Balances = Wrapper('Cryptopia', 'GetBalances', '')['Balances']
    BalanceList = []
    ListSell = []
    for commodity, stopbalance in six.iteritems(SellCoins):
        balance     = Balances[commodity][0]
        available   = balance - stopbalance
        sellfrac    = balance * SellPercent
        sellamount  = max(0.0, min(available, sellfrac))

        BalanceList.append((commodity, balance, stopbalance, sellamount))
        if (sellamount > 0):
            ListSell.append(commodity)

    six.print_('\n ---------------')
    demomodewarning = bcolors.WARNING + '!! DEMO MODE ACTIVE !!' + bcolors.ENDC if DemoMode == 1 else ''
    six.print_('   Buy : {:<10}{:^58}'.format(BuyCoin,  demomodewarning))
    six.print_(' ---------------\n')
    rowfmt_s = '{:<5} {:>20} {:>20} {:>20}'
    six.print_(rowfmt_s.format('Commodity', 'Balance', 'StopBalance', 'SellAmount'))
    six.print_(rowfmt_s.format('-'*5, '-'*16, '-'*16, '-'*16))
    rowfmt_d = '{:<5} {:>20.8f} {:>20.8f} {:>20.8f}'
    for com, bal, stopbal, sellamt in BalanceList:
        six.print_(rowfmt_d.format(com, bal, stopbal, sellamt))
    six.print_('')

    if not any([e[3] for e in BalanceList]):
        six.print_('\n No Coins to sell ... ')

    else:
        ### Load Market Lists
        Data = Wrapper('Cryptopia', 'GetTradePairs', [])

        six.print_('\n Searching for possible Trade Routes ...')

        MarketList = []
        for Market in Data['Data']:
            if Market['Status'] == 'OK':
                tradepair = (Market['Symbol'], Market['BaseSymbol'])
                idx = Market['Id']
                fee = Market['TradeFee']
                mintrade = Market['MinimumBaseTrade']
                MarketList.append([tx[0], tx[1], idx, fee, mintrade])

        ### find Markets to get Coins direct (Trade1)
        ListTrade1 = []
        for SellCoin in ListSell:
            for element in MarketList:
                if (str(SellCoin) == str(element[0])):
                    ListTrade1.append([element, 'Sell', str(SellCoin)])

                if (str(SellCoin) == str(element[1])):
                    ListTrade1.append([element, 'Buy', str(SellCoin)])

        ##shortest Route, single Trade
        ListSingleTrade = []
        for element in ListTrade1:
            if (str(BuyCoin) == str(element[0][0]) or str(BuyCoin) == str(element[0][1])):
                ListSingleTrade.append([element])

        a = len(ListSingleTrade)
        six.print_('   ... found', a, 'direct Trade(s)')

        ### find Markets to get coins on last trade (Trade2 and Trade3)
        ListLastTrade = []
        for element in MarketList:
            if str(BuyCoin) == str(element[0]):
                ListLastTrade.append([element, 'Buy'])
            if str(BuyCoin) == str(element[1]):
                ListLastTrade.append([element, 'Sell'])

        ## Route on two Trades
        ListTwoTrades = []
        for LastTrade in ListLastTrade:
            for FirstTrade in ListTrade1:
                if (str(FirstTrade[1]) == 'Buy' and str(LastTrade[0][0]) == str(FirstTrade[0][0]) and str(BuyCoin) != str(FirstTrade[0][0])):
                    ListTwoTrades.append([FirstTrade, LastTrade])
                if (str(FirstTrade[1]) == 'Buy' and str(LastTrade[0][1]) == str(FirstTrade[0][0]) and str(BuyCoin) != str(FirstTrade[0][0])):
                    ListTwoTrades.append([FirstTrade, LastTrade])
                if (str(FirstTrade[1]) == 'Sell' and str(LastTrade[0][0]) == str(FirstTrade[0][1]) and str(BuyCoin) != str(FirstTrade[0][1])):
                    ListTwoTrades.append([FirstTrade, LastTrade])
                if (str(FirstTrade[1]) == 'Sell' and str(LastTrade[0][1]) == str(FirstTrade[0][1]) and str(BuyCoin) != str(FirstTrade[0][1])):
                    ListTwoTrades.append([FirstTrade, LastTrade])
        b = len(ListTwoTrades)
        six.print_('   ... found', b, 'Trade Routes across two Markets')

        ## Route on 3 Trades
        List3Trades = []
        def completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade):
            for LastTrade in ListLastTrade:
                if (str(MiddleTradeAction) == 'Buy' and str(LastTrade[0][0]) == str(MiddleTrade[0]) and str(BuyCoin) != str(MiddleTrade[0]) and LastTrade[0][2] != MiddleTrade[2]):
                    List3Trades.append([FirstTrade, [MiddleTrade, MiddleTradeAction], LastTrade])
                if (str(MiddleTradeAction) == 'Buy' and str(LastTrade[0][1]) == str(MiddleTrade[0]) and str(BuyCoin) != str(MiddleTrade[0]) and LastTrade[0][2] != MiddleTrade[2]):
                    List3Trades.append([FirstTrade, [MiddleTrade, MiddleTradeAction], LastTrade])
                if (str(MiddleTradeAction) == 'Sell' and str(LastTrade[0][0]) == str(MiddleTrade[1]) and str(BuyCoin) != str(MiddleTrade[1]) and LastTrade[0][2] != MiddleTrade[2]):
                    List3Trades.append([FirstTrade, [MiddleTrade, MiddleTradeAction], LastTrade])
                if (str(MiddleTradeAction) == 'Sell' and str(LastTrade[0][1]) == str(MiddleTrade[1]) and str(BuyCoin) != str(MiddleTrade[1]) and LastTrade[0][2] != MiddleTrade[2]):
                    List3Trades.append([FirstTrade, [MiddleTrade, MiddleTradeAction], LastTrade])

        for MiddleTrade in MarketList:
            for FirstTrade in ListTrade1:
                if (str(FirstTrade[1]) == 'Buy' and str(MiddleTrade[0]) == str(FirstTrade[0][0]) and str(BuyCoin) != str(MiddleTrade[1]) and FirstTrade[0][2] != MiddleTrade[2]): #and str(BuyCoin) != str(FirstTrade[0][0])
                    MiddleTradeAction = 'Sell'
                    completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade)
                if (str(FirstTrade[1]) == 'Buy' and str(MiddleTrade[1]) == str(FirstTrade[0][0]) and str(BuyCoin) != str(MiddleTrade[0]) and FirstTrade[0][2] != MiddleTrade[2]): #and str(BuyCoin) != str(FirstTrade[0][0])
                    MiddleTradeAction = 'Buy'
                    completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade)
                if (str(FirstTrade[1]) == 'Sell' and str(MiddleTrade[0]) == str(FirstTrade[0][1]) and str(BuyCoin) != str(MiddleTrade[1]) and FirstTrade[0][2] != MiddleTrade[2]): #and str(BuyCoin) != str(FirstTrade[0][1])
                    MiddleTradeAction = 'Sell'
                    completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade)
                if (str(FirstTrade[1]) == 'Sell' and str(MiddleTrade[1]) == str(FirstTrade[0][1]) and str(BuyCoin) != str(MiddleTrade[0]) and FirstTrade[0][2] != MiddleTrade[2]): #and str(BuyCoin) != str(FirstTrade[0][1])
                    MiddleTradeAction = 'Buy'
                    completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade)
        c = len(List3Trades)
        six.print_('   ... found', c, 'Trade Routes across three Markets')

        ### get Markets Data and Routes
        def searchMax(Dict):
            return max(six.iterkeys(Dict), key=(lambda key: Dict[key]))

        def RouteCheck(Route, Data, Input):
            for element in Route:
                Price = Data['MarketSummaries'][str(element[0][2])]
                if ( str(element[1]) == 'Buy' and float(Price[1]) > 0.0 and float(Input) > 0.0 ):
                    Output = ( float(Input) * 100.0 / ( 100.0 + float(element[0][3]) ) ) / float(Price[1])
                    if ( float(Input) < float(element[0][4]) + 0.00000001 ):
                        Output = 0
                elif ( str(element[1]) == 'Sell' and float(Price[2]) > 0.0 and float(Input) > 0.0 ):
                    Output = float(Input) * float(Price[2]) - float(Input) * float(Price[2]) * ( float(element[0][3]) / 100.0 )
                    if ( float(Output) < float(element[0][4]) + 0.00000001 ):
                        Output = 0
                else:
                    Output = 0
                Input = Output
            return Output

        def OrderDepthBid(Orderbook, Amount):
            if (Amount <= Orderbook[0][1]): # no depth calc
                Price = Orderbook[0][0]
                return [Price, Amount, Price]
            else: # depth calc
                TeilAmount = 0
                TeilTotal = 0
                OrderDepth = 1
                for element in Orderbook:
                    if (OrderDepth == len(Orderbook) and Amount >= TeilAmount + element[1]):
                        Price = (TeilTotal + element[2]) / (TeilAmount + element[1])
                        return [Price, TeilAmount + element[1], element[0]]
                    else:
                        if (TeilAmount + element[1] < Amount):
                            TeilAmount = TeilAmount + element[1]
                            TeilTotal = TeilTotal + element[2]
                            OrderDepth = OrderDepth + 1
                        else:
                            RestAmount = Amount - TeilAmount
                            RestTotal = RestAmount * element[0]
                            Total = TeilTotal + RestTotal
                            Price = Total / Amount
                            return [Price, Amount, element[0]]

        def OrderDepthAsk(Orderbook, Total):
            if (Total <= Orderbook[0][2]): # no depth calc
                Price = Orderbook[0][0]
                return [Price, Total, Price]
            else: # depth calc
                TeilAmount = 0
                TeilTotal = 0
                OrderDepth = 1
                for element in Orderbook:
                    if (OrderDepth == len(Orderbook) and Total >= TeilTotal + element[2]):
                        Price = (TeilTotal + element[2]) / (TeilAmount + element[1])
                        return [Price, TeilTotal + element[2], element[0]]
                    else:
                        if (TeilTotal + element[2] < Total):
                            TeilAmount = TeilAmount + element[1]
                            TeilTotal = TeilTotal + element[2]
                            OrderDepth = OrderDepth + 1
                        else:
                            RestTotal = Total - TeilTotal
                            RestAmount = RestTotal / element[0]
                            Amount = TeilAmount + RestAmount
                            Price = Total / Amount
                            return [Price, Total, element[0]]

        def RouteCalc(Route, Data, Input):
            OrderData = []
            for element in Route:
                if ( str(element[1]) == 'Buy' and float(Input) > 0.0 ):
                    time.sleep(1)
                    InputNet = Input
                    Input = float(Input) * 100.0 / ( 100.0 + float(element[0][3]) )
                    OrderbookData = OrderDepthAsk(Data[element[0][2]]['SellOrderbook'], Input)
                    AskPrice = OrderbookData[0]
                    OrderPrice = OrderbookData[2]
                    Output = float(OrderbookData[1]) / float(OrderbookData[0])
                    if ( float(InputNet) < float(element[0][4]) + 0.00000001 ):
                        Output = 0
                    Orders = [[OrderPrice, Output, 0]]
                    if (float(AskPrice) != float(OrderPrice)):
                        TotalFake = float(Output) * float(OrderbookData[2])
                        for Symbol, Balance in six.iteritems(Balances):
                            if ( str(Symbol) == str(element[0][1]) and float(TotalFake) > float(Balance[0])):
                                Amount = float(Output)
                                TotalLeft = float(Input)
                                Orders = []
                                Amounts = []
                                Totals = []
                                for index, Position in enumerate(Data[element[0][2]]['SellOrderbook']):
                                    Amounts.append(float(Position[1]))
                                    Totals.append(float(Position[2]))
                                    TotalFake = float(sum(Amounts)) * float(Position[0])
                                    if ( float(TotalFake) > float(TotalLeft) and float(Position[0]) <= float(OrderPrice)):
                                        Jumper = 1
                                        if ( (float(sum(Amounts)) - float(Position[1])) * float(Data[element[0][2]]['SellOrderbook'][index-1][0]) >= float(element[0][4]) + 0.00000001 or index == 0 ):
                                            Price = float(Data[element[0][2]]['SellOrderbook'][index-1][0])
                                            Output = float(sum(Amounts)) - float(Position[1])
                                            TotalLeft = float(TotalLeft) - float(sum(Totals)) + float(Position[2])
                                            Orders.append([Price, Output, 1])
                                            Amounts = [float(Position[1])]
                                            Totals = [float(Position[2])]
                                            Jumper = 0
                                        if ( (float(sum(Amounts)) - float(Position[1])) * float(Data[element[0][2]]['SellOrderbook'][index-1][0]) < float(element[0][4]) + 0.00000001 and index != 0 and Jumper == 1):
                                            Price = float(Position[0])
                                            TotalP1 = float(sum(Totals)) - float(Position[2])
                                            AmountP1 = float(sum(Amounts)) - float(Position[1])
                                            TotalP2 = float(element[0][4]) + 0.00000001 - float(TotalP1)
                                            AmountP2 = float(TotalP2) / float(Price)
                                            if ((float(AmountP1) + float(AmountP1)) * float(Price) < float(TotalLeft)):
                                                if ((float(AmountP1) + float(AmountP1)) * float(Price) < 2 * float(element[0][4]) + 0.00000001):
                                                    Output = float(AmountP1) + float(AmountP2)
                                                    Orders.append([Price, Output, '11a'])
                                                    TotalLeft = float(TotalLeft) - float(TotalP2)
                                                    Amounts = [float(Position[1]) - float(AmountP2)]
                                                    Totals = [float(Position[2]) - float(TotalP2)]
                                                else:
                                                    Output = float(TotalLeft) / float(Price)
                                                    Orders.append([Price, Output, '11b'])
                                                    AmountP3 = float(Output) - (float(AmountP2) + float(AmountP1))
                                                    Amounts = [float(Position[1]) - float(AmountP3)]
                                                    TotalP3 = float(AmountP3) / float(Position[0])
                                                    Totals = [float(Position[2]) - float(TotalP3)]

                                    if ( float(Position[0]) == float(OrderPrice) and float(TotalLeft) >= float(element[0][4]) + 0.00000001):
                                        Output = 0
                                        for Order in Orders:
                                            Output = float(Output) + float(Order[1])
                                        Output = float(Amount) - float(Output)
                                        Price = float(Position[0])
                                        Orders.append([Price, Output, 2])
                                        TotalLeft = 0
                                        Totals = []
                                        Amounts = []
                    Output = 0
                    for Order in Orders:
                        Output = float(Output) + float(Order[1])
                    if (round(float(Output),8) * float(AskPrice) + float(Output) * float(AskPrice) * ( float(element[0][3]) / 100.0 )  > float(InputNet)):
                        Output = 0
                        count = 1
                        for Order in Orders:
                            if (count == len(Orders)):
                                Output = float(Output) + float(Order[1])
                                TotalDif = round(float(Output),8) * float(AskPrice) + float(Output) * float(AskPrice) * ( float(element[0][3]) / 100.0 )  - float(InputNet)
                                OrderCorr = round((float(TotalDif) * 100.0 / ( 100.0 + float(element[0][3]) )) / float(AskPrice) + 0.000000005, 8)
                                Output = round(float(Output) - float(OrderCorr),8)
                                OrderData.append([element[0][2], element[1], Order[0], float(Order[1]) - float(OrderCorr), Order[2]])
                            else:
                                Output = float(Output) + float(Order[1])
                                OrderData.append([element[0][2], element[1], Order[0], Order[1], Order[2]])
                            count = count + 1
                    else:
                        Output = 0
                        for Order in Orders:
                            Output = float(Output) + float(Order[1])
                            OrderData.append([element[0][2], element[1], Order[0], Order[1], Order[2]])

                elif ( str(element[1]) == 'Sell' and float(Input) > 0.0 ):
                        OrderbookData = OrderDepthBid(Data[element[0][2]]['BuyOrderbook'], Input)
                        BidPrice = OrderbookData[0]
                        OrderPrice = OrderbookData[2]
                        Input = OrderbookData[1]
                        Output = float(Input) * float(OrderbookData[0]) - float(Input) * float(OrderbookData[0]) * ( float(element[0][3]) / 100.0 )
                        if ( float(Output) < float(element[0][4]) + 0.00000001 ):
                            Output = 0
                        OrderData.append([element[0][2], element[1], OrderPrice, Input])

                else:
                    Output = 0
                    OrderData.append([element[0][2], element[1], 0.0, 0.0])

                Input = Output
            return [Output, OrderData]

        for SellCoin in ListSell:
            AmountToSell = 0.0
            for element in BalanceList:
                if (str(element[0]) == str(SellCoin)):
                    AmountToSell = element[3]
            assert AmountToSell != 0, 'Internal error. There was a balance on %s last time we checked,\n' \
                    + 'but now there somehow isn\'t.'
            ###check routes
            NumRoutes = {}
            NumProfit = {}
            count = 0
            six.print_('')
            six.print_(' ---------------------------------------------------------------------------')
            six.print_('')
            six.print_(' calculating Routes for', SellCoin, '->', BuyCoin)
            Data = Wrapper('Cryptopia', 'GetMarketSummaries', [])
            for Route in List3Trades:
                if (str(Route[0][2]) == str(SellCoin)):
                    NumRoutes.update({count:Route})
                    NumProfit.update({count:RouteCheck(Route, Data, AmountToSell)})
                    count = count + 1

            for Route in ListTwoTrades:
                if (str(Route[0][2]) == str(SellCoin)):
                    NumRoutes.update({count:Route})
                    NumProfit.update({count:RouteCheck(Route, Data, AmountToSell)})
                    count = count + 1

            for Route in ListSingleTrade:
                if (str(Route[0][2]) == str(SellCoin)):
                    NumRoutes.update({count:Route})
                    NumProfit.update({count:RouteCheck(Route, Data, AmountToSell)})
                    count = count + 1

            Balances = Wrapper('Cryptopia', 'GetBalances', '')['Balances']
            SelectionOfNumProfit = {0:0}
            Orderbooks = {}
            TradeDetails = {}
            Repeat = 1
            while 1 == Repeat:

                MaxProfit = searchMax(NumProfit)
                MaxProfitSelection = searchMax(SelectionOfNumProfit)
                if (float(NumProfit[MaxProfit]) < float(SelectionOfNumProfit[MaxProfitSelection]) or float(MaxProfit) == 0.0 ):
                    Repeat = 0
                else:

                    for element in NumRoutes[MaxProfit]:
                        if element[0][2] not in Orderbooks:
                            Data = Wrapper('Cryptopia', 'GetOrderbook', [element[0][2], 75])
                            Orderbooks.update({element[0][2]:Data})

                    ### calc Details on max Route
                    New = RouteCalc(NumRoutes[MaxProfit], Orderbooks, AmountToSell)
                    SelectionOfNumProfit.update({MaxProfit:New[0]})
                    TradeDetails.update({MaxProfit:New[1]})
                    NumProfit.update({MaxProfit:0})


            RouteNr = searchMax(SelectionOfNumProfit)
            if ( int(RouteNr) >> 0 and float(SelectionOfNumProfit[RouteNr]) > 0.00000001):
                MaxRouteDetails = NumRoutes[RouteNr]
                routestr = '  ->  '.join(['%s/%s (%s)'%(e[0][0], e[0][1], e[1]) for e in MaxRouteDetails])
                six.print_('\n Trade Route: %s'%routestr)

                six.print_('{:<15}'.format(' InputAmount :'), '{:>20.8f}{:<1}{:<7}'.format(AmountToSell, ' ', SellCoin))
                six.print_('{:<15}'.format(' OutputAmount:'), '{:>20.8f}{:<1}{:<7}'.format(SelectionOfNumProfit[RouteNr], ' ', BuyCoin))
                six.print_('')
                MaxRouteTrades = TradeDetails[RouteNr]
                six.print_(' Submit Trade(s):')
                if (DemoMode == 1):
                    for element in MaxRouteTrades:
                        six.print_('{:<4}'.format(element[1]), 'MarketId:', element[0], '\t', 'Price:', '{:>.8f}'.format(float(element[2])), '\t', 'Amount:', '{:>.8f}'.format(float(element[3])))
                    six.print_('   !! DEMO MODE ACTIVE !!   ')
                elif (DemoMode != 1):
                    for element in MaxRouteTrades:
                        Wrapper('Cryptopia', 'SubmitOrder', [element[0], element[1], element[2], element[3]])
            else:
                six.print_('')
                six.print_('{:<15}'.format(' InputAmount :'), '{:>20.8f}{:<1}{:<7}'.format(AmountToSell, ' ', SellCoin))
                six.print_('{:<15}'.format(' OutputAmount:'), 'Does not hit Trade Minimun, or is less than 1 satoshi.')

    six.print_('')
    six.print_(' ---------------------------------------------------------------------------')
    #submit tip (optional)
    if (TipActive == 1):
        six.print_('')
        six.print_(' Submit Tip :')
        if ( str(TipCoin) in dict(TipMinAmount) ):
            minTip = TipMinAmount[TipCoin]
            if ( float(minTip) * float(TipUsers) > float(TipAmount) * float(TipUsers) ):
                six.print_('')
                six.print_(' Tip not submitted. Amount per user to small, please edit timemachine.ini .')
                six.print_(' You\'ve set', float(TipAmount), str(TipCoin), 'per User .')
                six.print_(' Minimum is', minTip, str(TipCoin), '.')
            else:
                if ( int(TipUsers) >= 2 and int(TipUsers) <= 100):
                    six.print_('')
                    six.print_('', float(TipAmount) * float(TipUsers), str(TipCoin), 'divided equally amongst the last', TipUsers, 'active users.')
                    six.print_('')
                    if (DemoMode == 1):
                        six.print_('   !! DEMO MODE ACTIVE !!   ')
                    elif (DemoMode != 1):
                        Wrapper('Cryptopia', 'SubmitTip', [str(TipCoin), int(TipUsers), float(TipAmount) * float(TipUsers)])
                else:
                    six.print_('')
                    six.print_(' Tip not submitted, please edit timemachine.ini .')
                    six.print_(' You try to Tip', TipUsers, 'Users. ')
                    six.print_(' Do not Tip less than 2 or more than 100 Users !')
        else:
            six.print_('')
            six.print_(' Minimum Tip not provided in timemachine.ini !')
            six.print_(' Please update section: Missing_API_Data, MinimumTipAmounts')
        six.print_('')
        six.print_(' ---------------------------------------------------------------------------')


    def Pause(pause_seconds):
        ERASE_LINE = '\x1b[2K'
        while pause_seconds > 0:
            m, s = divmod(pause_seconds, 60)
            h, m = divmod(m, 60)
            sys.stdout.write(ERASE_LINE)
            sys.stdout.write('\rSleeping %2d:%02d:%02d'%(h,m,s))
            sys.stdout.flush()
            time.sleep(1)
            pause_seconds -= 1
        six.print_('')

    six.print_('')
    Pause(SleepInterval)
    six.print_('')
    six.print_(' ---------------------------------------------------------------------------')
