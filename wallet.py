from ecdsa import SigningKey, SECP256k1
import hashlib
import base58

def generate_keys():
    # Generar clave privada utilizando la curva SECP256k1
    private_key = SigningKey.generate(curve=SECP256k1)
    private_key_bytes = private_key.to_string()

    # Obtener la clave pública correspondiente
    public_key = private_key.get_verifying_key()
    public_key_bytes = public_key.to_string()

    # Generar la dirección de la wallet
    # 1. Aplicar SHA-256 a la clave pública
    sha256_pk = hashlib.sha256(public_key_bytes).digest()
    
    # 2. Aplicar RIPEMD-160 a la salida de SHA-256
    ripemd160 = hashlib.new('ripemd160')
    ripemd160.update(sha256_pk)
    public_key_hash = ripemd160.digest()

    # 3. Agregar el prefijo de versión (0x00 para Bitcoin)
    versioned_payload = b'\x00' + public_key_hash

    # 4. Aplicar SHA-256 dos veces
    sha256_1 = hashlib.sha256(versioned_payload).digest()
    sha256_2 = hashlib.sha256(sha256_1).digest()

    # 5. Tomar los primeros 4 bytes del segundo SHA-256 (checksum)
    checksum = sha256_2[:4]

    # 6. Agregar el checksum al payload versionado
    binary_address = versioned_payload + checksum

    # 7. Codificar en Base58
    wallet_address = base58.b58encode(binary_address).decode('utf-8')

    return {
        'private_key': private_key_bytes.hex(),
        'public_key': public_key_bytes.hex(),
        'wallet_address': wallet_address
    }

# Generar las claves
keys = generate_keys()
print(f"Private Key: {keys['private_key']}")
print(f"Public Key: {keys['public_key']}")
print(f"Wallet Address: {keys['wallet_address']}")
