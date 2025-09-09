---
layout: default
title: derive_session_key()
permalink: /derive_session_key/
---

<script>
document.documentElement.style.setProperty('--bg-color', '#0d1117');
document.body.style.backgroundColor = '#0d1117';
document.body.style.color = '#f0f6fc';
</script>


<style>
.butterfly-diagram {
  text-align: center;
  margin: 20px 0;
  padding: 20px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
}
</style>

# SecureCrypto.derive_session_key()

*ECDH + HKDF key derivation for authenticated session establishment*

## Overview

The core cryptographic method that establishes a secure session key using Elliptic Curve Diffie-Hellman (ECDH) key exchange combined with HKDF key derivation. This method fuses the ephemeral key exchange with a pre-shared authentication token to create a session key that provides both perfect forward secrecy and mutual authentication.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    derive_session_key [label="derive_session_key()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    x25519_from_public [label="x25519.X25519PublicKey.from_public_bytes()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    private_exchange [label="private_key.exchange()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    hkdf [label="HKDF" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    chacha20 [label="ChaCha20Poly1305()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> derive_session_key [color="#6e7681"];
    receive_files -> derive_session_key [color="#6e7681"];
    derive_session_key -> x25519_from_public [color="#6e7681"];
    derive_session_key -> private_exchange [color="#6e7681"];
    derive_session_key -> hkdf [color="#6e7681"];
    derive_session_key -> chacha20 [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

- **`peer_public_key_bytes`** (bytes): Raw peer's X25519 public key (exactly 32 bytes)
- **`shared_token`** (str): Authentication token in format "word-word" (e.g., "ocean-tiger")

## Return Value

**None** - Method modifies internal state by setting `self.cipher` for subsequent encryption/decryption operations.

## Requirements

derive_session_key() shall compute shared secret using X25519 ECDH when peer public key bytes are provided where the shared secret enables secure communication.

derive_session_key() shall derive session key using HKDF-SHA256 when shared secret is computed where the derivation combines shared secret with authentication token.

derive_session_key() shall initialize ChaCha20Poly1305 cipher when session key is derived where the cipher enables authenticated encryption operations.

derive_session_key() shall use authentication token as HKDF salt when deriving session key where the token provides mutual authentication.

derive_session_key() shall produce 256-bit session key when key derivation completes where the key provides sufficient cryptographic strength.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: derive_session_key(peer_public_key_bytes, shared_token)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Input validation
    check_peer_key [label="peer_public_key_bytes provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_key_len [label="len(peer_public_key_bytes) == 32?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_token [label="shared_token provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_token [label="Token format 'word-word'?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_private_key [label="Private key established?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Key exchange process
    load_peer_key [label="X25519PublicKey.from_public_bytes()\nLoad peer's public key" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    perform_ecdh [label="private_key.exchange(peer_public_key)\nCompute ECDH shared secret (32 bytes)" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Key derivation
    prep_hkdf [label="Prepare HKDF-SHA256:\nsalt = shared_token.encode('utf-8')\ninfo = b'session'" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    derive_key [label="HKDF.derive(32)\nDerive 256-bit session key" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    
    // Cipher initialization
    init_cipher [label="ChaCha20Poly1305(session_key)\nInitialize AEAD cipher" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    store_cipher [label="self.cipher = cipher\nStore for encrypt/decrypt ops" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    
    // Success path
    end_success [label="Session key established\n(Ready for encryption)" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Error paths
    error_no_peer_key [label="ValueError:\nPeer public key not provided" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_key_length [label="ValueError:\nInvalid key length\n(must be 32 bytes)" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_no_token [label="ValueError:\nShared token not provided" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_token_format [label="ValueError:\nInvalid token format\n(must be 'word-word')" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_no_private [label="CryptographicError:\nPrivate key not generated" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_key_load [label="CryptographicError:\nInvalid peer public key" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_ecdh [label="CryptographicError:\nECDH exchange failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_hkdf [label="CryptographicError:\nKey derivation failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_cipher [label="CryptographicError:\nCipher initialization failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    raise_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> check_peer_key;
    check_peer_key -> validate_key_len [label="Yes" color="green"];
    validate_key_len -> check_token [label="Yes" color="green"];
    check_token -> validate_token [label="Yes" color="green"];
    validate_token -> check_private_key [label="Yes" color="green"];
    check_private_key -> load_peer_key [label="Yes" color="green"];
    load_peer_key -> perform_ecdh;
    perform_ecdh -> prep_hkdf;
    prep_hkdf -> derive_key;
    derive_key -> init_cipher;
    init_cipher -> store_cipher;
    store_cipher -> end_success;
    
    // Error flows
    check_peer_key -> error_no_peer_key [label="No" color="red" style=dashed];
    validate_key_len -> error_key_length [label="No" color="red" style=dashed];
    check_token -> error_no_token [label="No" color="red" style=dashed];
    validate_token -> error_token_format [label="No" color="red" style=dashed];
    check_private_key -> error_no_private [label="No" color="red" style=dashed];
    load_peer_key -> error_key_load [color="red" style=dashed];
    perform_ecdh -> error_ecdh [color="red" style=dashed];
    derive_key -> error_hkdf [color="red" style=dashed];
    init_cipher -> error_cipher [color="red" style=dashed];
    
    error_no_peer_key -> raise_error;
    error_key_length -> raise_error;
    error_no_token -> raise_error;
    error_token_format -> raise_error;
    error_no_private -> raise_error;
    error_key_load -> raise_error;
    error_ecdh -> raise_error;
    error_hkdf -> raise_error;
    error_cipher -> raise_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Perfect Forward Secrecy**
- **Ephemeral Key Exchange**: X25519 private keys generated fresh for each session protect past communications if current keys compromised
- **No Key Persistence**: Private keys exist only in memory during active session and are destroyed after completion
- **Computational Security**: X25519 provides ~128-bit security against quantum computers and ~256-bit against classical
- **Session Isolation**: Each session uses independent key material, preventing cross-session attacks

### **Mutual Authentication**
- **Token Integration**: Shared authentication token mixed into HKDF salt ensures both parties possess same pre-shared secret
- **MITM Prevention**: Attacker cannot derive correct session key without knowing both ephemeral private key and authentication token
- **Out-of-Band Verification**: Two-word tokens enable human verification of connection authenticity
- **Token Binding**: HKDF cryptographically binds token to session key, preventing token substitution

### **Key Derivation Security**
- **HKDF-SHA256 Standard**: Uses RFC 5869 compliant key derivation with SHA-256 for proven security properties
- **Salt Usage**: Authentication token as salt prevents rainbow table attacks on shared secrets
- **Info Parameter**: Context string "session" ensures domain separation from other potential key uses
- **Key Length**: Derives full 256-bit keys to match ChaCha20Poly1305 security requirements

### **Cryptographic Strength**
- **Algorithm Selection**: X25519 provides state-of-the-art elliptic curve security with constant-time implementation
- **Key Size**: 32-byte keys provide adequate security margin against future cryptographic advances
- **Side-Channel Resistance**: X25519 and ChaCha20Poly1305 designed to resist timing and cache-timing attacks
- **Quantum Resistance**: While not quantum-resistant, provides maximum practical security with current technology

### **Input Validation Security**
- **Key Length Verification**: Enforces exactly 32-byte peer public keys to prevent malformed input exploitation
- **Token Format Validation**: Validates "word-word" format to ensure predictable input processing
- **Type Safety**: Enforces bytes input for keys and string input for tokens to prevent encoding attacks
- **Null Input Rejection**: Rejects empty or None inputs that could cause undefined behavior

### **Memory Security**
- **Ephemeral Secret Storage**: ECDH shared secret exists only during key derivation operation
- **Secure Cleanup**: Sensitive intermediate values should be cleared from memory when possible
- **Limited Exposure Time**: Minimizes time window where raw shared secrets exist in memory
- **Process Isolation**: Keys exist only in current process memory, not persistent storage

### **Error Handling Security**  
- **Fail-Safe Design**: Any error condition results in complete session establishment failure
- **Information Leakage Prevention**: Error messages don't reveal details about key exchange state or token values
- **Exception Safety**: No partial session state established on failure
- **Consistent Failure**: All error conditions result in same exception type for uniform handling

### **Attack Mitigation**
- **Chosen Key Attacks**: HKDF design prevents chosen key attacks on derived session keys
- **Replay Protection**: Ephemeral keys ensure each session uses unique key material
- **Key Recovery Attacks**: X25519 structure prevents practical private key recovery from public keys
- **Compromise Resistance**: Session key compromise doesn't affect other sessions due to perfect forward secrecy

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>