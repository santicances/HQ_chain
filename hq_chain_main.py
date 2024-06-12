
from hashlib import sha256
import time
import json

class Block:

    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash


    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys = True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:

    difficulty = 2
    def __init__(self):
        self.unconfirmed_transaction = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), '0'*64)
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)
        
    @property
    def last_block(self):
        return self.chain[-1]

    def new_transaction(self, transaction):
        self.unconfirmed_transaction.append(transaction)

    def mine (self):
        if not self.unconfirmed_transaction:
            return False
        last_block = self.last_block
        new_block = Block(index = last_block.index - 1, transactions = self.unconfirmed_transaction, timestamp = time.time(), previous_hash = last_block.hash)
        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transaction = []
        return new_block.index
    
    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0'*Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_block(self, block, proof):
        previous_hash = self.last_block.hash
        if(previous_hash != block.previous_hash):
            return False
        if not self.is_valid_proof(block, proof):
            return False
        block.hash = proof
        self.chain.append(block)
        return True


    def is_valid_proof(self, block, block_hash):
        return (block_hash.startswith('0'*Blockchain.difficulty) and block_hash == block.compute_hash())


    
    def print_block(self, n):
        if (len(self.chain) < n):
            return
        else:      
            block = self.chain[n]
            return ' Index {}\n Transactions {}\n Timestamp: {}\n PreviousHash: {}\n'.format(block.index, block.transactions, block.timestamp, block.previous_hash) 




######### todo bien#############################




a = Blockchain()
a.new_transaction('1')
a.new_transaction('ukhafsdfsdfhdsfwefh')
a.mine()
len_bc = len(a.chain)
print(a.print_block(len_bc-1))