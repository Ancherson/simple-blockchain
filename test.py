import hashlib
import time
import json
from urllib.parse import urlparse
import requests

class Block:
    def __init__(self, index, timestamp, data, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        sha = hashlib.sha256()
        sha.update(str(self.index).encode('utf-8') +
                   str(self.timestamp).encode('utf-8') +
                   str(self.data).encode('utf-8') +
                   str(self.previous_hash).encode('utf-8') +
                   str(self.nonce).encode('utf-8'))
        return sha.hexdigest()

    def mine_block(self, difficulty):
        while self.hash[:difficulty] != '0'*difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print("Block mined: ", self.hash)


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2
        self.nodes = set()
        self.pending_transactions = []

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_block):
        new_block.previous_hash = self.get_latest_block().hash
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def register_node(self, node_url):
        parsed_url = urlparse(node_url)
        self.nodes.add(parsed_url.netloc)

    def verify_chain(self):
        other_chains = []
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                chain = response.json()['chain']
                other_chains.append(chain)
        longest_chain = self.chain
        for chain in other_chains:
            if len(chain) > len(longest_chain) and self.is_chain_valid(chain):
                longest_chain = chain
        self.chain = longest_chain

    def submit_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self, miner_reward_address):
        if not self.pending_transactions:
            return False
        new_block = Block(len(self.chain), time.time(), self.pending_transactions, self.get_latest_block().hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        self.pending_transactions = [
            {"from": "network", "to": miner_reward_address, "amount": 1.0},
        ]
        return True

    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for transaction in block.data:
                if transaction["from"] == address:
                    balance -= transaction["amount"]
                elif transaction["to"] == address:
                    balance += transaction["amount"]
        return balance

    def get_chain(self):
        chain_data = []
        for block in self.chain:
            chain_data.append(block.__dict__)
        return {"length": len(chain_data), "chain": chain_data}


# Exemple d'utilisation avec deux noeuds

blockchain_node1 = Blockchain()
blockchain_node2 = Blockchain()
blockchain_node1.register_node("http://127.0.0.1:5001")
blockchain_node2.register_node("http://127.0.0.1:5000")

# Ajout d'une transaction sur le noeud 1
blockchain_node1.submit_transaction({"from": "John", "to": "Alice", "amount": 3.0})
blockchain_node1.submit_transaction({"from": "Alice", "to": "Bob", "amount": 1.0})
blockchain_node1.mine_pending_transactions("miner-address")

# Vérification de la chaîne sur le noeud 2
print("Chaîne du noeud 2 avant vérification:")
print(blockchain_node2.get_chain())
blockchain_node2.verify_chain()
print("Chaîne du noeud 2 après vérification:")
print(blockchain_node2.get_chain())

# Ajout d'une transaction sur le noeud 2
blockchain_node2.submit_transaction({"from": "Alice", "to": "John", "amount": 2.0})
blockchain_node2.mine_pending_transactions("miner-address")

# Vérification de la chaîne sur le noeud 1
print("Chaîne du noeud 1 avant vérification:")
print(blockchain_node1.get_chain())
blockchain_node1.verify_chain()
print("Chaîne du noeud 1 après vérification:")
print(blockchain_node1.get_chain())

# Affichage des soldes
print("Solde de John: ", blockchain_node1.get_balance("John"))
print("Solde de Alice: ", blockchain_node1.get_balance("Alice"))
print("Solde de Bob: ", blockchain_node1.get_balance("Bob"))
