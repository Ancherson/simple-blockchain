import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests


class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.difficulty = 4  # Niveau de difficulté pour le Proof of Work
        self.miner_reward = 10  # Récompense pour le mineur qui résout le Proof of Work
        self.nodes = set()

        # Création du bloc génésis
        self.add_block(previous_hash="1", proof=100)

    def add_block(self, proof, previous_hash=None):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.pending_transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.pending_transactions = []
        self.chain.append(block)

    def submit_transaction(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self, miner_address):
        # Création de la transaction de récompense pour le mineur
        self.submit_transaction({"from": "network", "to": miner_address, "amount": self.miner_reward})

        # Résolution du Proof of Work
        last_block = self.chain[-1]
        last_proof = last_block["proof"]
        proof = self.proof_of_work(last_proof)

        # Ajout du bloc à la chaîne
        previous_hash = self.hash(last_block)
        self.add_block(proof, previous_hash)

        print("Bloc ajouté à la chaîne!")
        print("Index:", len(self.chain))
        print("Transactions:", self.pending_transactions)
        print("Preuve:", proof)
        print("Hash précédent:", previous_hash)

    def proof_of_work(self, last_proof):
        nonce = 0
        while self.valid_proof(last_proof, nonce) is False:
            nonce += 1
        return nonce

    def valid_proof(self, last_proof, nonce):
        guess = f"{last_proof}{nonce}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == "0" * self.difficulty

    def hash(self, block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def verify_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Vérification du hash précédent
            if current_block["previous_hash"] != self.hash(previous_block):
                return False

            # Vérification de la preuve de travail
            if not self.valid_proof(previous_block["proof"], current_block["proof"]):
                return False

        return True

    def get_balance(self, address):
        balance = 0
        for block in self.chain:
            for transaction in block["transactions"]:
                if transaction["from"] == address:
                    balance -= transaction["amount"]
                elif transaction["to"] == address:
                    balance += transaction["amount"]
        return balance

    def get_chain(self):
        chain_data = []
        for block in self.chain:
            chain_data.append(block)
        return chain_data


class Node:
    def __init__(self, blockchain, port):
        self.blockchain = blockchain
        self.port = port

        # Démarrage du serveur HTTP
        self.server = HTTPServer(("0.0.0.0", port), self.RequestHandler)
        self.server.blockchain = blockchain
        
    def start(self):
        print(f"Node démarré sur le port {self.port}")
        self.server.serve_forever()

    class RequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/chain":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = json.dumps(self.server.blockchain.get_chain())
                self.wfile.write(response.encode())

            elif self.path == "/balance":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                address = self.headers["X-Address"]
                balance = self.server.blockchain.get_balance(address)
                response = json.dumps({"balance": balance})
                self.wfile.write(response.encode())

            else:
                self.send_response(404)
                self.end_headers()

        def do_POST(self):
            if self.path == "/transactions/new":
                content_length = int(self.headers["Content-Length"])
                post_data = self.rfile.read(content_length)
                transaction = json.loads(post_data.decode())
                self.server.blockchain.submit_transaction(transaction)
                print("Nouvelle transaction soumise")
                self.send_response(201)
                self.end_headers()

            elif self.path == "/mine":
                miner_address = self.headers["X-Address"]
                self.server.blockchain.mine_pending_transactions(miner_address)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = json.dumps({"message": "Mining successful!"})
                self.wfile.write(response.encode())

            else:
                self.send_response(404)
                self.end_headers()


# Exemple d'utilisation de la blockchain avec deux nœuds sur des ports différents
import threading
import urllib.request

if __name__ == "__main__":
    # Création de la blockchain et des deux nœuds
    blockchain = Blockchain()
    node1 = Node(blockchain, 8000)
    node2 = Node(blockchain, 8001)

    # Démarrage des threads des nœuds
    thread1 = threading.Thread(target=node1.start)
    thread2 = threading.Thread(target=node2.start)
    thread1.start()
    thread2.start()
    
    # Envoi d'une transaction du noeud 1 au noeud 2
    transaction = {"from": "adresse1", "to": "adresse2", "amount": 5}
    headers = {"Content-type": "application/json", "X-Address": "adresse1"}
    req = urllib.request.Request(url="http://localhost:8000/transactions/new", headers=headers, data=json.dumps(transaction).encode())
    response = urllib.request.urlopen(req)
    print(response.read().decode())

    # Minage d'un bloc pour valider la transaction
    headers = {"X-Address": "adresse2"}
    req = urllib.request.Request(url="http://localhost:8001/mine", headers=headers)
    response = urllib.request.urlopen(req)
    print(response.read().decode())

    # Vérification de l'état de la chaîne sur les deux nœuds
    req = urllib.request.urlopen("http://localhost:8000/chain")
    print(req.read().decode())
    req = urllib.request.urlopen("http://localhost:8001/chain")
    print(req.read().decode())

    # Vérification du solde de l'adresse 1 sur les deux nœuds
    headers = {"X-Address": "adresse1"}
    req = urllib.request.Request(url="http://localhost:8000/balance", headers=headers)
    response = urllib.request.urlopen(req)
    print(response.read().decode())
    req = urllib.request.Request(url="http://localhost:8001/balance", headers=headers)
    response = urllib.request.urlopen(req)
    print(response.read().decode())
