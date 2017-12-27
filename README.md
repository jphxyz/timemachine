# Cryptopia TIMEMACHINE
Auto-trader for Cryptopia Currency exchange

From 'CoinUser' on cryptopia forum. This script checks your account for some currencies
and automatically finds and executed the most profitable trading route (up to 3 markets)
to one desired currency.

This is useful for altcoin miners who only want to hold certain currencies.

Can be set up on Debian/Ubuntu as follows:
```
sudo apt-get install python-configparser python-urllib3 python-requests
wget https://github.com/jphxyz/timemachine/archive/master.zip
unzip master.zip
cd timemachine-master

  [ EDIT timemachine.ini and Module/Interface.ini per instructions
  in first post of https://www.cryptopia.co.nz/Forum/Thread/544 ]

python ./timemachine.py
```

Documentation, and code contributions welcome. Much thanks to CoinUser for the original work!
