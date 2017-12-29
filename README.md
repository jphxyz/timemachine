# Cryptopia TIMEMACHINE
Auto-trader for Cryptopia Currency exchange

Based on code from Cryptopia forum user, 'CoinUser'. This script
automatically finds and executes the most profitable trade route
to consolidate many altcoins into one desired currency.

## Debian/Ubuntu Install
```
sudo apt-get install python-configparser python-requests
wget https://github.com/jphxyz/timemachine/archive/master.zip
unzip master.zip
cd timemachine-master

  [ Create config/timemachine.ini from config/timemachine.ini.sample and edit ]

./timemachine.py
```

## OSX Install
Might work out of the box. If not try
```
python -m pip install requests configparser
```

Download and extract TIMEMACHINE:
https://github.com/jphxyz/timemachine/archive/master.zip

in the command prompt `cd` to the timemachine-master folder
that you just extracted

  [ Create config/timemachine.ini from config/timemachine.ini.sample and edit ]

python ./timemachine.py

## Windows install
Python 2.x or 3.x (https://www.python.org/downloads/)
```
python -m pip install requests configparser
```

Download and extract TIMEMACHINE:
https://github.com/jphxyz/timemachine/archive/master.zip

in the command prompt `cd` to the timemachine-master folder
that you just extracted

  [ Create config/timemachine.ini from config/timemachine.ini.sample and edit ]

python ./timemachine.py
