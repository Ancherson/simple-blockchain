import socket
import hashlib
import datetime
import json

# Initialisation du serveur
HOST = "localhost"
PORT = 8888
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,)
server_socket.bind((HOST, PORT))

broad_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,socket.IPPROTO_UDP)
broad_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
broad_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# Définition des constantes de la blockchain
DIFFICULTY = 4  # Nombre de zéros requis au début du hash
BLOCK_SIZE = 1  # Nombre de transactions par bloc
BLOCKCHAIN_FILENAME = "blockchain.json"

class Blockchain:        
    def __init__(self,chain = []):
        self.chain = chain
        self.pending_transactions = []
        if chain == [] :
            self.create_genesis_block()
        self.check_Integrity()
        

    def create_genesis_block(self):
        block = {
            "index": 0,
            "timestamp": str(datetime.datetime.now()),
            "transactions": ["Permier block, première transaction"],
            "previous_hash": "0"*64,
            "nonce": 0
        }
        while self.hash_block(block)[:DIFFICULTY] != '0'*DIFFICULTY:
            block["nonce"] = block["nonce"] + 1
            
        self.chain.append(block)
        with open(BLOCKCHAIN_FILENAME, 'w') as f:
            f.write("{\"blockchain\":[]}")
        self.write_json(json.dumps(block))

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)

        if len(self.pending_transactions) == BLOCK_SIZE:
            self.mine_block()

    def mine_block(self):
        last_block = self.chain[-1]
        index = int(last_block["index"] )+ 1
        timestamp = str(datetime.datetime.now())
        transactions = self.pending_transactions.copy()
        previous_hash = self.hash_block(last_block)
        nonce = get_valid_nonce(broad_sock,DIFFICULTY,block = {
            "index": index,
            "timestamp": timestamp,
            "transactions": transactions,
            "previous_hash": previous_hash,
            "nonce": 0
        })

        block = {
            "index": index,
            "timestamp": timestamp,
            "transactions": transactions,
            "previous_hash": previous_hash,
            "nonce": nonce
        }
        
        # Enregistrement de la blockchain dans un fichier
        self.write_json(json.dumps(block))

        
        self.chain.append(block)
        self.pending_transactions = []

    def hash_block(self, block):
        block_string = json.dumps(block).encode("utf-8")
        return hashlib.sha256(block_string).hexdigest()


    def to_json(self):
        return json.dumps(self.chain)
    
    def write_json(self,new_data):
        with open(BLOCKCHAIN_FILENAME,'r+') as file:
            # First we load existing data into a dict.
            file_data = json.load(file)
            # Join new_data with file_data inside emp_details
            file_data["blockchain"].append(new_data)
            # Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            json.dump(file_data, file, indent = 4)
        
    def check_Integrity(self):
        last_hash = 0
        for current_block in self.chain:
            if current_block['index'] > 0 :
                if current_block["previous_hash"] != last_hash :
                    print("Blockchain is compromised !")
                    print(f"Blockchain's block {current_block['index']-1} has modified DATA !!\n")
                    return False
            last_hash = self.hash_block(current_block)

        print("Blockchain is good")
        return True


def get_valid_nonce(sock,DIFFICULTY, block):
    """
    Envoie un message en broadcast demandant le nounce pour exécuter une proof of work
    dans le cadre d"une blockchain et attend la première réponse valide.
    """

    answer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,)
    answer_socket.bind(("localhost", 8887))
    answer_socket.settimeout(3)  # Temps d"attente maximum de x secondes

    message = f"Demande de nounce pour une preuve de travail|{DIFFICULTY}|{json.dumps(block)}"

    nonce = None
    while not nonce:
        sock.sendto(message.encode("utf-8"), ("255.255.255.255", 5000))
        try:
            data, _ = answer_socket.recvfrom(1024)
            new_nonce = int(data.decode("utf-8"))
            if check_proof_of_work(new_nonce,block, DIFFICULTY):
                print(f"le nonce {new_nonce} fonctionne, ajout du block")
                nonce = new_nonce
            else:
                sock.sendto(message.encode("utf-8"), ("255.255.255.255", 5000))
        except (socket.timeout, ValueError):
            pass
    sock.sendto(b"Fin de la recherche de nounce", ("255.255.255.255", 5000))

    return nonce


def check_proof_of_work(nonce,block, DIFFICULTY):
    """
    Vérifie si le nounce fourni est une solution valide pour la cible donnée.
    """
    block["nonce"] = nonce
    hash_val = blockchain.hash_block(block)
    return hash_val[:DIFFICULTY] == "0"*DIFFICULTY
        

# Création ou chargement de la blockchain à partir du fichier
try:
    with open(BLOCKCHAIN_FILENAME, "r") as f:
        json_list = (json.loads(f.read())["blockchain"])
        good_chain = []
        for elt in json_list:
            good_chain.append(eval(elt.replace("'", "\"")))
        
        blockchain = Blockchain(good_chain)
        print(blockchain.chain)
except FileNotFoundError:
    blockchain = Blockchain()
    print(blockchain.chain)

# Boucle principale du serveur
while True:
    # Réception d"un message du client
    message, client_address = server_socket.recvfrom(1024)
    message = message.decode("utf-8")

    # Traitement du message
    if message == "get blockchain":
        # Envoi de la blockchain complète au client
        for block in blockchain.chain:
            server_socket.sendto(str(block).encode("utf-8"), client_address)
        server_socket.sendto("end of blockchain".encode("utf-8"), client_address)
    else:
        # Ajout d"une nouvelle transaction à la blockchain
        transaction = message
        print('transaction reçu: {transaction}')
        
        # Confirmation de l"ajout du bloc au client
        response = f"Transaction ajouté au prochain block de la blockchain : {transaction}"
        server_socket.sendto(response.encode("utf-8"), client_address)
        
        blockchain.add_transaction(transaction)