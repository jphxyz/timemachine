#!/usr/bin/env python

import sys
import ConfigParser
import json
import time
from Module.Interface import Api

location = str(sys.path[0]) + str("/")

zzz = 0.07
def TM():
    Word = ["T", "I", "M", "E", "M", "A", "C", "H", "I", "N", "E" ]
    for element in Word:
        print element,
        time.sleep(0.07)
    return ""
print " ---------------------------------------------------------------------------"
print ""
print '{:<26}'.format(""), TM()
#print '{:^76}'.format(str("T I M E M A C H I N E"))
print ""
time.sleep(zzz)
print '{:^76}'.format(str("advanced auto-sell program"))
time.sleep(zzz)
print '{:^76}'.format(str("for CRYPTOPIA"))
time.sleep(zzz * 7)
print '{:>76}'.format(str("by CoinUser"))
print " ---------------------------------------------------------------------------"

Loop = 1
while 1 == Loop:
    ###read conf data
    config = ConfigParser.ConfigParser()
    config.read(location + "timemachine.ini")
    ConfDict = {}
    for section in config.sections():
        ConfDict[section] = {}
        for option in config.options(section):
            ConfDict[section][option] = config.get(section, option)
    if (len(ConfDict) == 0):
        print " "
        print " !!! ERROR !!!"
        print "timemachine.ini not found !"
        exit()
    BuyCoin = str(ConfDict['Main_Settings']['coin_to_buy'])
    TimeInterval = int(ConfDict['Main_Settings']['sleep_minutes']) * 60
    DemoMode = int(ConfDict['Demo_Mode']['active'])
    SellBalance = float(ConfDict['Main_Settings']['sell_percent_of_available_balance']) * float(0.01)
    Fee = float(ConfDict['Missing_API_Data']['tradefee'])
    BaseTradeMin = json.loads(str(ConfDict['Missing_API_Data']['basemintrade']))
    SuspendedMarkets = json.loads(str(ConfDict['Missing_API_Data']['suspendedmarkets']))
    TipActive = int(ConfDict['Submit_Tip']['active'])
    TipCoin = str(ConfDict['Submit_Tip']['coin'])
    TipAmount = int(ConfDict['Submit_Tip']['tip_amount_per_user'])
    TipUsers = int(ConfDict['Submit_Tip']['to_last_active_users'])
    TipMinAmount = json.loads(str(ConfDict['Missing_API_Data']['minimumtipamounts']))
    ListSellCoins = []
    for k, v in ConfDict['Coins_To_SELL_and_Stop_at_Balance'].iteritems():
        if (k <> str("symbol")):
            SYMBOL = k.upper()
            ListSellCoins.append([str(SYMBOL), float(v)])

    for element in ListSellCoins:
        if str(BuyCoin) == element[0]:
            print " "
            print " !!! ERROR !!!"
            print " The Coin you want purchase is in the List of Coins to sell !"
            print " Please edit timemachine.ini !"
            print " And erase", element[0], "form the list. Or choose a different Coin to buy ."
            exit()

    ### get api data
    def Wrapper(Exchange, Action, ActionData):
        GetCoins = Api(Action, ActionData, "F")
        x = getattr(GetCoins, Exchange)
        Data = x()
        return Data

    ### get Balance and calculate trade Amounts
    def Input(Balance, StopBalance):
        AvailableReal = float(Balance[0]) - float(StopBalance)
        SellAmount = float(Balance[0]) * float(SellBalance)
        if (float(Balance[0]) < float(StopBalance)):
            return float(0.0)
        elif (float(SellAmount) <= float(AvailableReal)):
            return float(SellAmount)
        elif (float(SellAmount) > float(AvailableReal)):
            return float(AvailableReal)

    def Bal():
        Data = Wrapper("Cryptopia", "GetBalances", "")
        Balances = Data['Balances']
        return Balances
    Balances = Bal()
    BalanceList = []
    ListSell = []
    for element in ListSellCoins:
        InputAmount = Input(Balances[element[0]], element[1])
        BalanceList.append([element[0], Balances[element[0]], element[1], InputAmount] )
        if (float(InputAmount) > float(0.0)):
            ListSell.append(element[0])
    if (DemoMode == 1):
        TM = 2 * "   !! DEMO MODE ACTIVE !!   "
    elif (DemoMode <> 1):
        TM = " "
    print ""
    print " ---------------"
    print '{:<8}{:<10}{:^58}'.format(str("  Buy :"), BuyCoin, TM)         
    print " ---------------"
    print ""
    print " Sell\t",  '{:>20}'.format(str("Available")), "\t", '{:>20}'.format(str("StopBalance")),"\t" , '{:>20}'.format(str("InputAmount"))
    print " ------\t",  '{:>20}'.format(str("----------------")), "\t", '{:>20}'.format(str("----------------")),"\t" , '{:>20}'.format(str("----------------"))
    SumInputs = 0.0
    for element in BalanceList:
        print "", element[0],"\t", '{:>20.8f}'.format(float(element[1][0])),"\t", '{:>20.8f}'.format(float(element[2])),"\t", '{:>20.8f}'.format(float(element[3]))
        SumInputs = float(SumInputs) + float(element[3])
    print " "

    if (len(BalanceList) >> 0 and float(SumInputs) > float(0.0)):

        ### Load Market Lists
        Data = Wrapper("Cryptopia", "GetTradePairs", [])

        print " "
        print " searching for possible Trade Routes ... "

        MarketList = []
        for Market in Data['Data']:
            try:
                if Market['Symbol'] not in list(SuspendedMarkets) and  Market['BaseSymbol'] not in list(SuspendedMarkets):
                    TotalMin = BaseTradeMin[Market['BaseSymbol']]
                    MarketList.append([Market['Symbol'], Market['BaseSymbol'], Market['Id'], Fee, TotalMin])
            except KeyError, e:
                print " "
                print " !!! ERROR !!!"
                print " Missing Minimum Trade Amount for", e, "!"
                print " Please update timemachine.ini !"
                print " Add", e, "to BaseMinTrade in section [Missing_API_Data] !"
                exit()
                
        ### find Markets to get Coins direct (Trade1)
        ListTrade1 = []
        for SellCoin in ListSell:
            for element in MarketList:
                if (str(SellCoin) == str(element[0])):
                    ListTrade1.append([element, str("Sell"), str(SellCoin)])

                if (str(SellCoin) == str(element[1])):
                    ListTrade1.append([element, str("Buy"), str(SellCoin)])

        ##shortest Route, single Trade
        ListSingleTrade = []
        for element in ListTrade1:
            if (str(BuyCoin) == str(element[0][0]) or str(BuyCoin) == str(element[0][1])):
                ListSingleTrade.append([element])

        a = len(ListSingleTrade)
        print "   ... found", a, "direct Trade(s)"

        ### find Markets to get coins on last trade (Trade2 and Trade3)
        ListLastTrade = []
        for element in MarketList:
            if str(BuyCoin) == str(element[0]):
                ListLastTrade.append([element, str("Buy")])
            if str(BuyCoin) == str(element[1]):
                ListLastTrade.append([element, str("Sell")])
            
        ## Route on two Trades
        ListTwoTrades = []
        for LastTrade in ListLastTrade:
            for FirstTrade in ListTrade1:    
                if (str(FirstTrade[1]) == str("Buy") and str(LastTrade[0][0]) == str(FirstTrade[0][0]) and str(BuyCoin) <> str(FirstTrade[0][0])):
                    ListTwoTrades.append([FirstTrade, LastTrade])
                if (str(FirstTrade[1]) == str("Buy") and str(LastTrade[0][1]) == str(FirstTrade[0][0]) and str(BuyCoin) <> str(FirstTrade[0][0])):
                    ListTwoTrades.append([FirstTrade, LastTrade])
                if (str(FirstTrade[1]) == str("Sell") and str(LastTrade[0][0]) == str(FirstTrade[0][1]) and str(BuyCoin) <> str(FirstTrade[0][1])):
                    ListTwoTrades.append([FirstTrade, LastTrade])
                if (str(FirstTrade[1]) == str("Sell") and str(LastTrade[0][1]) == str(FirstTrade[0][1]) and str(BuyCoin) <> str(FirstTrade[0][1])):
                    ListTwoTrades.append([FirstTrade, LastTrade])
        b = len(ListTwoTrades)
        print "   ... found", b, "Trade Routes across two Markets"

        ## Route on 3 Trades
        List3Trades = []
        def completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade):
            for LastTrade in ListLastTrade:    
                if (str(MiddleTradeAction) == str("Buy") and str(LastTrade[0][0]) == str(MiddleTrade[0]) and str(BuyCoin) <> str(MiddleTrade[0]) and LastTrade[0][2] <> MiddleTrade[2]):
                    List3Trades.append([FirstTrade, [MiddleTrade, MiddleTradeAction], LastTrade])
                if (str(MiddleTradeAction) == str("Buy") and str(LastTrade[0][1]) == str(MiddleTrade[0]) and str(BuyCoin) <> str(MiddleTrade[0]) and LastTrade[0][2] <> MiddleTrade[2]):
                    List3Trades.append([FirstTrade, [MiddleTrade, MiddleTradeAction], LastTrade])
                if (str(MiddleTradeAction) == str("Sell") and str(LastTrade[0][0]) == str(MiddleTrade[1]) and str(BuyCoin) <> str(MiddleTrade[1]) and LastTrade[0][2] <> MiddleTrade[2]):
                    List3Trades.append([FirstTrade, [MiddleTrade, MiddleTradeAction], LastTrade])
                if (str(MiddleTradeAction) == str("Sell") and str(LastTrade[0][1]) == str(MiddleTrade[1]) and str(BuyCoin) <> str(MiddleTrade[1]) and LastTrade[0][2] <> MiddleTrade[2]):
                    List3Trades.append([FirstTrade, [MiddleTrade, MiddleTradeAction], LastTrade])
                    
        for MiddleTrade in MarketList:
            for FirstTrade in ListTrade1:    
                if (str(FirstTrade[1]) == str("Buy") and str(MiddleTrade[0]) == str(FirstTrade[0][0]) and str(BuyCoin) <> str(MiddleTrade[1]) and FirstTrade[0][2] <> MiddleTrade[2]): #and str(BuyCoin) <> str(FirstTrade[0][0])
                    MiddleTradeAction = "Sell"
                    completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade)
                if (str(FirstTrade[1]) == str("Buy") and str(MiddleTrade[1]) == str(FirstTrade[0][0]) and str(BuyCoin) <> str(MiddleTrade[0]) and FirstTrade[0][2] <> MiddleTrade[2]): #and str(BuyCoin) <> str(FirstTrade[0][0])
                    MiddleTradeAction = "Buy"
                    completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade)
                if (str(FirstTrade[1]) == str("Sell") and str(MiddleTrade[0]) == str(FirstTrade[0][1]) and str(BuyCoin) <> str(MiddleTrade[1]) and FirstTrade[0][2] <> MiddleTrade[2]): #and str(BuyCoin) <> str(FirstTrade[0][1])
                    MiddleTradeAction = "Sell"
                    completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade)
                if (str(FirstTrade[1]) == str("Sell") and str(MiddleTrade[1]) == str(FirstTrade[0][1]) and str(BuyCoin) <> str(MiddleTrade[0]) and FirstTrade[0][2] <> MiddleTrade[2]): #and str(BuyCoin) <> str(FirstTrade[0][1])
                    MiddleTradeAction = "Buy"
                    completeList3Trades(MiddleTradeAction, MiddleTrade, FirstTrade)
        c = len(List3Trades)
        print "   ... found", c, "Trade Routes across three Markets"

        ### get Markets Data and Routes
        def searchMAX(Dict):
             v=list(Dict.values())
             return list(Dict.keys())[v.index(max(v))]

        def RouteCheck(Route, Data, Input):
            for element in Route:
                Price = Data['MarketSummaries'][str(element[0][2])]
                if ( str(element[1]) == str("Buy") and float(Price[1]) > float(0.0) and float(Input) > float(0.0) ):
                    Output = ( float(Input) * float(100) / ( float(100) + float(element[0][3]) ) ) / float(Price[1])
                    if ( float(Input) < float(element[0][4]) + float(0.00000001) ):
                        Output = 0
                elif ( str(element[1]) == str("Sell") and float(Price[2]) > float(0.0) and float(Input) > float(0.0) ):                                                  
                    Output = float(Input) * float(Price[2]) - float(Input) * float(Price[2]) * ( float(element[0][3]) / float(100) )
                    if ( float(Output) < float(element[0][4]) + float(0.00000001) ):
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
                if ( str(element[1]) == str("Buy") and float(Input) > float(0.0) ):
                    time.sleep(1)
                    InputNet = Input
                    Input = float(Input) * float(100) / ( float(100) + float(element[0][3]) )
                    OrderbookData = OrderDepthAsk(Data[element[0][2]]['SellOrderbook'], Input)
                    AskPrice = OrderbookData[0]
                    OrderPrice = OrderbookData[2]
                    Output = float(OrderbookData[1]) / float(OrderbookData[0])
                    if ( float(InputNet) < float(element[0][4]) + float(0.00000001) ):
                        Output = 0
                    Orders = [[OrderPrice, Output, 0]]
                    if (float(AskPrice) <> float(OrderPrice)):
                        TotalFake = float(Output) * float(OrderbookData[2])
                        for Symbol, Balance in Balances.iteritems():
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
                                        if ( (float(sum(Amounts)) - float(Position[1])) * float(Data[element[0][2]]['SellOrderbook'][index-1][0]) >= float(element[0][4]) + float(0.00000001) or index == 0 ):
                                            Price = float(Data[element[0][2]]['SellOrderbook'][index-1][0])
                                            Output = float(sum(Amounts)) - float(Position[1])
                                            TotalLeft = float(TotalLeft) - float(sum(Totals)) + float(Position[2])
                                            Orders.append([Price, Output, 1])
                                            Amounts = [float(Position[1])]
                                            Totals = [float(Position[2])]
                                            Jumper = 0
                                        if ( (float(sum(Amounts)) - float(Position[1])) * float(Data[element[0][2]]['SellOrderbook'][index-1][0]) < float(element[0][4]) + float(0.00000001) and index <> 0 and Jumper == 1):
                                            Price = float(Position[0])
                                            TotalP1 = float(sum(Totals)) - float(Position[2])
                                            AmountP1 = float(sum(Amounts)) - float(Position[1])
                                            TotalP2 = float(element[0][4]) + float(0.00000001) - float(TotalP1)
                                            AmountP2 = float(TotalP2) / float(Price)
                                            if ((float(AmountP1) + float(AmountP1)) * float(Price) < float(TotalLeft)):
                                                if ((float(AmountP1) + float(AmountP1)) * float(Price) < 2 * float(element[0][4]) + float(0.00000001)):
                                                    Output = float(AmountP1) + float(AmountP2)
                                                    Orders.append([Price, Output, "11a"])
                                                    TotalLeft = float(TotalLeft) - float(TotalP2)
                                                    Amounts = [float(Position[1]) - float(AmountP2)]
                                                    Totals = [float(Position[2]) - float(TotalP2)]
                                                else:
                                                    Output = float(TotalLeft) / float(Price)
                                                    Orders.append([Price, Output, "11b"])
                                                    AmountP3 = float(Output) - (float(AmountP2) + float(AmountP1))
                                                    Amounts = [float(Position[1]) - float(AmountP3)]
                                                    TotalP3 = float(AmountP3) / float(Position[0])
                                                    Totals = [float(Position[2]) - float(TotalP3)]

                                    if ( float(Position[0]) == float(OrderPrice) and float(TotalLeft) >= float(element[0][4]) + float(0.00000001)):
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
                    if (round(float(Output),8) * float(AskPrice) + float(Output) * float(AskPrice) * ( float(element[0][3]) / float(100) )  > float(InputNet)):
                        Output = 0
                        count = 1
                        for Order in Orders:
                            if (count == len(Orders)):
                                Output = float(Output) + float(Order[1])
                                TotalDif = round(float(Output),8) * float(AskPrice) + float(Output) * float(AskPrice) * ( float(element[0][3]) / float(100) )  - float(InputNet)
                                OrderCorr = round((float(TotalDif) * float(100) / ( float(100) + float(element[0][3]) )) / float(AskPrice) + 0.000000005, 8)
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

                elif ( str(element[1]) == str("Sell") and float(Input) > float(0.0) ):
                        OrderbookData = OrderDepthBid(Data[element[0][2]]['BuyOrderbook'], Input)
                        BidPrice = OrderbookData[0]
                        OrderPrice = OrderbookData[2]
                        Input = OrderbookData[1]
                        Output = float(Input) * float(OrderbookData[0]) - float(Input) * float(OrderbookData[0]) * ( float(element[0][3]) / float(100) )
                        if ( float(Output) < float(element[0][4]) + float(0.00000001) ):
                            Output = 0
                        OrderData.append([element[0][2], element[1], OrderPrice, Input])

                else:
                    Output = 0
                    OrderData.append([element[0][2], element[1], 0.0, 0.0])
                
                Input = Output
            return [Output, OrderData]

        for SellCoin in ListSell:
            for element in BalanceList:
                if (str(element[0]) == str(SellCoin)):
                    AmountToSell = element[3]
            ###check routes
            NumRoutes = {}
            NumProfit = {}
            count = 0
            print ""
            print " ---------------------------------------------------------------------------"
            print ""
            print " calculating Routes for", SellCoin, "->", BuyCoin
            Data = Wrapper("Cryptopia", "GetMarketSummaries", [])
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

            Balances = Bal()
            SelectionOfNumProfit = {0:0}
            Orderbooks = {}
            TradeDetails = {}
            Repeat = 1
            while 1 == Repeat:
                
                MaxProfit = searchMAX(NumProfit)
                MaxProfitSelection = searchMAX(SelectionOfNumProfit)
                if (float(NumProfit[MaxProfit]) < float(SelectionOfNumProfit[MaxProfitSelection]) or float(MaxProfit) == float(0.0) ):
                    Repeat = 0
                else:

                    for element in NumRoutes[MaxProfit]:
                        if element[0][2] not in Orderbooks:
                            Data = Wrapper("Cryptopia", "GetOrderbook", [element[0][2], 75])
                            Orderbooks.update({element[0][2]:Data})

                    ### calc Details on max Route
                    New = RouteCalc(NumRoutes[MaxProfit], Orderbooks, AmountToSell)
                    SelectionOfNumProfit.update({MaxProfit:New[0]})
                    TradeDetails.update({MaxProfit:New[1]})
                    NumProfit.update({MaxProfit:0})
                

            RouteNr = searchMAX(SelectionOfNumProfit)
            if ( int(RouteNr) >> int(0) and float(SelectionOfNumProfit[RouteNr]) > float(0.00000001)):
                MaxRouteDetails = NumRoutes[RouteNr]
                print ""
                print " Trade Route : ",
                count = 0
                for element in MaxRouteDetails:
                    count = count + 1
                    if (len(MaxRouteDetails) == count):
                        print str(element[0][0]) + "/" + str(element[0][1]), "(" + str(element[1]) + ")"
                    else:
                        print str(element[0][0]) + "/" + str(element[0][1]), "(" + str(element[1]) + ")",  "  ->  ",
                print '{:<15}'.format(str(" InputAmount :")), '{:>20.8f}{:<1}{:<7}'.format(AmountToSell, " ", SellCoin)
                print '{:<15}'.format(str(" OutputAmount:")), '{:>20.8f}{:<1}{:<7}'.format(SelectionOfNumProfit[RouteNr], " ", BuyCoin)
                print ""
                MaxRouteTrades = TradeDetails[RouteNr]
                print " Submit Trade(s):"
                if (DemoMode == 1):
                    for element in MaxRouteTrades:
                        print '{:<4}'.format(element[1]), "MarketId:", element[0], "\t", "Price:", '{:>.8f}'.format(float(element[2])), "\t", "Amount:", '{:>.8f}'.format(float(element[3]))
                    print "   !! DEMO MODE ACTIVE !!   "
                elif (DemoMode <> 1):
                    for element in MaxRouteTrades:
                        Wrapper("Cryptopia", "SubmitOrder", [element[0], element[1], element[2], element[3]])
            else:
                print ""
                print '{:<15}'.format(str(" InputAmount :")), '{:>20.8f}{:<1}{:<7}'.format(AmountToSell, " ", SellCoin)
                print '{:<15}'.format(str(" OutputAmount:")), "Does not hit Trade Minimun, or is less than 1 satoshi."
                

    else:
        print ""
        print " No Coins to sell ... "
    print ""
    print " ---------------------------------------------------------------------------"
    #submit tip (optional)
    if (TipActive == 1):
        print ""
        print " Submit Tip :"
        if ( str(TipCoin) in dict(TipMinAmount) ):
            minTip = TipMinAmount[TipCoin]
            if ( float(minTip) * float(TipUsers) > float(TipAmount) * float(TipUsers) ):
                print ""
                print " Tip not submitted. Amount per user to small, please edit timemachine.ini ."
                print " You've set", float(TipAmount), str(TipCoin), "per User ."
                print " Minimum is", minTip, str(TipCoin), "."
            else:
                if ( int(TipUsers) >= int(2) and int(TipUsers) <= int(100)):
                    print ""
                    print "", float(TipAmount) * float(TipUsers), str(TipCoin), "divided equally amongst the last", TipUsers, "active users."
                    print ""
                    if (DemoMode == 1):
                        print "   !! DEMO MODE ACTIVE !!   "
                    elif (DemoMode <> 1):
                        Wrapper("Cryptopia", "SubmitTip", [str(TipCoin), int(TipUsers), float(TipAmount) * float(TipUsers)])
                else:
                    print ""
                    print " Tip not submitted, please edit timemachine.ini ."
                    print " You try to Tip", TipUsers, "Users. "
                    print " Do not Tip less than 2 or more than 100 Users !"
        else:
            print ""
            print " Minimum Tip not provided in timemachine.ini !"
            print " Please update section: Missing_API_Data, MinimumTipAmounts"
        print ""
        print " ---------------------------------------------------------------------------"


    def Pause(TimeInterval):
        TD = 0
        for index, point in enumerate(range(TimeInterval / 3)):
            if (point == TD):
                TD = TD + 20
                if ( TimeInterval/60 - point/20 >> 1 and index == 0):
                    print '{:>6}{:<1}{:<7}'.format(TimeInterval/60 - point/20, "", "Minutes"),
                elif ( TimeInterval/60 - point/20 >> 1 ):
                    print "."
                    print '{:>6}{:<1}{:<7}'.format(TimeInterval/60 - point/20, "", "Minutes"),
                elif ( TimeInterval/60 - point/20 == 1 ):
                    print "."
                    print '{:>6}{:<1}{:<7}'.format(TimeInterval/60 - point/20, "", "Minute"),
            else:
                print ".",
            time.sleep(3)
        return "."
    print ""
    print " ... Sleep ..."
    print ""
    print Pause(TimeInterval)
    print ""
    print " ... Start ..."
    print ""
    print " ---------------------------------------------------------------------------"
