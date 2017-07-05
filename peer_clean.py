# Cleans peers.txt of duplicates and nodes on same first network octet
# thus improving geographic spread of peers

import re

global netlist #so it can be accessed in multiple places
netlist = []

def clean_tuples(sent_tuples): # sent_tuples is the peer tuple list from local or remote

	cleaned = [] # holder for the adjusted peer list
	
	for tuple in sent_tuples:
		HOST = tuple[0]
		mnet = HOST.split(".")
		tnet = mnet[0] # get the first octet - normally the network id (e.g. google cloud uses 104.x.x.x so we need the 104 bit)
		match = False # we set false as we are testing for a match
		for item in netlist:
			if tnet == item: # if the network id is already in netlist then it's a match - we don't want any more this session
				match = True
		if not match:
			netlist.append(tnet) # if we don't have this yet then we want to add it
			cleaned.append(tuple) # as it is good we append to the returned tuple
	
	return cleaned # this is sent back to the caller
	
# example below
	
with open("peers.txt", "r") as peer_list:
	peers = peer_list.read()
	raw_tuples = re.findall("'([\d\.]+)', '([\d]+)'", peers)
	
	print(raw_tuples)
	print("\n")
	
	peer_tuples = clean_tuples(raw_tuples)
	
	print(peer_tuples)

output = open("peers.txt", 'w')
for x in peer_tuples:
	output.write(str(x) + "\n")
output.close()

# the peer_tuples are now clean !! so you can do things with it

