---
layout: default
title: get_public_key_bytes()
permalink: /get_public_key_bytes/
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

# SecureCrypto.get_public_key_bytes()

*Extract X25519 public key for network transmission and key exchange*

## Overview

Extracts the X25519 public key as raw bytes suitable for network transmission during the key exchange phase. This method provides the public component of the ephemeral key pair that enables secure ECDH key agreement without exposing the private key material.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    get_public_key_bytes [label="get_public_key_bytes()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    public_bytes [label="public_key.public_bytes()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> get_public_key_bytes [color="#6e7681"];
    receive_files -> get_public_key_bytes [color="#6e7681"];
    get_public_key_bytes -> public_bytes [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

**None** - Method extracts the public key from the instance's key pair.

## Return Value

- **Type**: `bytes`
- **Size**: Exactly 32 bytes (256 bits)
- **Format**: Raw X25519 public key in standard encoding
- **Usage**: Safe for network transmission and public distribution

## Requirements

get_public_key_bytes() shall return 32-byte public key when method is invoked where the key is in standard X25519 encoding format.

get_public_key_bytes() shall extract public key from established key pair when key pair exists where the key pair was generated during initialization.

get_public_key_bytes() shall provide key suitable for network transmission when extraction completes where the key can be safely shared with peers.

get_public_key_bytes() shall maintain key pair security when public key is extracted where private key remains protected within the instance.

get_public_key_bytes() shall enable key exchange operations when public key is transmitted where the key enables ECDH shared secret computation.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: get_public_key_bytes()" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Validation checks
    check_keypair [label="Key pair initialized?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_public_key [label="self.public_key exists?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_key_type [label="Valid X25519 public key?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Key extraction
    extract_bytes [label="self.public_key.public_bytes(\n    encoding=Encoding.Raw,\n    format=PublicFormat.Raw\n)" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Format validation
    check_length [label="len(key_bytes) == 32?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_format [label="Valid X25519 format?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Security checks
    check_not_zero [label="key_bytes != b'\\x00' * 32?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_point [label="Valid curve point?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Success path
    return_bytes [label="return key_bytes\n(32-byte X25519 public key)" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Error paths
    error_no_keypair [label="CryptographicError:\nKey pair not initialized" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_no_public [label="CryptographicError:\nPublic key not available" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_invalid_type [label="CryptographicError:\nInvalid key type" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_extraction [label="CryptographicError:\nKey extraction failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_wrong_length [label="CryptographicError:\nInvalid key length" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_invalid_format [label="CryptographicError:\nInvalid key format" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_zero_key [label="CryptographicError:\nZero key detected" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_invalid_point [label="CryptographicError:\nInvalid curve point" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    raise_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> check_keypair;
    check_keypair -> check_public_key [label="Yes" color="green"];
    check_public_key -> validate_key_type [label="Yes" color="green"];
    validate_key_type -> extract_bytes [label="Yes" color="green"];
    extract_bytes -> check_length;
    check_length -> validate_format [label="Yes" color="green"];
    validate_format -> check_not_zero [label="Yes" color="green"];
    check_not_zero -> validate_point [label="Yes" color="green"];
    validate_point -> return_bytes [label="Yes" color="green"];
    
    // Error flows
    check_keypair -> error_no_keypair [label="No" color="red" style=dashed];
    check_public_key -> error_no_public [label="No" color="red" style=dashed];
    validate_key_type -> error_invalid_type [label="No" color="red" style=dashed];
    extract_bytes -> error_extraction [color="red" style=dashed];
    check_length -> error_wrong_length [label="No" color="red" style=dashed];
    validate_format -> error_invalid_format [label="No" color="red" style=dashed];
    check_not_zero -> error_zero_key [label="No" color="red" style=dashed];
    validate_point -> error_invalid_point [label="No" color="red" style=dashed];
    
    error_no_keypair -> raise_error;
    error_no_public -> raise_error;
    error_invalid_type -> raise_error;
    error_extraction -> raise_error;
    error_wrong_length -> raise_error;
    error_invalid_format -> raise_error;
    error_zero_key -> raise_error;
    error_invalid_point -> raise_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Public Key Safety**
- **Safe for Distribution**: Public keys are cryptographically safe to transmit over insecure channels
- **No Private Information**: Contains no information that can be used to derive the private key
- **Standard Encoding**: Uses RFC 7748 standard raw encoding for maximum interoperability
- **Network Transmission**: Safe for network transmission without additional encryption

### **Key Format Security**
- **Fixed Length**: Exactly 32 bytes prevents variable-length attacks and parsing ambiguities
- **Raw Encoding**: Direct binary representation avoids encoding/decoding vulnerabilities
- **Standard Format**: Uses established X25519 public key format with proven security properties
- **Byte Order**: Uses standard little-endian encoding as specified in RFC 7748

### **Cryptographic Integrity**
- **Valid Curve Point**: Ensures extracted key represents a valid point on the Curve25519 elliptic curve
- **Non-Zero Validation**: Rejects all-zero keys which would be cryptographically weak
- **Mathematical Validity**: Validates key meets X25519 mathematical requirements
- **Format Consistency**: Ensures key format matches expected X25519 public key structure

### **Key Pair Security**
- **Private Key Protection**: Public key extraction doesn't expose or compromise private key material
- **Instance Isolation**: Key extraction from one instance doesn't affect other instances
- **Memory Security**: Public key data is safe to exist in memory without special protection
- **No Side Effects**: Key extraction doesn't modify or affect the underlying key pair

### **Implementation Security**
- **Library Trust**: Relies on Python cryptography library's proven X25519 implementation
- **Error Handling**: Comprehensive error checking prevents malformed key extraction
- **State Validation**: Ensures cryptographic state is valid before key extraction
- **Exception Safety**: Proper exception handling prevents information leakage on errors

### **Network Protocol Security**
- **MITM Resistance**: Public key exchange combined with shared token prevents man-in-the-middle attacks
- **Authentication Integration**: Public key becomes part of authenticated key exchange protocol
- **Perfect Forward Secrecy**: Ephemeral public keys ensure session isolation
- **Replay Protection**: Each session uses unique ephemeral public keys

### **Attack Mitigation**
- **Key Substitution Attacks**: Shared token authentication prevents public key substitution
- **Invalid Key Attacks**: Validation ensures only valid curve points are returned
- **Weak Key Attacks**: Mathematical validation prevents weak or malformed keys
- **Implementation Attacks**: Uses constant-time library implementations to resist side-channel attacks

### **Operational Security**
- **No Persistent Storage**: Public keys exist only during active sessions
- **Memory Cleanup**: Public key data can be safely discarded after transmission
- **Process Isolation**: Keys exist only in current process memory space
- **Resource Management**: No special resource cleanup required for public key data

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>