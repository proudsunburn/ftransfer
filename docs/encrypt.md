---
layout: default
title: encrypt()
permalink: /encrypt/
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

# SecureCrypto.encrypt()

*ChaCha20Poly1305 authenticated encryption for secure data transmission*

## Overview

Provides authenticated encryption using the ChaCha20Poly1305 AEAD (Authenticated Encryption with Associated Data) algorithm. This method simultaneously encrypts data for confidentiality and generates an authentication tag to prevent tampering, providing both secrecy and integrity in a single operation.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    encrypt [label="encrypt()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    cipher_encrypt [label="cipher.encrypt()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    
    // Edges
    send_files -> encrypt [color="#6e7681"];
    encrypt -> cipher_encrypt [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

- **`data`** (bytes): Plaintext data to encrypt (any length from 0 to ~256 GB)
- **`nonce`** (bytes): 12-byte nonce that must be unique for each encryption with the same key

## Return Value

- **Type**: `bytes`
- **Content**: Encrypted ciphertext with integrated authentication tag
- **Size**: `len(data) + 16` bytes (16-byte authentication tag appended)

## Requirements

encrypt() shall return ciphertext with integrated authentication tag when provided with valid plaintext data and unique nonce where the authentication tag prevents tampering detection.

encrypt() shall use ChaCha20Poly1305 AEAD algorithm when session key has been established via derive_session_key() where the session key provides 256-bit security strength.

encrypt() shall generate unique 12-byte nonce when nonce parameter is not provided where uniqueness prevents cryptographic attacks.

encrypt() shall fail with authentication error when session key is not established where failure prevents insecure transmission.

encrypt() shall produce ciphertext of size len(data) + 16 bytes when encryption succeeds where the additional 16 bytes contain the authentication tag.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: encrypt(data, nonce)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Input validation
    check_data [label="data provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_session [label="Session key\nestablished?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_nonce [label="nonce provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Nonce handling
    gen_nonce [label="Generate 12-byte nonce\nos.urandom(12)" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    validate_nonce [label="Validate nonce length\n(must be 12 bytes)" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    
    // Encryption process
    prep_cipher [label="Prepare ChaCha20Poly1305\ncipher with session key" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    encrypt_data [label="cipher.encrypt(nonce, data)\nAEAD encryption" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    append_tag [label="Ciphertext includes:\ndata + 16-byte auth tag" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Success path
    return_result [label="Return ciphertext\n(len(data) + 16 bytes)" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Error paths
    error_no_data [label="ValueError:\nEmpty data not allowed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_no_session [label="CryptographicError:\nSession key not established" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_bad_nonce [label="ValueError:\nInvalid nonce length" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_encrypt [label="CryptographicError:\nEncryption failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    raise_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> check_data;
    check_data -> check_session [label="Yes" color="green"];
    check_session -> check_nonce [label="Yes" color="green"];
    check_nonce -> gen_nonce [label="No" color="orange"];
    check_nonce -> validate_nonce [label="Yes" color="blue"];
    gen_nonce -> prep_cipher;
    validate_nonce -> prep_cipher;
    prep_cipher -> encrypt_data;
    encrypt_data -> append_tag;
    append_tag -> return_result;
    
    // Error flows
    check_data -> error_no_data [label="No" color="red" style=dashed];
    check_session -> error_no_session [label="No" color="red" style=dashed];
    validate_nonce -> error_bad_nonce [color="red" style=dashed];
    encrypt_data -> error_encrypt [color="red" style=dashed];
    
    error_no_data -> raise_error;
    error_no_session -> raise_error;
    error_bad_nonce -> raise_error;
    error_encrypt -> raise_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Nonce Security**
- **Uniqueness Requirement**: Nonces must never be reused with the same session key to prevent catastrophic cryptographic failure
- **Random Generation**: Uses `os.urandom(12)` for cryptographically secure nonce generation when not provided
- **Length Validation**: Enforces exactly 12-byte nonces as required by ChaCha20Poly1305 specification

### **Key Management**
- **Session Key Dependency**: Requires pre-established session key from `derive_session_key()` using ECDH+HKDF
- **Key Isolation**: Session keys are ephemeral and never stored persistently
- **Perfect Forward Secrecy**: Compromised keys cannot decrypt past sessions due to ephemeral key generation

### **Authenticated Encryption (AEAD)**
- **Integrity Protection**: ChaCha20Poly1305 provides built-in authentication tag preventing tampering
- **Confidentiality**: Stream cipher provides strong confidentiality for data transmission
- **Tag Verification**: 16-byte authentication tag automatically appended and verified on decryption

### **Side-Channel Resistance**
- **Constant-Time Operations**: ChaCha20Poly1305 designed to resist timing attacks
- **Memory Security**: Plaintext data should be cleared after encryption when possible
- **Cache-Timing Protection**: Algorithm structure minimizes cache-timing vulnerabilities

### **Input Validation**
- **Data Size Limits**: Supports data up to ChaCha20Poly1305 limits (~256GB theoretical)
- **Empty Data Handling**: Prevents encryption of empty data which could leak information
- **Type Safety**: Enforces bytes input to prevent encoding issues

### **Error Handling Security**
- **Fail-Safe Design**: All error conditions result in immediate failure without partial encryption
- **Information Leakage Prevention**: Error messages don't reveal sensitive cryptographic state
- **Exception Safety**: Ensures no intermediate state corruption on encryption failure

### **Attack Mitigation**
- **Chosen Plaintext Attacks**: AEAD construction resists chosen plaintext attacks
- **Nonce Misuse Resistance**: While not nonce-misuse resistant, proper nonce generation prevents issues
- **Key Recovery Attacks**: ChaCha20 design prevents practical key recovery attacks

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>