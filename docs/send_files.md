---
layout: default
title: send_files()
permalink: /send_files/
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

# send_files() Function

High-performance file transmission server with streaming protocol and end-to-end encryption.

## Overview

Main server function that handles file transmission using optimized streaming buffers. Sets up TCP server, performs key exchange, and securely transmits files using a unified streaming protocol optimized for maximum throughput, especially for many small files.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    main [label="main()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    send_files [label="send_files()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    validate_files [label="validate_files()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    collect_files_recursive [label="collect_files_recursive()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    get_tailscale_ip [label="TailscaleDetector.get_tailscale_ip()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    verify_peer_ip_cached [label="TailscaleDetector.verify_peer_ip_cached()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    generate_token [label="SecureTokenGenerator.generate_token()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    crypto_init [label="SecureCrypto()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    recv_all [label="recv_all()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    calculate_speed [label="calculate_speed()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    format_speed [label="format_speed()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
    
    // Edges
    main -> send_files [color="#6e7681"];
    send_files -> validate_files [color="#6e7681"];
    send_files -> collect_files_recursive [color="#6e7681"];
    send_files -> get_tailscale_ip [color="#6e7681"];
    send_files -> verify_peer_ip_cached [color="#6e7681"];
    send_files -> generate_token [color="#6e7681"];
    send_files -> crypto_init [color="#6e7681"];
    send_files -> recv_all [color="#6e7681"];
    send_files -> calculate_speed [color="#6e7681"];
    send_files -> format_speed [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_paths` | `List[str]` | List of file/directory paths to send |
| `pod` | `bool` | Bind to localhost for containerized environments (default: False) |

## Return Value

- **Type**: `None`
- **Description**: Function completes file transmission or raises exception on failure

## Requirements

send_files() shall establish TCP server on port 15820 when function is invoked with valid file paths where the server accepts connections from authenticated Tailscale peers.

send_files() shall validate all file paths before transmission when file_paths parameter is provided where validation ensures files exist and are accessible.

send_files() shall perform key exchange with connecting client when client connection is established where the exchange uses X25519 ECDH with shared authentication token.

send_files() shall encrypt all transmitted data using ChaCha20Poly1305 when session key is derived where encryption provides confidentiality and integrity.

send_files() shall prompt user to exclude virtual environment directories when venv patterns are detected where exclusion improves transfer efficiency by skipping cache directories.

send_files() shall prompt user to enable compression when preparing to transfer files where compression defaults to No and uses Blosc+LZ4 when enabled.

send_files() shall stream files using 1MB buffers when transmitting data where streaming optimizes performance for large files and many small files.

send_files() shall bind to localhost when pod parameter is True where localhost binding enables containerized deployment.

send_files() shall verify connecting peer IP using Tailscale peer verification when pod parameter is False where verification prevents unauthorized access.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: send_files(file_paths, pod)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Validation phase
    validate_input [label="validate_files(file_paths)" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    collect_files [label="collect_files_recursive()\nBuild file manifest" shape=box style=filled fillcolor="#56d364" fontcolor="white"];

    // User prompts
    venv_prompt [label="Prompt: Exclude venv dirs?\n[Y/n]" shape=box style=filled fillcolor="#e91e63" fontcolor="white"];
    compression_prompt [label="Prompt: Use compression?\n[y/N]" shape=box style=filled fillcolor="#e91e63" fontcolor="white"];

    // Network setup
    get_ip [label="get_tailscale_ip()\nGet local IP" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    bind_check [label="pod == True?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    bind_localhost [label="Bind to 127.0.0.1:15820" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    bind_tailscale [label="Bind to tailscale_ip:15820" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    
    // Authentication
    generate_auth [label="generate_token()\nCreate 2-word token" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    display_token [label="Display connection string:\n'transfer.py receive ip:token'" shape=box style=filled fillcolor="#e91e63" fontcolor="white"];
    
    // Connection waiting
    wait_conn [label="Accept TCP connection\n(5 minute timeout)" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    verify_peer [label="verify_peer_ip_cached()\nValidate client IP" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    
    // Cryptographic handshake
    crypto_init [label="SecureCrypto()\nGenerate X25519 keypair" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    exchange_keys [label="Exchange public keys\n(64 bytes total)" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    derive_key [label="derive_session_key()\nECDH + HKDF-SHA256" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    
    // File transmission
    send_metadata [label="Send batch metadata:\n{filename, size, hash}" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    stream_files [label="Stream files with 1MB buffers:\nread → hash → encrypt → send" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Completion
    calc_speed [label="calculate_speed()\nCompute transfer rate" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    show_result [label="Display: 'Transfer complete:\nX bytes sent'" shape=box style=filled fillcolor="#e91e63" fontcolor="white"];
    cleanup [label="Close connections\nCleanup resources" shape=box style=filled fillcolor="#9e9e9e" fontcolor="white"];
    end_success [label="Return (success)" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Error paths
    error_validation [label="Validation Error:\nFiles not found/accessible" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_network [label="Network Error:\nCannot bind/connect" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_auth [label="Authentication Error:\nPeer verification failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_crypto [label="Cryptographic Error:\nKey exchange failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    end_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> validate_input;
    validate_input -> collect_files;
    collect_files -> venv_prompt;
    venv_prompt -> compression_prompt;
    compression_prompt -> get_ip;
    get_ip -> bind_check;
    bind_check -> bind_localhost [label="Yes" color="green"];
    bind_check -> bind_tailscale [label="No" color="blue"];
    bind_localhost -> generate_auth;
    bind_tailscale -> generate_auth;
    generate_auth -> display_token;
    display_token -> wait_conn;
    wait_conn -> verify_peer;
    verify_peer -> crypto_init;
    crypto_init -> exchange_keys;
    exchange_keys -> derive_key;
    derive_key -> send_metadata;
    send_metadata -> stream_files;
    stream_files -> calc_speed;
    calc_speed -> show_result;
    show_result -> cleanup;
    cleanup -> end_success;
    
    // Error flows
    validate_input -> error_validation [color="red" style=dashed];
    get_ip -> error_network [color="red" style=dashed];
    bind_localhost -> error_network [color="red" style=dashed];
    bind_tailscale -> error_network [color="red" style=dashed];
    wait_conn -> error_network [color="red" style=dashed];
    verify_peer -> error_auth [color="red" style=dashed];
    exchange_keys -> error_crypto [color="red" style=dashed];
    derive_key -> error_crypto [color="red" style=dashed];
    
    error_validation -> end_error;
    error_network -> end_error;
    error_auth -> end_error;
    error_crypto -> end_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Network Security**
- **Peer Verification**: Uses `verify_peer_ip_cached()` to ensure only authenticated Tailscale peers can connect
- **Port Binding**: Fixed port 15820 provides consistent endpoint, pod mode allows containerized deployment
- **Connection Timeout**: 5-minute timeout prevents resource exhaustion from stalled connections

### **Cryptographic Security**
- **Perfect Forward Secrecy**: Ephemeral X25519 keys generated per session protect past communications if keys compromised
- **Authenticated Encryption**: ChaCha20Poly1305 AEAD prevents tampering and provides confidentiality
- **Key Exchange Security**: ECDH + HKDF-SHA256 with shared token ensures mutual authentication

### **Authentication Security**  
- **Two-Word Tokens**: 34.6 bits entropy (~200² combinations) provides adequate security for short-lived sessions
- **Token Integration**: Shared token mixed into HKDF salt prevents man-in-the-middle attacks
- **Visual Verification**: Human-readable tokens enable out-of-band verification

### **File System Security**
- **Path Validation**: `validate_files()` prevents path traversal attacks and validates file accessibility
- **Integrity Protection**: SHA-256 hashing during streaming enables end-to-end integrity verification
- **Access Control**: File permissions checked before transmission

### **Performance Security**
- **Memory Management**: 1MB streaming buffers prevent excessive memory usage with large files
- **Resource Limits**: Connection timeouts and buffer limits prevent DoS attacks
- **Streaming Protocol**: Single-pass I/O minimizes data exposure time in memory

### **Attack Mitigation**
- **Replay Protection**: Ephemeral keys and nonces prevent replay attacks
- **Timing Attack Resistance**: ChaCha20Poly1305 provides constant-time operations
- **Side-Channel Protection**: Secure key generation and handling procedures

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>