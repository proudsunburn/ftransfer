---
layout: default
title: SecureCrypto
permalink: /securecrypto/
---

<script>
document.documentElement.style.setProperty('--bg-color', '#0d1117');
document.body.style.backgroundColor = '#0d1117';
document.body.style.color = '#f0f6fc';
</script>

# SecureCrypto Class

End-to-end encryption using modern cryptography.

## Overview

Implements file transfer encryption using X25519 elliptic curve Diffie-Hellman key exchange and ChaCha20Poly1305 authenticated encryption. Provides comprehensive cryptographic protection for file transfers.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    securecrypto [label="SecureCrypto" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    x25519_generate [label="X25519PrivateKey.generate()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    chacha20_encrypt [label="ChaCha20Poly1305.encrypt()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    chacha20_decrypt [label="ChaCha20Poly1305.decrypt()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    hkdf_derive [label="HKDF.derive()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    os_urandom [label="os.urandom()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> securecrypto [color="#6e7681"];
    receive_files -> securecrypto [color="#6e7681"];
    securecrypto -> x25519_generate [color="#6e7681"];
    securecrypto -> chacha20_encrypt [color="#6e7681"];
    securecrypto -> chacha20_decrypt [color="#6e7681"];
    securecrypto -> hkdf_derive [color="#6e7681"];
    securecrypto -> os_urandom [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

| Method | Description |
|--------|-------------|
| `__init__()` | Initialize cryptographic key pair for session |
| `derive_session_key(peer_public_key_bytes, shared_secret)` | Derive session key using ECDH + HKDF |
| `encrypt(data, nonce)` | Encrypt data with ChaCha20Poly1305 |
| `decrypt(encrypted_data, nonce)` | Decrypt and authenticate ciphertext |
| `get_public_key_bytes()` | Get public key bytes for key exchange |

## Return Value

- **Type**: `SecureCrypto` instance
- **Description**: Initialized cryptographic context with ephemeral X25519 key pair

## Requirements

SecureCrypto class shall provide end-to-end encryption using X25519 key exchange when cryptographic operations are needed where the key exchange enables secure communication.

SecureCrypto class shall implement ChaCha20Poly1305 authenticated encryption when session keys are established where encryption provides confidentiality and integrity.

SecureCrypto class shall derive session keys using HKDF-SHA256 when shared secrets are computed where key derivation combines ECDH output with authentication tokens.

SecureCrypto class shall generate ephemeral key pairs when instances are created where ephemeral keys provide perfect forward secrecy.

SecureCrypto class shall maintain separate methods for encryption and decryption when cryptographic operations are performed where separation provides clear functional interfaces.

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>