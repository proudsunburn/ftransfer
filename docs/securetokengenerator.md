---
layout: default
title: SecureTokenGenerator
permalink: /securetokengenerator/
---

<script>
document.documentElement.style.setProperty('--bg-color', '#0d1117');
document.body.style.backgroundColor = '#0d1117';
document.body.style.color = '#f0f6fc';
</script>

# SecureTokenGenerator Class

Generate secure two-word authentication tokens.

## Overview

Generates human-readable authentication tokens using a 200+ word vocabulary. Provides cryptographically secure token generation for transfer authentication while maintaining usability through memorable word pairs.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    token_generator [label="SecureTokenGenerator" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    entropy_collector [label="EntropyCollector.get_system_entropy()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    len_vocab [label="len(vocabulary)" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    int_from_bytes [label="int.from_bytes()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> token_generator [color="#6e7681"];
    token_generator -> entropy_collector [color="#6e7681"];
    token_generator -> len_vocab [color="#6e7681"];
    token_generator -> int_from_bytes [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

| Method | Description |
|--------|-------------|
| `generate_token()` | Generate secure two-word authentication token (static method) |

## Return Value

- **Type**: `SecureTokenGenerator` instance
- **Description**: Token generator with cryptographically secure random generation

## Requirements

SecureTokenGenerator class shall generate cryptographically secure authentication tokens when token generation is requested where tokens use two-word format.

SecureTokenGenerator class shall select words from curated vocabulary when generating tokens where vocabulary contains 200+ memorable English words.

SecureTokenGenerator class shall provide ~34.6 bits of entropy when tokens are generated where entropy level ensures adequate security for authentication.

SecureTokenGenerator class shall format tokens with hyphen separator when word selection completes where format is "word1-word2".

SecureTokenGenerator class shall ensure tokens are human-communicable when generated where tokens can be easily spoken or typed.

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>