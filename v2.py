from hashlib import sha256
import time
import json
import os
from flask import Flask, request, jsonify

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = 0

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
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), '0'*64)
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        if self.add_block(new_block, proof):
            self.total_supply += Blockchain.reward  # Incrementa el suministro total
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
        return (block_hash.startswith('0'*Blockchain.difficulty) and block_hash == block.compute_hash())

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
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()
    blockchain.add_new_transaction(tx_data)
    return "Success", 201

# Endpoint to mine new blocks
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine or maximum supply reached"
    return f"Block #{result} is mined."

# Endpoint to return the blockchain
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return jsonify(length=len(chain_data), chain=chain_data, total_supply=blockchain.total_supply)

# Endpoint to add new peers
@app.route('/register_node', methods=['POST'])
def register_new_peer():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    peers.add(node_address)
    with open(peers_file, 'w') as f:
        json.dump(list(peers), f)
    return get_chain()

# Endpoint to register with another node
def register_with_existing_node(node_address):
    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}
    response = requests.post(f"{node_address}/register_node", data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        with open(peers_file, 'w') as f:
            json.dump(list(peers), f)
        return True
    return False

def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.chain = []
    for block_data in chain_dump:
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"])
        block.hash = block_data["hash"]
        generated_blockchain.chain.append(block)
    return generated_blockchain

# Run the Flask web application
app.run(port=5000)
