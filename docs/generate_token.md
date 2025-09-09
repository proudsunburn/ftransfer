---
layout: default
title: generate_token()
permalink: /generate_token/
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

# SecureTokenGenerator.generate_token()

*Generate cryptographically secure two-word authentication tokens using enhanced entropy*

## Overview

Generates human-readable two-word authentication tokens using cryptographically secure random number generation enhanced with multiple entropy sources. Combines a curated vocabulary of 200+ memorable words with high-quality randomness to create tokens that are both secure and easy to communicate verbally or visually.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    generate_token [label="generate_token()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    secrets_choice [label="secrets.choice()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> generate_token [color="#6e7681"];
    generate_token -> secrets_choice [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

**None** - Static method that generates tokens independently using internal entropy collection.

## Return Value

- **Type**: `str`
- **Format**: `"word1-word2"` (hyphen-separated)
- **Length**: Variable (typically 10-20 characters)
- **Security**: ~34.6 bits of entropy (2^17.3 possible combinations)
- **Vocabulary**: Curated list of common, memorable English words

## Requirements

generate_token() shall return two-word authentication token when method is invoked where the token format is "word1-word2" with hyphen separator.

generate_token() shall use cryptographically secure random number generation when selecting words where randomness prevents token prediction.

generate_token() shall select words from curated vocabulary when generating tokens where vocabulary contains 200+ memorable English words.

generate_token() shall provide ~34.6 bits of entropy when token is generated where entropy level ensures adequate security for authentication.

generate_token() shall ensure tokens are human-readable when generated where tokens can be easily communicated verbally or visually.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: generate_token()" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Entropy collection
    collect_entropy [label="Collect entropy sources:\nOS random, timing, process state" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    init_rng [label="Initialize secrets.SystemRandom()\nCryptographically secure RNG" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    
    // Vocabulary validation
    check_vocabulary [label="Vocabulary loaded and valid?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_vocab_size [label="len(vocabulary) >= 200?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Token generation
    select_first_word [label="first_word = secrets.choice(vocabulary)\nSelect first word randomly" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    validate_first [label="Valid word selected?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    select_second_word [label="second_word = secrets.choice(vocabulary)\nSelect second word randomly" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    validate_second [label="Valid word selected?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Token formatting
    format_token [label="token = f'{first_word}-{second_word}'\nFormat with hyphen separator" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    validate_format [label="Valid token format?\n(word-word)" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Quality checks
    check_duplicates [label="Words are different?\n(avoid 'word-word')" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_length [label="Reasonable length?\n(5-30 characters)" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_chars [label="Valid characters only?\n(letters, hyphen)" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Success path
    return_token [label="return token\n(e.g., 'ocean-tiger')" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Error paths
    error_entropy [label="CryptographicError:\nEntropy collection failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_rng [label="CryptographicError:\nRNG initialization failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_no_vocab [label="ConfigurationError:\nVocabulary not available" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_small_vocab [label="SecurityError:\nVocabulary too small" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_first_word [label="CryptographicError:\nFirst word selection failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_second_word [label="CryptographicError:\nSecond word selection failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_format [label="FormatError:\nToken formatting failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_length [label="ValidationError:\nToken length invalid" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_chars [label="ValidationError:\nInvalid characters in token" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    retry_generation [label="Retry token generation\n(max 3 attempts)" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    raise_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> collect_entropy;
    collect_entropy -> init_rng;
    init_rng -> check_vocabulary;
    check_vocabulary -> validate_vocab_size [label="Yes" color="green"];
    validate_vocab_size -> select_first_word [label="Yes" color="green"];
    select_first_word -> validate_first;
    validate_first -> select_second_word [label="Yes" color="green"];
    select_second_word -> validate_second;
    validate_second -> format_token [label="Yes" color="green"];
    format_token -> validate_format;
    validate_format -> check_duplicates [label="Yes" color="green"];
    check_duplicates -> check_length [label="Yes" color="green"];
    check_length -> validate_chars [label="Yes" color="green"];
    validate_chars -> return_token [label="Yes" color="green"];
    
    // Error flows
    collect_entropy -> error_entropy [color="red" style=dashed];
    init_rng -> error_rng [color="red" style=dashed];
    check_vocabulary -> error_no_vocab [label="No" color="red" style=dashed];
    validate_vocab_size -> error_small_vocab [label="No" color="red" style=dashed];
    validate_first -> error_first_word [label="No" color="red" style=dashed];
    validate_second -> error_second_word [label="No" color="red" style=dashed];
    validate_format -> error_format [label="No" color="red" style=dashed];
    check_length -> error_length [label="No" color="red" style=dashed];
    validate_chars -> error_chars [label="No" color="red" style=dashed];
    
    // Retry logic
    check_duplicates -> retry_generation [label="No" color="orange"];
    retry_generation -> select_first_word [color="orange"];
    
    error_entropy -> raise_error;
    error_rng -> raise_error;
    error_no_vocab -> raise_error;
    error_small_vocab -> raise_error;
    error_first_word -> raise_error;
    error_second_word -> raise_error;
    error_format -> raise_error;
    error_length -> raise_error;
    error_chars -> raise_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Cryptographic Randomness**
- **High-Quality Entropy**: Uses `secrets.SystemRandom()` which derives from OS-level cryptographically secure random sources
- **Entropy Sources**: Combines multiple entropy sources including `/dev/urandom`, system timers, and process state
- **Uniform Distribution**: Each word selected with equal probability ensuring no statistical bias
- **Seed Independence**: Each token generation independent of previous generations

### **Security Strength Analysis**
- **Entropy Calculation**: ~34.6 bits of entropy from 200² = 40,000 possible combinations
- **Attack Resistance**: ~17,300 average guesses required for brute force attack
- **Time Complexity**: Adequate security for short-lived authentication sessions
- **Collision Probability**: Extremely low probability of generating identical tokens

### **Vocabulary Security**
- **Curated Word List**: Hand-selected common English words avoiding confusing or inappropriate terms
- **Pronunciation Clarity**: Words chosen for clear verbal communication to prevent miscommunication
- **Visual Distinction**: Words selected to be visually distinct when written to prevent transcription errors
- **Length Optimization**: Word lengths balanced between security and usability

### **Attack Vector Mitigation**
- **Dictionary Attacks**: Large vocabulary size makes dictionary attacks computationally expensive
- **Brute Force Resistance**: 34.6 bits provides adequate resistance for temporary authentication tokens
- **Social Engineering Resistance**: Human-readable format enables out-of-band verification
- **Timing Attacks**: Constant-time word selection prevents timing-based cryptanalysis

### **Token Format Security**
- **Standard Delimiter**: Hyphen separator provides clear word boundary without encoding issues
- **ASCII Compatibility**: All tokens use standard ASCII characters for maximum compatibility
- **Length Predictability**: Consistent format enables reliable parsing and validation
- **Case Sensitivity**: Consistent lowercase format prevents case-related authentication issues

### **Implementation Security**
- **Library Trust**: Relies on Python's `secrets` module which is designed for cryptographic use
- **Error Handling**: Comprehensive error checking prevents weak token generation
- **State Independence**: No persistent state between token generations
- **Memory Security**: Tokens exist only as needed, no persistent storage of generation state

### **Operational Security**
- **Session Scope**: Tokens designed for single-session use with limited lifetime
- **Out-of-Band Verification**: Human-readable format enables verbal/visual confirmation
- **Transport Security**: Safe to transmit over insecure channels as part of broader authentication protocol
- **Revocation Capability**: Tokens naturally expire with session termination

### **Communication Security**
- **Verbal Transmission**: Words selected for clear verbal communication over various channels
- **Visual Transmission**: Format optimized for clear written/displayed communication
- **Error Detection**: Distinct word selection reduces transcription and communication errors
- **International Compatibility**: English words provide broad international recognition

### **Entropy Quality Assurance**
- **Source Validation**: Validates that entropy sources are available and functioning
- **Generation Testing**: Internal validation ensures tokens meet format and quality requirements
- **Retry Logic**: Automatic retry on generation failures to ensure token quality
- **Statistical Properties**: Regular validation of token distribution properties during testing

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>