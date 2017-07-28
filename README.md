# stuff
General things

# optiminer.py

optiminer.py to be used with Python3.5

Optimized CPU-miner for Bismuth cryptocurrency

Change for dev pool mining capability as well as current Python3.5 based local node

Just adjust your config.txt as needed and use with python3.5

Copyright Hclivess, Primedigger, Maccaspacca 2017

# optipool.py

optipool.py to be used with Python3.5

Optimized CPU-miner for Bismuth cryptocurrency dev pool mining only

Copyright Hclivess, Primedigger, Maccaspacca 2017

Dev pool Diff can be passed as an optional argument on startup. If not set it defaults to 50

E.g. 'python3 optipool.py 60' would set the diff to 60
E.g. 'python3 optipool.py' would default to diff 50

No variable diff down in this one

# optipool.exe

1. Place into Bismuth application folder (C:\Program Files (x86)\Bismuth)
2. For mining to poolware.py pool only (e.g. main official pool or your own private one) so adjust config.txt
3. Run from command prompt once node is up to date
4. Command> optipool.exe
5. Defaults to diff of 50 or you can place as arguement in command

Tested on Windows 10

Users on earlier windows versions may need to install https://www.microsoft.com/enus/download/details.aspx?id=48234

# optiminer.exe

1. Place into Bismuth application folder (C:\Program Files (x86)\Bismuth)
2. For mining to poolware.py pool (e.g. main official pool or your own private one) or solo so adjust config.txt
3. Drop in alternative to default miner
4. Command> optiminer.exe

Tested on Windows 10

Users on earlier windows versions may need to install https://www.microsoft.com/enus/download/details.aspx?id=48234

# peer_clean.py

Cleans Bismuth peers.txt of duplicates and nodes on same first network octet thus improving geographic spread of peers

Run from command line in Bismuth folder and it will clean your peers.txt