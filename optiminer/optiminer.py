# optiminer.py v 0.14 to be used with Python3.5
# Optimized CPU-miner for Bismuth cryptocurrency
# Change for dev pool mining capability as well as current Python3.5 based local node
# Just adjust your config.txt as needed and use with python3.5
# Copyright Hclivess, Primedigger, Maccaspacca 2017

import math, base64, sqlite3, os, hashlib, time, socks, keys, log, re, connections, options
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto import Random
from multiprocessing import Process, freeze_support

# After how many cycles to print speed message. In this miner version, 1 cycle = num_block_hashes
debug_print_mod = 10

# num_block_hashes specifies how many iterations nonce should be increased by +1
# before diff and the random part of the nonce is recaluated.
# This number can be tuned. It shouldn't be too high, otherwise you miss out on diff changes.
num_block_hashes = 25000

# load config
lines = [line.rstrip('\n') for line in open('config.txt')]
for line in lines:
    if "port=" in line:
        port = line.strip('port=')
    if "pool_ip=" in line:
        mining_ip_conf = line.split('=')[1]
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
    if "pool_address=" in line:
        pool_address = line.split('=')[1]
    if "mining_pool=" in line:
        pool_conf = int(line.strip('mining_pool='))
    if "ledger_path=" in line:
        ledger_path_conf = line.split('=')[1]


# load config

def nodes_block_submit(block_send, app_log):
    # connect to all nodes
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

                app_log.warning("Miner: Proceeding to submit mined block to node")

                connections.send(s, "block", 10)
                connections.send(s, block_send, 10)

                app_log.warning("Miner: Block submitted to node {}".format(peer_ip))
            except Exception as e:
                app_log.warning("Miner: Could not submit block to node {} because {}".format(peer_ip, e))
                pass

                # submit mined block to node


def check_uptodate(interval, app_log):
    # check if blocks are up to date
    while sync_conf == 1:
        conn = sqlite3.connect("static/ledger.db")  # open to select the last tx to create a new hash from
        conn.text_factory = str
        c = conn.cursor()

        execute(c, ("SELECT timestamp FROM transactions WHERE reward != 0 ORDER BY block_height DESC LIMIT 1;"),
                app_log)
        timestamp_last_block = c.fetchone()[0]
        time_now = str(time.time())
        last_block_ago = float(time_now) - float(timestamp_last_block)

        if last_block_ago > interval:
            app_log.warning("Local blockchain is {} minutes behind ({} seconds), waiting for sync to complete".format(
                int(last_block_ago) / 60, last_block_ago))
            time.sleep(5)
        else:
            break
        conn.close()
        # check if blocks are up to date


def send(sdef, data):
    sdef.sendall(data)


bin_format_dict = dict((x, format(ord(x), '8b').replace(' ', '0')) for x in '0123456789abcdef')


def bin_convert(string):
	return ''.join(bin_format_dict[x] for x in string)


def bin_convert_orig(string):
    return ''.join(format(ord(x), '8b').replace(' ', '0') for x in string)


def execute(cursor, what, app_log):
    # secure execute for slow nodes
    passed = 0
    while passed == 0:
        try:
            # print cursor
            # print what

            cursor.execute(what)
            passed = 1
        except Exception as e:
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
        except Exception as e:
            app_log.warning("Retrying database execute due to {}".format(e))
            time.sleep(0.1)
            pass
            # secure execute for slow nodes
    return cursor


def miner(q, privatekey_readable, public_key_hashed, address):
    from Crypto.PublicKey import RSA
    Random.atfork()
    key = RSA.importKey(privatekey_readable)
    app_log = log.log("miner_" + q + ".log", debug_level_conf)
    rndfile = Random.new()
    tries = 0
    firstrun = True
    begin = time.time()

    if pool_conf == 1:      
        self_address = address
        address = pool_address

    while True:
        try:
            tries = tries + 1
            start_time = time.time()
            firstrun = False
            now = time.time()
            #block_timestamp = '%.2f' % time.time()
            s = socks.socksocket()
            s.connect(("127.0.0.1", int(port)))  # connect to local node
            connections.send(s, "blocklast", 10)
            db_block_hash = connections.receive(s, 10)[7]

            connections.send(s, "diffget", 10)
            diff = float(connections.receive(s, 10))
            diff = int(diff[1])
            diff_real = int(diff)

            if pool_conf == 0:
                diff = int(diff)

            else:  # if pooled
                diff_real = int(diff)
                diff_pool = diff_real
                diff = 50

                if diff > diff_pool:
                    diff = diff_pool

            if tries % debug_print_mod == 0:
                print('db_block_hash: {} diff: {},({})'.format(db_block_hash, diff, diff_real))

            nonce_acc_len = 8
            nonce_acc_pf = "%." + str(nonce_acc_len) + "x"
            nonce = hashlib.sha224(rndfile.read(16) + str.encode(q)).hexdigest()[:32 - nonce_acc_len]
            count = 0

            mining_condition_bin = bin_convert_orig(db_block_hash)[0:diff]

            mining_condition_test_bin = ''
            diff_hex = 0
            while (len(mining_condition_test_bin) < diff):
                diff_hex += 1
                mining_condition_test_bin = bin_convert(db_block_hash[0:diff_hex])
            diff_hex -= 1

            mining_condition = db_block_hash[0:diff_hex]

            hash_time = 0.0

            # Compute the static part of the hash (this doesn't change if we change the nonce)
            start_hash = hashlib.sha224()
            start_hash.update(address.encode("utf-8"))

            # efficiently scan nonces
            for count in range(num_block_hashes):
                try_nonce = nonce + (nonce_acc_pf % count)

                mining_hash_lib = start_hash.copy()
                mining_hash_lib.update((try_nonce + db_block_hash).encode("utf-8"))
                # hash_stop_time = time.time()

                # hash_time += hash_stop_time - hash_start_time

                mining_hash = mining_hash_lib.hexdigest()  # hardfork

                # we first check hex diff, then binary diff
                if mining_condition in mining_hash:
                    block_timestamp = '%.2f' % time.time()
                    if mining_condition_bin in bin_convert(mining_hash):
                        # recheck
                        mining_hash_check = hashlib.sha224(
                            (address + try_nonce + db_block_hash).encode("utf-8")).hexdigest()
                        if mining_hash_check != mining_hash or mining_condition_bin not in bin_convert_orig(
                                mining_hash_check):
                            print("FOUND block, but block hash doesn't match:", mining_hash_check, 'vs.', mining_hash)
                            break
                        else:
                            print("YAY FOUND BLOCK, CHECK CORRECT")
                            print("NEW BLOCK HASH: ", mining_hash_check, "mining condition:", mining_condition)

                        app_log.warning("Thread {} found a good block hash in {} cycles".format(q, tries))

                        # serialize txs
                        mempool = sqlite3.connect("mempool.db")
                        mempool.text_factory = str
                        m = mempool.cursor()
                        execute(m, ("SELECT * FROM transactions ORDER BY timestamp;"), app_log)
                        result = m.fetchall()  # select all txs from mempool
                        mempool.close()

                        # include data
                        block_send = []
                        del block_send[:]  # empty
                        removal_signature = []
                        del removal_signature[:]  # empty

                        for dbdata in result:
                            transaction = (
                                str(dbdata[0]), str(dbdata[1][:56]), str(dbdata[2][:56]), '%.8f' % float(dbdata[3]),
                                str(dbdata[4]), str(dbdata[5]), str(dbdata[6]),
                                str(dbdata[7]))  # create tuple
                            # print transaction
                            block_send.append(transaction)  # append tuple to list for each run
                            removal_signature.append(str(dbdata[4]))  # for removal after successful mining

                        # claim reward
                        transaction_reward = tuple
                        transaction_reward = (str(block_timestamp), str(address[:56]), str(address[:56]), '%.8f' % float(0), "0", str(try_nonce))  # only this part is signed!
                        # print transaction_reward

                        h = SHA.new(str(transaction_reward).encode("utf-8"))
                        signer = PKCS1_v1_5.new(key)
                        signature = signer.sign(h)
                        signature_enc = base64.b64encode(signature)

                        if signer.verify(h, signature) == True:
                            app_log.warning("Signature valid")

                            block_send.append((str(block_timestamp), str(address[:56]), str(address[:56]), '%.8f' % float(0), str(signature_enc.decode("utf-8")), str(public_key_hashed), "0", str(try_nonce)))  # mining reward tx
                            app_log.warning("Block to send: {}".format(block_send))
                            # claim reward
                            # include data

                            tries = 0

                            # submit mined block to node

                            if sync_conf == 1:
                                check_uptodate(300, app_log)

                            if pool_conf == 1:
                                mining_condition = bin_convert(db_block_hash)[0:diff_real]
                                if mining_condition in mining_hash:
                                    app_log.warning("Miner: Submitting block to all nodes, because it satisfies real difficulty too")
                                    nodes_block_submit(block_send, app_log)

                                try:
                                    s = socks.socksocket()
                                    s.settimeout(0.3)
                                    if tor_conf == 1:
                                        s.setproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050)
                                    s.connect((mining_ip_conf, 8525))  # connect to pool
                                    app_log.warning("Connected")

                                    app_log.warning("Miner: Proceeding to submit mined block to pool")

                                    connections.send(s, "block", 10)
                                    connections.send(s, self_address, 10)
                                    connections.send(s, block_send, 10)

                                    app_log.warning("Miner: Block submitted to pool")

                                except Exception as e:
                                    app_log.warning("Miner: Could not submit block to pool")
                                    pass

                            if pool_conf == 0:
                                nodes_block_submit(block_send, app_log)
                        else:
                            app_log.warning("Invalid signature")

                count += 1
            stop_time = time.time()
            time_diff = stop_time - start_time

            if tries % debug_print_mod == 0:
                print(time_diff, ' for ' + str(num_block_hashes) + ' hashes', float(num_block_hashes) / float(time_diff), ' hashes per sec in thread', q)

                # remove sent from mempool

                # submit mined block to node

                # break
        except Exception as e:
            print(e)
            time.sleep(0.1)
            raise


if __name__ == '__main__':
    freeze_support()  # must be this line, dont move ahead

    app_log = log.log("miner.log", debug_level_conf)
    (key, private_key_readable, public_key_readable, public_key_hashed, address) = keys.read()

    if not os.path.exists('mempool.db'):
        # create empty mempool
        mempool = sqlite3.connect('mempool.db')
        mempool.text_factory = str
        m = mempool.cursor()
        execute(m, (
            "CREATE TABLE IF NOT EXISTS transactions (timestamp, address, recipient, amount, signature, public_key, openfield)"),
                app_log)
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
        except Exception as e:
            print(e)
            app_log.warning(
                "Miner: Please start your node for the block to be submitted or adjust mining ip in settings.")
            time.sleep(1)
    # verify connection
    if sync_conf == 1:
        check_uptodate(120, app_log)

    instances = range(int(mining_threads_conf))
    print(instances)
    for q in instances:
        p = Process(target=miner, args=(str(q + 1), private_key_readable, public_key_hashed, address))
        p.daemon = True
        p.start()
        print("thread " + str(p) + " started")
    for q in instances:
        p.join()
        p.terminate()
