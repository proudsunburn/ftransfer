---
layout: default
title: TailscaleDetector
permalink: /tailscaledetector/
---

<script>
document.documentElement.style.setProperty('--bg-color', '#0d1117');
document.body.style.backgroundColor = '#0d1117';
document.body.style.color = '#f0f6fc';
</script>

# TailscaleDetector Class

Network peer validation and Tailscale integration.

## Overview

Handles Tailscale network detection, IP address resolution, and peer verification. Provides caching mechanisms for performance optimization and security validation of network participants.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    tailscaledetector [label="TailscaleDetector" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    subprocess_run [label="subprocess.run()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    json_loads [label="json.loads()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    time_time [label="time.time()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> tailscaledetector [color="#6e7681"];
    receive_files -> tailscaledetector [color="#6e7681"];
    tailscaledetector -> subprocess_run [color="#6e7681"];
    tailscaledetector -> json_loads [color="#6e7681"];
    tailscaledetector -> time_time [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

| Method | Description |
|--------|-------------|
| `get_tailscale_ip()` | Get local Tailscale IP address |
| `verify_peer_ip_cached(ip)` | Cached peer validation with time-based cache |
| `verify_peer_ip(ip)` | Direct real-time peer validation |
| `get_tailscale_peers()` | Enumerate network peers |
| `is_tailscale_ip(ip)` | Validate IP is in Tailscale range |

## Return Value

- **Type**: `TailscaleDetector` instance
- **Description**: Network detector with peer validation capabilities

## Requirements

TailscaleDetector class shall provide network peer validation when peer verification is needed where validation ensures only authenticated peers can connect.

TailscaleDetector class shall cache peer information when validation is performed where caching improves performance by avoiding repeated CLI calls.

TailscaleDetector class shall detect local Tailscale IP address when network discovery is needed where detection enables connection endpoint determination.

TailscaleDetector class shall parse Tailscale CLI output when peer information is retrieved where parsing extracts IP addresses and hostnames.

TailscaleDetector class shall maintain cache freshness when peer data ages where freshness ensures accurate peer status information.

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>