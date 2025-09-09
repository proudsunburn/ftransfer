---
layout: default
title: receive_files()
permalink: /receive_files/
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

# receive_files() Function

High-performance file reception client with streaming protocol and end-to-end decryption.

## Overview

Main client function that connects to sender, performs key exchange, and securely receives files using the optimized streaming protocol. Handles connection parsing, peer verification, and file reconstruction from streamed data with batch metadata processing.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    main [label="main()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    verify_peer_ip_cached [label="TailscaleDetector.verify_peer_ip_cached()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    crypto_init [label="SecureCrypto()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    recv_all [label="recv_all()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    calculate_speed [label="calculate_speed()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    format_speed [label="format_speed()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    main -> receive_files [color="#6e7681"];
    receive_files -> verify_peer_ip_cached [color="#6e7681"];
    receive_files -> crypto_init [color="#6e7681"];
    receive_files -> recv_all [color="#6e7681"];
    receive_files -> calculate_speed [color="#6e7681"];
    receive_files -> format_speed [color="#6e7681"];
}
{% endgraphviz %}

</div>

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_string` | `str` | Connection string in format "ip:token" |
| `pod` | `bool` | Accept connections from localhost for containerized environments (default: False) |
| `resume` | `bool` | Resume from existing .part files if available (default: False) |

## Return Value

- **Type**: `None`
- **Description**: Function completes file reception or raises exception on failure

## Requirements

receive_files() shall parse connection string to extract IP address and authentication token when connection_string parameter is provided where the format is "ip:token".

receive_files() shall establish TCP connection to sender on port 15820 when IP address is parsed where connection timeout is 30 seconds.

receive_files() shall verify sender IP using Tailscale peer verification when pod parameter is False where verification ensures sender is authenticated peer.

receive_files() shall perform key exchange with sender when TCP connection is established where the exchange uses X25519 ECDH with shared authentication token.

receive_files() shall decrypt all received data using ChaCha20Poly1305 when session key is derived where decryption ensures data confidentiality and integrity.

receive_files() shall receive files using streaming protocol with incremental saving when encrypted data is received where FileWriter instances handle direct stream-to-disk writing without memory accumulation.

receive_files() shall accept connections from localhost when pod parameter is True where localhost acceptance enables containerized deployment.

receive_files() shall resume from existing .part files when resume parameter is True where FileWriter instances verify existing data integrity before continuing transfers.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: receive_files(connection_string, pod)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Connection string parsing
    parse_conn [label="Parse connection string\n'ip:token' format" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    validate_format [label="Valid format?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    extract_ip [label="Extract IP address\nand authentication token" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    validate_ip [label="Valid IPv4?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Peer verification
    pod_check [label="pod == True?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    verify_peer [label="verify_peer_ip_cached(ip)\nValidate Tailscale peer" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    skip_verification [label="Skip peer verification\n(pod mode)" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    peer_valid [label="Peer authenticated?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Network connection
    connect_tcp [label="TCP connect to ip:15820\n(30 second timeout)" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    connection_ok [label="Connection successful?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Cryptographic handshake
    crypto_init [label="SecureCrypto()\nGenerate X25519 keypair" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    exchange_keys [label="Exchange public keys\nwith sender" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    derive_key [label="derive_session_key()\nECDH + HKDF-SHA256 + token" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    key_success [label="Key derivation successful?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // File reception with incremental saving
    receive_metadata [label="Receive batch metadata:\n{filename, size, hash, offset}" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    create_filewriters [label="Create FileWriter instances\nfor incremental saving" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    open_part_files [label="Open .part files\n(resume if --resume flag)" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    stream_loop [label="Stream chunks:\nrecv() → decrypt() → write_chunk()" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    complete_files [label="Complete files:\nmove .part to final names" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    verify_integrity [label="Verify SHA-256 hashes\nfor all received files" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    integrity_ok [label="All hashes valid?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Completion
    calc_speed [label="calculate_speed()\nCompute transfer rate" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    show_result [label="Display: 'Transfer complete!\nSaved: files'" shape=box style=filled fillcolor="#e91e63" fontcolor="white"];
    cleanup [label="Close connections\nCleanup resources" shape=box style=filled fillcolor="#9e9e9e" fontcolor="white"];
    end_success [label="Return (success)" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Error paths
    error_parse [label="ParseError:\nInvalid connection string" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_ip [label="ValueError:\nInvalid IP address" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_peer [label="AuthenticationError:\nPeer not verified" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_network [label="NetworkError:\nConnection failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_crypto [label="CryptographicError:\nKey exchange failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_integrity [label="IntegrityError:\nFile hash mismatch" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    end_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> parse_conn;
    parse_conn -> validate_format;
    validate_format -> extract_ip [label="Yes" color="green"];
    extract_ip -> validate_ip;
    validate_ip -> pod_check [label="Yes" color="green"];
    pod_check -> skip_verification [label="Yes" color="orange"];
    pod_check -> verify_peer [label="No" color="blue"];
    verify_peer -> peer_valid;
    peer_valid -> connect_tcp [label="Yes" color="green"];
    skip_verification -> connect_tcp;
    connect_tcp -> connection_ok;
    connection_ok -> crypto_init [label="Yes" color="green"];
    crypto_init -> exchange_keys;
    exchange_keys -> derive_key;
    derive_key -> key_success;
    key_success -> receive_metadata [label="Yes" color="green"];
    receive_metadata -> create_filewriters;
    create_filewriters -> open_part_files;
    open_part_files -> stream_loop;
    stream_loop -> complete_files;
    complete_files -> verify_integrity;
    verify_integrity -> integrity_ok;
    integrity_ok -> calc_speed [label="Yes" color="green"];
    calc_speed -> show_result;
    show_result -> cleanup;
    cleanup -> end_success;
    
    // Error flows
    validate_format -> error_parse [label="No" color="red" style=dashed];
    validate_ip -> error_ip [label="No" color="red" style=dashed];
    peer_valid -> error_peer [label="No" color="red" style=dashed];
    connection_ok -> error_network [label="No" color="red" style=dashed];
    key_success -> error_crypto [label="No" color="red" style=dashed];
    integrity_ok -> error_integrity [label="No" color="red" style=dashed];
    
    error_parse -> end_error;
    error_ip -> end_error;
    error_peer -> end_error;
    error_network -> end_error;
    error_crypto -> end_error;
    error_integrity -> end_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Connection Security**
- **Connection String Validation**: Strict parsing of "ip:token" format prevents injection attacks
- **IP Address Validation**: IPv4 format validation prevents malformed address exploitation
- **Connection Timeout**: 30-second timeout prevents hanging connections and resource exhaustion

### **Peer Authentication**
- **Tailscale Peer Verification**: Uses `verify_peer_ip_cached()` to ensure sender is authenticated Tailscale peer
- **Cached Verification**: 30-second cache prevents repeated CLI calls while maintaining security
- **Pod Mode Override**: Localhost-only mode for containerized deployments bypasses peer verification

### **Cryptographic Security**
- **Perfect Forward Secrecy**: Ephemeral X25519 keys generated per session protect past communications
- **Mutual Authentication**: ECDH key exchange with shared token prevents man-in-the-middle attacks
- **Session Key Derivation**: HKDF-SHA256 with token salt ensures both parties know the shared secret

### **File Reception Security**
- **Directory Traversal Prevention**: File paths validated before FileWriter creation to prevent escape attacks
- **Incremental File Writing**: FileWriter class manages .part files with atomic completion operations
- **Resume Verification**: Existing .part files re-hashed on resume to ensure integrity before continuation
- **Integrity Verification**: SHA-256 hash verification ensures files haven't been tampered with
- **Atomic File Operations**: Files written to .part locations then atomically renamed on completion

### **Data Protection**
- **Authenticated Decryption**: ChaCha20Poly1305 AEAD prevents accepting tampered data
- **Streaming Decryption**: Data decrypted in chunks and written directly to disk without memory accumulation
- **Memory Efficiency**: FileWriter approach eliminates large memory buffers, reducing attack surface
- **Secure Cleanup**: Connection resources and .part files properly cleaned up on failure

### **Error Handling Security**
- **Fail-Safe Design**: Any error condition results in complete operation failure
- **Information Disclosure Prevention**: Error messages don't reveal sensitive network or cryptographic details
- **Resource Cleanup**: Ensures connections and partial files cleaned up on failure

### **Network Security**
- **Port Consistency**: Fixed port 15820 provides predictable endpoint for firewall configuration
- **Connection Limits**: Single connection per session prevents resource exhaustion
- **Timeout Protection**: Network timeouts prevent indefinite blocking

### **FileWriter Security**
- **Incremental Hash Verification**: Continuous SHA-256 hashing during writing ensures data integrity
- **Resume Integrity**: Existing .part files re-hashed completely before resuming to detect tampering
- **Atomic Completion**: Files moved from .part to final names only after complete verification
- **Partial File Isolation**: Incomplete transfers isolated with .part extension to prevent confusion
- **Memory Attack Prevention**: Direct stream-to-disk writing eliminates large memory allocations

### **Attack Mitigation**
- **Replay Protection**: Ephemeral keys and session binding prevent replay attacks  
- **DoS Protection**: Connection timeouts and resource limits prevent denial of service
- **Data Validation**: All received data validated before processing or storage
- **Resume Attack Prevention**: .part files validated with hash verification before continuation
- **Side-Channel Resistance**: Cryptographic operations designed to resist timing attacks

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>