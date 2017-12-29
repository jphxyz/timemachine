#!/usr/bin/env python

'''
Copyright (c) 2016, jphxyz
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
DISCLAIMED. IN NO EVENT SHALL jphxyz BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

'''
Inspired by (and partly derived from) CoinUser's script, which can be found
in this forum post: https://www.cryptopia.co.nz/Forum/Thread/544
'''

import json, os, sys, time
from Module import six
from Module.CryptopiaWrapper import CryptopiaWrapper
import Module.Markets as markets
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def pause(pause_seconds):
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

### read and validate config file
cfgloc = os.path.join(sys.path[0], 'config', 'timemachine.ini')
assert os.path.isfile(cfgloc), '' \
        + ' !!! ERROR !!!' \
        + ' config/timemachine.ini not found.'

config = six.moves.configparser.ConfigParser()
config.read(cfgloc)
ConfDict        = config.__dict__['_sections']

DemoMode        = (ConfDict['Main_Settings']['demo_mode'].lower() in ('y', 'yes', '1', 'true'))
GaudyStartup    = (ConfDict['Main_Settings']['gaudy_startup_sequence'].lower() in ('y', 'yes', '1', 'true'))
DonatePercent   = float(ConfDict['Main_Settings']['donate_percent'])/100.0

buyCoin         = ConfDict['Trade_Settings']['coin_to_buy']
SellFraction    = float(ConfDict['Trade_Settings']['sell_percent_of_available_balance'])/100.0
MaxTrades       = int(ConfDict['Trade_Settings']['max_trades'])
RateOvershoot   = float(ConfDict['Trade_Settings']['rate_overshoot'])/100.0

StopBalances    = {k.upper(): float(v) for k, v in six.iteritems(ConfDict['Keep_Balance']) if k not in ('symbol', '__name__')}

PublicKey       = ConfDict['Cryptopia']['public_key']
PrivateKey      = ConfDict['Cryptopia']['private_key']

api = CryptopiaWrapper(PublicKey, PrivateKey)

# Dramatic startup messages
zzz = 0.07 if GaudyStartup else 0.0
six.print_(' ---------------------------------------------------------------------------')
six.print_('')
sys.stdout.write('{:<26}'.format(''))
for letter in 'TIMEMACHINE':
    sys.stdout.write(' ' + letter)
    time.sleep(zzz)
    sys.stdout.flush()
six.print_('\n')
if DemoMode:
    six.print_(bcolors.WARNING+'{:^76}\n'.format('!!! DEMO MODE !!!')+bcolors.ENDC)
time.sleep(zzz)
six.print_('{:^76}'.format('advanced auto-sell program'))
time.sleep(zzz)
six.print_('{:^76}'.format('for CRYPTOPIA'))
time.sleep(zzz * 7)
six.print_('{:>76}'.format('by jphxyz and CoinUser'))
six.print_(' ---------------------------------------------------------------------------')

six.print_('\n Fetching Account Balances...', end=' ', flush=True)
# Not documented, but querying GetBalance with no
# currency argument apparently returns all currencies.
balances = api.getBalance('')
six.print_('OK.')

available = {b['Symbol']:b['Available'] for b in balances if (b['Status'] == 'OK') and (not b['Symbol'] == buyCoin) and (b['Available'] > 0)}

if len(available.keys()) == 0:
    six.print_('\n No coins to sell. Exiting.')
    sys.exit(0)

six.print_('\n ---------------')
six.print_('   Buy : ', buyCoin)
six.print_(' ---------------\n')
rowfmt_s = '{:<10} {:>20} {:>20} {:>20}'
six.print_(rowfmt_s.format('Commodity', 'Balance', 'StopBalance', 'SellAmount'))
six.print_(rowfmt_s.format('-'*5, '-'*16, '-'*16, '-'*16))
rowfmt_d = '{:<10} {:>20.8f} {:>20.8f} {:>20.8f}'
for sym, bal in six.iteritems(available):
    stopbal = StopBalances[sym] if sym in StopBalances else 0.0
    six.print_(rowfmt_d.format(sym, bal, stopbal, bal - stopbal))
six.print_('')

six.print_('\n Initializing Market Network...', end=' ', flush=True)
net = markets.Network(api)
six.print_('OK.')

totalconverted = 0.0

for sellcoin in available:
    if available[sellcoin] == 0:
        continue

    tosell = available[sellcoin] * SellFraction
    if sellcoin in StopBalances:
        tosell -= StopBalance[sellcoin]

    # Establish route
    expected_value, route = net.getBestRoute(sellcoin, buyCoin, tosell, 3, RateOvershoot)
    rtstring = ' -> '.join(['[%s (%g)]'%(coin, qty) for coin, qty in route])
    six.print_('\n\n Established trade route: %s'%rtstring)

    output_val = tosell

    # Now execute trades
    for i, coin in enumerate(route[:-1]):
        assert (coin != route[i+1]), 'Route is wonky. (%s)'(' -> '.join(route))
        fromcoin = coin[0]
        tocoin = route[i+1][0]
        pair = net.getTradePair(fromcoin, tocoin)
        sym = pair.Symbol
        base = pair.BaseSymbol
        assert fromcoin in (sym, base) and tocoin in (sym, base), 'Wrong trade pair fetched.'

        while (not DemoMode):
            bals = api.getBalance(fromcoin)
            if bals['Available'] < output_val:
                if bals['HeldForTrades'] > 0:
                    six.print_(' Waiting on open orders ...')
                    pause(15)
                else:
                    output_val = bals['Available']
                    six.print_(' Insufficient available funds for intended transaction.\n' \
                             + ' Reducting sell amount of %s to %g.'%(fromcoin, output_val))
                    break
            else:
                break

        market = net.getMarket(pair.Id)

        # Echanges are labeled Symbol/BaseSymbol (e.g. BTC/USDT)
        # If 'fromcoin' is Symbol, then I want to place a sell order
        # to get the next currency in the route.
        # If 'fromcoin' is BaseSymbol, then I want to place a buy order.
        #
        # The Amount field should always be specified in units of the
        # trade symbol, not the base currency.
        input_val = output_val
        if fromcoin == sym:
            tradeType = 'Sell'
            rate = market['BidPrice'] * (1.0 - RateOvershoot)
            amount = input_val * (1.0 - pair.TradeFee/100.0)
            output_val = amount*rate
        else:
            tradeType = 'Buy'
            rate = market['AskPrice'] * (1.0 + RateOvershoot)
            amount = input_val/rate * (1.0 - pair.TradeFee/100.0)
            output_val = amount

        if DemoMode:
            six.print_(bcolors.WARNING + 'DEMO MODE:' + bcolors.ENDC, end=' ')

        six.print_(' Submitting %4s order: %g %s -> %g %s ...'%(tradeType, input_val, fromcoin, output_val, tocoin), end=' ', flush=True)

        if DemoMode:
            six.print_('')
            time.sleep(1)
        else:
            api.submitTrade(pair.Id, tradeType, rate, amount)
            six.print_('OK.\n\n')

    totalconverted += output_val

if not DemoMode:
    six.print_(' Donating %g%% to developers.'%(DonatePercent))
    amtToDonate = totalconverted * DonatePercent
    if amtToDonate > 0:
        api.submitTransfer(buyCoin, 'jphxyz', amtToDonate)
        six.print_(' Thank you!!')
