# optiminer.py v0.1 ported from miner_opt.py v0.1 by Primedigger
# adjusted to support latest Bismuth client 3.491
# to be used with Python2
# 
# Original script information
# ///////////////////////////
# Optimized CPU-miner by Primedigger for the Bismuth cryptocurrency, see https://github.com/hclivess/Bismuth
#
# Bitcointalk thread: https://bitcointalk.org/index.php?topic=1896497.0 (main)
# https://bitcointalk.org/index.php?topic=1898984.120 (buy / sell Bismuth) 
# 
#
# Based on the observation that only a small part of the time is spend calculating sha224 hashes in the reference miner
# This is mostly due to "def bin_convert" being quite expensive in Python (the function is named bin_convert_orig in this implementation) 
# and also the SQL commands for calculating the diff taking a long time
#
# 

import math, base64, sqlite3, os, hashlib, time, socks, keys, log, re, connections
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto import Random
from multiprocessing import Process, freeze_support

# After how many cycles to print speed message. In this miner version, 1 cycle = num_block_hashes
debug_print_mod = 10

# num_block_hashes specifies how many iterations nonce should be increased by +1
# before diff and the random part of the nonce is recaluated.
# This number can be tuned. It shouldn't be too high, otherwise you miss out on diff changes.
num_block_hashes = 10000

# load config
lines = [line.rstrip('\n') for line in open('config.txt')]
for line in lines:
    if "port=" in line:
        port = line.strip('port=')
    if "mining_ip=" in line:
        mining_ip_conf = line.strip("mining_ip=")
    if "mining_threads=" in line:
        mining_threads_conf = line.strip('mining_threads=')
    if "diff_recalc=" in line:
        diff_recalc_conf = line.strip('diff_recalc=')
    if "tor=" in line:
        tor_conf = int(line.strip('tor='))
    if "miner_sync=" in line:
        sync_conf = int(line.strip('miner_sync='))
    if "debug_level=" in line:
        debug_level_conf = line.strip('debug_level=')
# load config

def check_uptodate(interval, app_log):
    # check if blocks are up to date
    while sync_conf == 1:
        conn = sqlite3.connect("static/ledger.db")  # open to select the last tx to create a new hash from
        conn.text_factory = str
        c = conn.cursor()

        execute(c, ("SELECT timestamp FROM transactions WHERE reward != 0 ORDER BY block_height DESC LIMIT 1;"), app_log)
        timestamp_last_block = c.fetchone()[0]
        time_now = str(time.time())
        last_block_ago = float(time_now) - float(timestamp_last_block)

        if last_block_ago > interval:
            app_log.warning("Local blockchain is {} minutes behind ({} seconds), waiting for sync to complete".format(int(last_block_ago) / 60,last_block_ago))
            time.sleep(5)
        else:
            break
        conn.close()
    # check if blocks are up to date

def send(sdef, data):
    sdef.sendall(data)

bin_format_dict = dict((x,format(ord(x), 'b')) for x in '0123456789abcdef')

def bin_convert(string):
    return ''.join(bin_format_dict[x] for x in string)

def bin_convert_orig(string):
    return ''.join(format(ord(x), 'b') for x in string)

def execute(cursor, what, app_log):
    # secure execute for slow nodes
    passed = 0
    while passed == 0:
        try:
            # print cursor
            # print what

            cursor.execute(what)
            passed = 1
        except Exception, e:
            app_log.warning("Retrying database execute due to {}".format(e))
            time.sleep(0.1)
            pass
            # secure execute for slow nodes
    return cursor

def execute_param(cursor, what, param, app_log):
    # secure execute for slow nodes
    passed = 0
    while passed == 0:
        try:
            # print cursor
            # print what
            cursor.execute(what, param)
            passed = 1
        except Exception, e:
            app_log.warning("Retrying database execute due to {}".format(e))
            time.sleep(0.1)
            pass
            # secure execute for slow nodes
    return cursor

def miner(q,privatekey_readable, public_key_hashed, address):
    from Crypto.PublicKey import RSA
    Random.atfork()
    key = RSA.importKey(privatekey_readable)
    app_log = log.log("miner_"+q+".log",debug_level_conf)
    rndfile = Random.new()
    tries = 0

    while True:
        try:
            tries = tries +1
            start_time = time.time()

            #
            # You can also remove the 1==1 and do the diff recalcuation ever so often (with tries % x).
            # But you might miss out on diff changes and produce a wrong block with a wrong diff
            # 

            if 1==1: #tries % 2 == 0 or tries == 1: #only do this ever so often
                block_timestamp = '%.2f' % time.time()

                conn = sqlite3.connect("static/ledger.db") #open to select the last tx to create a new hash from
                conn.text_factory = str
                c = conn.cursor()
                execute(c ,("SELECT block_hash, timestamp FROM transactions WHERE reward != 0 ORDER BY block_height DESC LIMIT 1;"), app_log)
                result = c.fetchall()
                db_block_hash = result[0][0]
                timestamp_last_block = float(result[0][1])

                # calculate difficulty
                execute_param(c, ("SELECT block_height FROM transactions WHERE CAST(timestamp AS INTEGER) > ? AND reward != 0"), (timestamp_last_block - 1800,), app_log)  # 1800=30 min
                blocks_per_30 = len(c.fetchall())

                diff = blocks_per_30 * 2

                # drop diff per minute if over target
                time_drop = time.time()

                drop_factor = 120  # drop 0,5 diff per minute

                if time_drop > timestamp_last_block + 120:  # start dropping after 2 minutes
                    diff = diff - (time_drop - timestamp_last_block) / drop_factor  # drop 0,5 diff per minute (1 per 2 minutes)

                if time_drop > timestamp_last_block + 300 or diff < 37:  # 5 m lim
                    diff = 37  # 5 m lim
                        # drop diff per minute if over target 

                #app_log.warning("Mining, {} cycles passed in thread {}, difficulty: {}, {} blocks per minute".format(tries,q,diff,blocks_per_minute))
                diff = int(diff)


            if tries % debug_print_mod == 0:
                print 'db_block_hash:', db_block_hash, 'diff:',diff
            
            nonce_acc_len = 8
            nonce_acc_pf = "%." + str(nonce_acc_len) + "x"
            nonce = hashlib.sha224(rndfile.read(16)+str(q)).hexdigest()[:32 - nonce_acc_len]
            count = 0

            mining_condition_bin = bin_convert_orig(db_block_hash)[0:diff]

            mining_condition_test_bin = ''
            diff_hex = 0
            while(len(mining_condition_test_bin) < diff):
                diff_hex += 1
                mining_condition_test_bin = bin_convert(db_block_hash[0:diff_hex])
            diff_hex -= 1

            mining_condition = db_block_hash[0:diff_hex]

            hash_time = 0.0

            

            # Compute the static part of the hash (this doesn't change if we change the nonce)
            start_hash = hashlib.sha224()
            start_hash.update(address)
            
            # efficiently scan nonces
            for count in xrange(num_block_hashes):
                try_nonce = nonce + (nonce_acc_pf % count)

                mining_hash_lib = start_hash.copy()
                mining_hash_lib.update(try_nonce + db_block_hash)
                #hash_stop_time = time.time()

                #hash_time += hash_stop_time - hash_start_time

                mining_hash = mining_hash_lib.hexdigest()  # hardfork
                
                # we first check hex diff, then binary diff
                if mining_condition in mining_hash:
                    if mining_condition_bin in bin_convert(mining_hash):
                        #recheck
                        mining_hash_check = hashlib.sha224(address + try_nonce + db_block_hash).hexdigest()
                        if mining_hash_check != mining_hash or mining_condition_bin not in bin_convert_orig(mining_hash_check):
                            print "FOUND block, but block hash doesn't match:", mining_hash_check, 'vs.', mining_hash
                            break
                        else:
                            print "YAY FOUND BLOCK, CHECK CORRECT"
                            print "NEW BLOCK HASH: ", mining_hash_check, "mining condition:", mining_condition

                        app_log.warning("Thread {} found a good block hash in {} cycles".format(q,tries))

                        # serialize txs
                        mempool = sqlite3.connect("mempool.db")
                        mempool.text_factory = str
                        m = mempool.cursor()
                        execute(m, ("SELECT * FROM transactions ORDER BY timestamp;"), app_log)
                        result = m.fetchall()  # select all txs from mempool
                        mempool.close()

                        #include data
                        block_send = []
                        del block_send[:]  # empty
                        removal_signature = []
                        del removal_signature[:]  # empty

                        for dbdata in result:
                            transaction = (
                                str(dbdata[0]), str(dbdata[1][:56]), str(dbdata[2][:56]), '%.8f' % float(dbdata[3]), str(dbdata[4]), str(dbdata[5]), str(dbdata[6]),
                                str(dbdata[7]))  # create tuple
                            # print transaction
                            block_send.append(transaction)  # append tuple to list for each run
                            removal_signature.append(str(dbdata[4]))  # for removal after successful mining

                        # claim reward
                        transaction_reward = tuple
                        transaction_reward = (str(block_timestamp), str(address[:56]), str(address[:56]), '%.8f' % float(0), "0", str(try_nonce))  # only this part is signed!
                        # print transaction_reward

                        h = SHA.new(str(transaction_reward))
                        signer = PKCS1_v1_5.new(key)
                        signature = signer.sign(h)
                        signature_enc = base64.b64encode(signature)

                        block_send.append((str(block_timestamp), str(address[:56]), str(address[:56]), '%.8f' % float(0), str(signature_enc),
                                           str(public_key_hashed), "0", str(try_nonce)))  # mining reward tx
                        # claim reward
                        # include data

                        tries = 0

                        #submit mined block to node

                        if sync_conf == 1:
                            check_uptodate(300, app_log)

			global peer_dict
			peer_dict = {}
			with open("peers.txt") as f:
				for line in f:
					line = re.sub("[\)\(\:\\n\'\s]", "", line)
					peer_dict[line.split(",")[0]] = line.split(",")[1]

				for k, v in peer_dict.items():
					peer_ip = k
					# app_log.info(HOST)
					peer_port = int(v)
					# app_log.info(PORT)
			# connect to all nodes

					try:
						s = socks.socksocket()
						s.settimeout(0.3)
						if tor_conf == 1:
							s.setproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
						s.connect((peer_ip, int(peer_port)))  # connect to node in peerlist
						app_log.warning("Connected")

						app_log.warning("Miner: Proceeding to submit mined block")

						connections.send(s, "block", 10)
						connections.send(s, block_send, 10)

						app_log.warning("Miner: Block submitted to {}".format(peer_ip))
					except Exception, e:
						app_log.warning("Miner: Could not submit block to {} because {}".format(peer_ip,e))
						pass

                        #remove sent from mempool
                        mempool = sqlite3.connect("mempool.db")
                        mempool.text_factory = str
                        m = mempool.cursor()
                        for x in removal_signature:
                            execute_param(m,("DELETE FROM transactions WHERE signature =?;"),(x,), app_log)
                            app_log.warning("Removed a transaction with the following signature from mempool: {}".format(x))
                        mempool.commit()
                        mempool.close()

                count += 1
            stop_time = time.time()
            time_diff = stop_time - start_time


            if tries % debug_print_mod == 0:
                print time_diff, ' for '+str(num_block_hashes)+' hashes', float(num_block_hashes) / float(time_diff) , ' hashes per sec in thread', q

                #remove sent from mempool

            #submit mined block to node

                #break
        except Exception, e:
            print e
            time.sleep(0.1)
            raise

if __name__ == '__main__':
    freeze_support()  # must be this line, dont move ahead

    app_log = log.log("miner.log",debug_level_conf)
    (key, private_key_readable, public_key_readable, public_key_hashed, address) = keys.read()

    if not os.path.exists('mempool.db'):
        # create empty mempool
        mempool = sqlite3.connect('mempool.db')
        mempool.text_factory = str
        m = mempool.cursor()
        execute(m,("CREATE TABLE IF NOT EXISTS transactions (timestamp, address, recipient, amount, signature, public_key, openfield)"), app_log)
        mempool.commit()
        mempool.close()
        app_log.warning("Core: Created mempool file")
        # create empty mempool
    else:
        app_log.warning("Mempool exists")

    # verify connection
    connected = 0
    while connected == 0:
        try:
            s = socks.socksocket()
            if tor_conf == 1:
                s.setproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
            s.connect((mining_ip_conf, int(port)))
            app_log.warning("Connected")
            connected = 1
            s.close()
        except Exception, e:
            print e
            app_log.warning(
                "Miner: Please start your node for the block to be submitted or adjust mining ip in settings.")
            time.sleep(1)
    # verify connection
    if sync_conf == 1:
        check_uptodate(120, app_log)

    instances = range(int(mining_threads_conf))
    print instances
    for q in instances:
        p = Process(target=miner,args=(str(q+1),private_key_readable, public_key_hashed, address))
        p.daemon = True
        p.start()
        print "thread "+str(p)+ " started"
    for q in instances:
        p.join()
        p.terminate()
