from hashlib import sha256
import time
import json
import os
import random
from flask import Flask, request, jsonify
from ecdsa import SigningKey, VerifyingKey, SECP256k1

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = 0
        self.stakeholder = None  # Para PoS

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

class Blockchain:
    difficulty = 2
    reward = 50  # Recompensa fija por bloque minado
    max_supply = 21000000  # Máximo suministro de monedas

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.total_supply = 0  # Total de monedas emitidas
        self.stakes = {}  # Diccionario de participaciones para PoS
        self.balances = {}  # Diccionario de balances para las direcciones de wallets
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), '0'*64)
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_new_transaction(self, transaction):
        # Verificar que la transacción esté firmada correctamente
        if self.verify_transaction(transaction):
            self.unconfirmed_transactions.append(transaction)
        else:
            return False

    def mine(self):
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block
        if last_block.index % 2 == 0:
            # Use PoW
            new_block = Block(index=last_block.index + 1,
                              transactions=self.unconfirmed_transactions,
                              timestamp=time.time(),
                              previous_hash=last_block.hash)
            proof = self.proof_of_work(new_block)
        else:
            # Use PoS
            stakeholder = self.select_stakeholder()
            if not stakeholder:
                return False
            new_block = Block(index=last_block.index + 1,
                              transactions=self.unconfirmed_transactions,
                              timestamp=time.time(),
                              previous_hash=last_block.hash)
            new_block.stakeholder = stakeholder
            proof = self.proof_of_stake(new_block)

        if self.add_block(new_block, proof):
            self.total_supply += Blockchain.reward  # Incrementa el suministro total
            self.update_balances(new_block)
            self.unconfirmed_transactions = []
            return new_block.index
        return False

    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0'*Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def proof_of_stake(self, block):
        return block.compute_hash()

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash
        if previous_hash != block.previous_hash:
            return False
        if not self.is_valid_proof(block, proof):
            return False
        if self.total_supply + Blockchain.reward > Blockchain.max_supply:
            return False  # No permite superar el suministro máximo
        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        if block.index % 2 == 0:
            # PoW
            return block_hash.startswith('0'*Blockchain.difficulty) and block_hash == block.compute_hash()
        else:
            # PoS
            return block_hash == block.compute_hash() and block.stakeholder is not None

    def select_stakeholder(self):
        if not self.stakes:
            return None
        total_stake = sum(self.stakes.values())
        selection = random.uniform(0, total_stake)
        current = 0
        for stakeholder, stake in self.stakes.items():
            current += stake
            if current > selection:
                return stakeholder
        return None

    def add_stake(self, stakeholder, amount):
        if stakeholder in self.stakes:
            self.stakes[stakeholder] += amount
        else:
            self.stakes[stakeholder] = amount

    def update_balances(self, block):
        for tx in block.transactions:
            sender = tx['sender']
            receiver = tx['receiver']
            amount = tx['amount']
            self.balances[sender] -= amount
            self.balances[receiver] = self.balances.get(receiver, 0) + amount
        # Recompensa de minado
        if block.index % 2 == 0:
            miner = tx['sender']
            self.balances[miner] = self.balances.get(miner, 0) + self.reward

    def verify_transaction(self, transaction):
        sender_public_key = transaction['sender_public_key']
        signature = bytes.fromhex(transaction['signature'])
        tx_data = json.dumps(transaction['data'], sort_keys=True).encode()

        verifying_key = VerifyingKey.from_string(bytes.fromhex(sender_public_key), curve=SECP256k1)
        return verifying_key.verify(signature, tx_data)

# Flask web application
app = Flask(__name__)

# Initialize a Blockchain object
blockchain = Blockchain()

# Path to store peers
peers_file = 'peers.json'

# Load peers from file
if os.path.exists(peers_file):
    with open(peers_file, 'r') as f:
        peers = set(json.load(f))
else:
    peers = set()

# Endpoint to add a new transaction
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["sender", "receiver", "amount", "sender_public_key", "signature"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    transaction = {
        "data": {
            "sender": tx_data["sender"],
            "receiver": tx_data["receiver"],
            "amount": tx_data["amount"]
        },
        "sender_public_key": tx_data["sender_public_key"],
        "signature": tx_data["signature"]
    }

    if blockchain.add_new_transaction(transaction):
        return "Success", 201
    else:
        return "Transaction verification failed", 400

# Endpoint to mine new blocks
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine or maximum supply reached"
    return f"Block #{result} is mined."

# Endpoint to view the blockchain
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data), "chain": chain_data})

# Endpoint to add new peers
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    peers.add(node_address)
    with open(peers_file, 'w') as f:
        json.dump(list(peers), f)
    
    return get_chain()

if __name__ == '__main__':
    app.run(debug=True, port=8000)
