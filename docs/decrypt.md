---
layout: default
title: decrypt()
permalink: /decrypt/
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

# SecureCrypto.decrypt()

*ChaCha20Poly1305 authenticated decryption with integrity verification*

## Overview

Performs authenticated decryption using ChaCha20Poly1305 AEAD, automatically verifying data integrity and authenticity before returning plaintext. This method provides the inverse operation of `encrypt()`, ensuring that only authentic, unmodified ciphertext can be successfully decrypted.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    decrypt [label="decrypt()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    cipher_decrypt [label="cipher.decrypt()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    
    // Edges
    receive_files -> decrypt [color="#6e7681"];
    decrypt -> cipher_decrypt [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

- **`ciphertext`** (bytes): Ciphertext with integrated authentication tag (minimum 16 bytes)
- **`nonce`** (bytes): 12-byte nonce that was used during encryption

## Return Value

- **Type**: `bytes`
- **Content**: Decrypted plaintext data
- **Size**: `len(encrypted_data) - 16` bytes (authentication tag removed)

## Requirements

decrypt() shall return plaintext data when provided with valid ciphertext and matching nonce where the ciphertext contains integrated authentication tag.

decrypt() shall verify authentication tag before returning plaintext when decryption is attempted where verification ensures data integrity and authenticity.

decrypt() shall use ChaCha20Poly1305 AEAD algorithm when session key has been established via derive_session_key() where the session key provides 256-bit security strength.

decrypt() shall fail with authentication error when ciphertext has been tampered with where failure prevents accepting corrupted data.

decrypt() shall produce plaintext of size len(ciphertext) - 16 bytes when decryption succeeds where the 16 bytes are the removed authentication tag.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: decrypt(ciphertext, nonce)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Input validation
    check_ciphertext [label="ciphertext provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_min_length [label="len(ciphertext) >= 16?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_session [label="Session key\nestablished?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_nonce [label="nonce valid?\n(12 bytes)" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Decryption process
    prep_cipher [label="Prepare ChaCha20Poly1305\ncipher with session key" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    extract_tag [label="Ciphertext contains:\ndata + 16-byte auth tag" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    decrypt_data [label="cipher.decrypt(nonce, ciphertext)\nAEAD decryption + verification" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    verify_auth [label="Automatic auth tag\nverification by AEAD" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Success path
    return_plaintext [label="Return plaintext\n(len(ciphertext) - 16 bytes)" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Error paths
    error_no_ciphertext [label="ValueError:\nNo ciphertext provided" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_too_short [label="ValueError:\nCiphertext too short\n(< 16 bytes)" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_no_session [label="CryptographicError:\nSession key not established" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_bad_nonce [label="ValueError:\nInvalid nonce length" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_auth_failed [label="AuthenticationError:\nAuthentication tag invalid\n(data tampered)" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_decrypt [label="CryptographicError:\nDecryption failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    raise_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> check_ciphertext;
    check_ciphertext -> check_min_length [label="Yes" color="green"];
    check_min_length -> check_session [label="Yes" color="green"];
    check_session -> check_nonce [label="Yes" color="green"];
    check_nonce -> prep_cipher [label="Yes" color="green"];
    prep_cipher -> extract_tag;
    extract_tag -> decrypt_data;
    decrypt_data -> verify_auth;
    verify_auth -> return_plaintext;
    
    // Error flows
    check_ciphertext -> error_no_ciphertext [label="No" color="red" style=dashed];
    check_min_length -> error_too_short [label="No" color="red" style=dashed];
    check_session -> error_no_session [label="No" color="red" style=dashed];
    check_nonce -> error_bad_nonce [label="No" color="red" style=dashed];
    decrypt_data -> error_auth_failed [label="Auth Fail" color="red" style=dashed];
    decrypt_data -> error_decrypt [label="Decrypt Fail" color="red" style=dashed];
    
    error_no_ciphertext -> raise_error;
    error_too_short -> raise_error;
    error_no_session -> raise_error;
    error_bad_nonce -> raise_error;
    error_auth_failed -> raise_error;
    error_decrypt -> raise_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Authentication Tag Verification**
- **Integrity Assurance**: ChaCha20Poly1305 automatically verifies 16-byte authentication tag before returning plaintext
- **Tamper Detection**: Any modification to ciphertext results in authentication failure and exception
- **All-or-Nothing**: Decryption fails completely if any bit of ciphertext or tag is altered

### **Key Management Security**
- **Session Key Dependency**: Requires same session key used for encryption, established via ECDH+HKDF
- **Key Isolation**: Session keys are ephemeral and never persist between sessions
- **Perfect Forward Secrecy**: Past sessions remain secure even if current keys are compromised

### **Nonce Handling**
- **Nonce Reuse Detection**: Same nonce used for encryption must be used for decryption
- **Length Validation**: Enforces exactly 12-byte nonces as required by ChaCha20Poly1305
- **Replay Protection**: Nonces are single-use within each session

### **Side-Channel Protection**
- **Constant-Time Verification**: Authentication tag verification resistant to timing attacks
- **Memory Security**: Ciphertext should be cleared after decryption when possible
- **Cache-Timing Resistance**: ChaCha20Poly1305 designed to minimize cache-timing leaks

### **Input Validation Security**
- **Minimum Length Check**: Rejects ciphertext shorter than 16 bytes (no room for auth tag)
- **Type Safety**: Enforces bytes input to prevent encoding-related vulnerabilities
- **Size Limits**: Supports decryption up to ChaCha20Poly1305 theoretical limits

### **Error Handling Security**
- **Fail-Safe Design**: All error conditions result in immediate failure with no partial decryption
- **Information Leakage Prevention**: Error messages don't reveal details about ciphertext or key state
- **Exception Safety**: No intermediate plaintext exposure on decryption failure

### **Attack Mitigation**
- **Chosen Ciphertext Attacks**: AEAD construction prevents chosen ciphertext attacks
- **Padding Oracle Attacks**: No padding means no padding oracle vulnerabilities
- **Key Recovery Attacks**: ChaCha20 structure prevents practical key recovery
- **Timing Attacks**: Constant-time operations prevent timing-based cryptanalysis

### **Data Integrity**
- **End-to-End Verification**: Combines with SHA-256 file hashing for complete integrity assurance
- **Atomic Operations**: Decryption is atomic - either completely succeeds or fails entirely
- **No Partial Results**: Never returns partial plaintext from corrupted ciphertext

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>