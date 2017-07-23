# stuff
General things

# optiminer.py

optiminer.py v 0.12 to be used with Python3.5

Optimized CPU-miner for Bismuth cryptocurrency

Change for dev pool mining capability as well as current Python3.5 based local node

Just adjust your config.txt as needed and use with python3.5

Copyright Hclivess, Primedigger, Maccaspacca 2017

# optipool.py

optipool.py v 0.12 to be used with Python3.5

Optimized CPU-miner for Bismuth cryptocurrency dev pool mining only

Copyright Hclivess, Primedigger, Maccaspacca 2017

Dev pool Diff can be passed as an optional argument on startup. If not set it defaults to 50

E.g. 'python3 optipool.py 60' would set the diff to 60
E.g. 'python3 optipool.py' would default to diff 50

No variable diff down in this one

# peer_clean.py

Cleans Bismuth peers.txt of duplicates and nodes on same first network octet thus improving geographic spread of peers

Run from command line in Bismuth folder and it will clean your peers.txt