import socket
import hashlib
import json

# Initialisation du client
HOST = 'localhost'
PORT = 8888
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Fonction pour ajouter une transaction
def add_transaction(data):
    message = f'{data}'
    client_socket.sendto(message.encode('utf-8'), (HOST, PORT))
    response, _ = client_socket.recvfrom(1024)
    print(response.decode('utf-8'))

# Fonction pour obtenir la blockchain complète
def get_blockchain(bool = True):
    client_socket.sendto('get blockchain'.encode('utf-8'), (HOST, PORT))
    blockchain = []
    while True:
        block, _ = client_socket.recvfrom(1024)
        block = block.decode('utf-8')
        if block == 'end of blockchain':
            break
        blockchain.append(block)
    if bool :
        print('\n'.join(blockchain))
    return blockchain




def get_proof_of_work(prev_nounce,DIFFICULTY,block_str):
    """
    Calcule le nounce pour la cible donnée.

    Args:
        DIFFICULTY (int): Cible de la preuve de travail.

    Returns:
        int: Le nounce valide trouvé.
    """
    block = json.loads(block_str)
    block["nonce"] = prev_nounce
    hash_str = json.dumps(block).encode("utf-8")
    hash_val = hashlib.sha256(hash_str).hexdigest()
    print(hash_val)
    if hash_val[:DIFFICULTY] == '0'*DIFFICULTY:
        return prev_nounce
    else:
        None

def hash_block(block):
        block_string = json.dumps(block).encode("utf-8")
        return hashlib.sha256(block_string).hexdigest()

def check_Integrity(blockchain):
        last_hash = 0
        good_chain = []
        for elt in blockchain:
            good_chain.append(eval(elt.replace("'", "\"")))
        for current_block in good_chain:
            if current_block['index'] > 1 :
                if current_block["previous_hash"] != last_hash :
                    print("Blockchain is compromised !")
                    print(f"Blockchain's block {current_block['index']-1} has modified DATA !!\n")
                    return False
            last_hash = hash_block(current_block)
        print("Blockchain is good\n")
        return True

# Boucle principale du client
while True:
    print('Que souhaitez-vous faire ?')
    print('1. Ajouter une transaction')
    print('2. Obtenir la blockchain complète')
    print('3. Devenir un mineur de block')
    print('4. Verifier l\'intégrité')
    print('5. Quittez')
    print('6. Devenir un mineur de block en partant d\'un nonce x')

    choice = input()

    if choice == '1':
        data = input('Entrez les données de la transaction : ')
        add_transaction(data)
    elif choice == '2':
        get_blockchain()
    elif choice == '3':
        # Configuration de la socket en broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("", 5000))
        data, _ = sock.recvfrom(1024)
        print(data.decode("utf-8"))
        message = data.decode("utf-8").split('|')[0]
        if message == 'Demande de nounce pour une preuve de travail':
            DIFFICULTY = data.decode("utf-8").split('|')[1]
            previous_hash = data.decode("utf-8").split('|')[2]
        # sock.setblocking(False)
        sock.settimeout(1/10000)
        prev_nounce = 0
        # Boucle d'attente de demande de nounce
        while True:
            
            try:
                data, _ = sock.recvfrom(1024)
                message = data.decode("utf-8").split('|')[0]
            except (socket.timeout, ValueError):
                pass

            
            if message == 'Demande de nounce pour une preuve de travail':
                DIFFICULTY = int(DIFFICULTY)  # Valeur de la cible de la preuve de travail
                print(prev_nounce)
                nonce = get_proof_of_work(prev_nounce,DIFFICULTY,previous_hash)
                prev_nounce += 1
                if nonce != None:
                    answer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,)
                    answer_socket.sendto(str(nonce).encode("utf-8"), ('localhost',8887))
                    break
            elif message == 'Fin de la recherche de nounce':
                print("stopped, Somebody found it :(\n")
                break

        sock.close()
        
        
    elif choice == '4':
        blockchain = get_blockchain(False)
        check_Integrity(blockchain)
        
        
    elif choice == '5':
        break
    elif choice == '6':
        print("Veillez rentrer x un nombre, la recherche du nonce se fera à partir de x:")
        prev_nounce = int(input())
                # Configuration de la socket en broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(("", 5000))
        data, _ = sock.recvfrom(1024)
        print(data.decode("utf-8"))
        message = data.decode("utf-8").split('|')[0]
        if message == 'Demande de nounce pour une preuve de travail':
            DIFFICULTY = data.decode("utf-8").split('|')[1]
            previous_hash = data.decode("utf-8").split('|')[2]
        # sock.setblocking(False)
        sock.settimeout(1/10000)
        # Boucle d'attente de demande de nounce
        while True:
            try:
                data, _ = sock.recvfrom(1024)
                message = data.decode("utf-8").split('|')[0]
            except (socket.timeout, ValueError):
                pass

            
            if message == 'Demande de nounce pour une preuve de travail':
                DIFFICULTY = int(DIFFICULTY)  # Valeur de la cible de la preuve de travail
                print(prev_nounce)
                nonce = get_proof_of_work(prev_nounce,DIFFICULTY,previous_hash)
                prev_nounce += 1
                if nonce != None:
                    answer_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,)
                    answer_socket.sendto(str(nonce).encode("utf-8"), ('localhost',8887))
                    break
            elif message == 'Fin de la recherche de nounce':
                print("stopped, Somebody found it :(\n")
                break

        sock.close()
        

    else:
        print('Choix invalide\n')



