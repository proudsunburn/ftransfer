---
layout: default
title: ftransfer docs
permalink: /
---

<script>
document.documentElement.style.setProperty('--bg-color', '#0d1117');
document.body.style.backgroundColor = '#0d1117';
document.body.style.color = '#f0f6fc';
</script>

<!-- Navigation Styling -->
<style>
.table-of-contents {
    max-width: 250px;
}

.nav-section {
    margin-bottom: 15px;
}

.nav-header {
    margin: 0 0 8px 0;
    padding: 4px 0;
    color: #f0f6fc;
    cursor: default;
}

.nav-header.expandable {
    cursor: pointer;
    position: relative;
    padding-right: 20px;
}

.nav-header.expandable:before {
    content: "▶";
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    font-size: 10px;
    transition: transform 0.2s;
}

.nav-header.expandable.expanded:before {
    transform: translateY(-50%) rotate(90deg);
}

.nav-items {
    list-style: none;
    margin: 0;
    padding: 0;
    margin-left: 15px;
}

.nav-items li {
    margin: 4px 0;
}

.nav-items a {
    display: block;
    padding: 3px 8px;
    color: #7d8590;
    text-decoration: none;
    font-size: 13px;
    border-radius: 4px;
    transition: all 0.2s;
}

.nav-items a:hover {
    color: #f0f6fc;
    background-color: #21262d;
}

.nav-items a.active {
    color: #58a6ff;
    background-color: #1f2937;
}

.class-link.expandable {
    position: relative;
    padding-right: 20px !important;
}

.class-link.expandable:after {
    content: "▶";
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 10px;
    transition: transform 0.2s;
}

.class-link.expandable.expanded:after {
    transform: translateY(-50%) rotate(90deg);
}

.method-nav {
    margin-left: 20px !important;
}

.method-nav a {
    font-size: 12px;
    color: #6e7681;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
}

.method-nav a:hover {
    color: #e6edf3;
    background-color: #1c2128;
}

.class-item {
    margin-bottom: 8px;
}

.architecture-diagram, .protocol-diagram, .security-diagram {
    text-align: center;
    margin: 20px 0;
    padding: 20px;
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
}

.protocol-diagram {
    background: #161b22;
}

.security-diagram {
    background: #0d1117;
    border-color: #30363d;
}

.components-table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    color: #e6edf3;
}

.components-table th {
    background: #21262d;
    padding: 12px;
    border: 1px solid #30363d;
    color: #f0f6fc;
    text-align: left;
}

.components-table td {
    padding: 10px;
    border: 1px solid #30363d;
}

.components-table tr:nth-child(even) {
    background: #161b22;
}
</style>

<!-- Main Content Area -->
<div class="spa-content">

<!-- Overview Section -->
<div id="overview" class="content-section active">
  <h1>Transfer Files System Overview</h1>

  <p>Secure file transfer program over Tailscale networks using end-to-end encryption with automatic key exchange and peer authentication.</p>
  
<h2>System Architecture</h2>

  <div class="architecture-diagram">
  
  {% graphviz %}
  digraph {
      rankdir=TB;
      bgcolor="transparent";
      edge [color="#6e7681" fontcolor="#f0f6fc"];
      
      // Main components
      sender [label="Sender\n(send_files)" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12];
      tailscale [label="Tailscale Network\n(Encrypted Tunnel)" shape=ellipse style=filled fillcolor="#56d364" fontcolor="white" fontsize=11];
      receiver [label="Receiver\n(receive_files)" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12];
      
      // Security layer
      crypto [label="X25519 + ChaCha20Poly1305\nEnd-to-End Encryption" shape=box style="filled,rounded" fillcolor="#f78166" fontcolor="white" fontsize=10];
      
      // Edges
      sender -> tailscale [label="Port 15820"];
      tailscale -> receiver [label="Encrypted Data"];
      sender -> crypto [style=dotted color="#f78166" fontcolor="#f0f6fc"];
      receiver -> crypto [style=dotted color="#f78166" fontcolor="#f0f6fc"];
  }
  {% endgraphviz %}
  
  </div>

<h2>Transfer Protocol Flow</h2>

<h3>Sender Workflow</h3>
  
  <div class="protocol-diagram">
  
  {% graphviz %}
  digraph {
      rankdir=LR;
      bgcolor="transparent";
      edge [color="#6e7681"];
      fontcolor="#f0f6fc";
      
      // Sender flow nodes
      main1 [label="main()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
      send [label="send_files()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=11];
      validate [label="validate_files()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=10];
      getip [label="get_tailscale_ip()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=10];
      token [label="generate_token()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=10];
      crypto1 [label="SecureCrypto()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=10];
      stream [label="Stream Files\n(1MB buffers)" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=10];
      
      // Flow
      main1 -> send -> validate -> getip -> token -> crypto1 -> stream;
      
      // Labels
      main1 [xlabel="Parse CLI"];
      validate [xlabel="Check files exist"];
      getip [xlabel="Get local IP"];
      token [xlabel="2-word auth"];
      crypto1 [xlabel="Key exchange"];
      stream [xlabel="Encrypt & send"];
  }
  {% endgraphviz %}
  
  </div>

<h3>Receiver Workflow</h3>
  
  <div class="protocol-diagram">
  
  {% graphviz %}
  digraph {
      rankdir=LR;
      bgcolor="transparent";
      edge [color="#6e7681"];
      fontcolor="#f0f6fc";
      
      // Receiver flow nodes
      main2 [label="main()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
      receive [label="receive_files()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=11];
      verify [label="verify_peer_ip_cached()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=10];
      crypto2 [label="SecureCrypto()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=10];
      recvall [label="recv_all()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=10];
      decrypt [label="decrypt()" shape=box style=filled fillcolor="#56d364" fontcolor="white" fontsize=10];
      
      // Flow
      main2 -> receive -> verify -> crypto2 -> recvall -> decrypt;
      
      // Labels
      main2 [xlabel="Parse connection"];
      verify [xlabel="Validate sender"];
      crypto2 [xlabel="Key exchange"];
      recvall [xlabel="Receive data"];
      decrypt [xlabel="Decrypt & save"];
  }
  {% endgraphviz %}
  
  </div>

<h2>Security Architecture</h2>

  <div class="security-diagram">
  
  {% graphviz %}
  digraph {
      rankdir=TB;
      bgcolor="transparent";
      edge [color="#6e7681"];
      
      // Security layers
      subgraph cluster_network {
          label="Network Security";
          style=filled;
          fillcolor="#1a1a1a";
          fontcolor="white";
          
          tailscale_net [label="Tailscale Peer Verification" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
          port [label="Fixed Port 15820" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
      }
      
      subgraph cluster_crypto {
          label="Cryptographic Security";
          style=filled;
          fillcolor="#2a1a1a";
          fontcolor="white";
          
          x25519 [label="X25519 ECDH\nKey Exchange" shape=box style=filled fillcolor="#58a6ff" fontcolor="white"];
          chacha20 [label="ChaCha20Poly1305\nAEAD Encryption" shape=box style=filled fillcolor="#58a6ff" fontcolor="white"];
          hkdf [label="HKDF-SHA256\nKey Derivation" shape=box style=filled fillcolor="#58a6ff" fontcolor="white"];
      }
      
      subgraph cluster_auth {
          label="Authentication";
          style=filled;
          fillcolor="#3a1a1a";
          fontcolor="white";
          
          tokens [label="2-Word Tokens\n34.6 bits entropy" shape=box style=filled fillcolor="#f78166" fontcolor="white"];
      }
      
      // Connections
      tailscale_net -> x25519;
      x25519 -> hkdf;
      hkdf -> chacha20;
      tokens -> x25519;
  }
  {% endgraphviz %}
  
  </div>

  <h2>Performance Features</h2>

  <ul>
    <li><strong>Unified Streaming Protocol</strong>: Single-pass I/O (read → hash → stream)</li>
    <li><strong>1MB Buffer Strategy</strong>: Memory-efficient for large files, 3-10x faster for many small files</li>
    <li><strong>Batch Metadata Transmission</strong>: Reduces network overhead for libraries/venvs</li>
    <li><strong>Connection Caching</strong>: 30-second TTL for peer verification</li>
    <li><strong>Perfect Forward Secrecy</strong>: Ephemeral X25519 keys protect past communications</li>
  </ul>

  <h2>Key Components</h2>

  <table class="components-table">
    <thead>
      <tr>
        <th>Component</th>
        <th>Purpose</th>
        <th>Security Level</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>TailscaleDetector</strong></td>
        <td>Network peer validation and IP discovery</td>
        <td>Safety-Critical</td>
      </tr>
      <tr>
        <td><strong>SecureCrypto</strong></td>
        <td>End-to-end encryption and key management</td>
        <td>Safety-Critical</td>
      </tr>
      <tr>
        <td><strong>SecureTokenGenerator</strong></td>
        <td>Human-readable authentication tokens</td>
        <td>Security-Critical</td>
      </tr>
      <tr>
        <td><strong>send_files() / receive_files()</strong></td>
        <td>Main transfer coordination</td>
        <td>Security-Critical</td>
      </tr>
      <tr>
        <td><strong>Utility Functions</strong></td>
        <td>File validation, speed calculation, etc.</td>
        <td>Reliability-Critical</td>
      </tr>
    </tbody>
  </table>

  ---
  
  *Use the navigation panel to explore detailed documentation for each component. All documentation includes formal specifications, call graphs, and security analysis.*
</div>

<!-- TailscaleDetector Section -->
<div id="tailscaledetector" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/tailscaledetector/">Loading TailscaleDetector documentation...</div>
</div>

<!-- SecureCrypto Section -->
<div id="securecrypto" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/securecrypto/">Loading SecureCrypto documentation...</div>
</div>


<!-- SecureTokenGenerator Section -->
<div id="securetokengenerator" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/securetokengenerator/">Loading SecureTokenGenerator documentation...</div>
</div>


<!-- send_files Section -->
<div id="send_files" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/send_files/">Loading send_files() documentation...</div>
</div>

<!-- receive_files Section -->
<div id="receive_files" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/receive_files/">Loading receive_files() documentation...</div>
</div>

<!-- main Section -->
<div id="main" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/main/">Loading main() documentation...</div>
</div>

<!-- recv_all Section -->
<div id="recv_all" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/recv_all/">Loading recv_all() documentation...</div>
</div>

<!-- validate_files Section -->
<div id="validate_files" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/validate_files/">Loading validate_files() documentation...</div>
</div>


<!-- format_speed Section -->
<div id="format_speed" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/format_speed/">Loading format_speed() documentation...</div>
</div>

<!-- calculate_speed Section -->
<div id="calculate_speed" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/calculate_speed/">Loading calculate_speed() documentation...</div>
</div>


<!-- collect_files_recursive Section -->
<div id="collect_files_recursive" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/collect_files_recursive/">Loading collect_files_recursive() documentation...</div>
</div>

<!-- Method-level sections -->

<!-- get_tailscale_ip Section -->
<div id="get_tailscale_ip" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/get_tailscale_ip/">Loading get_tailscale_ip() documentation...</div>
</div>

<!-- verify_peer_ip_cached Section -->
<div id="verify_peer_ip_cached" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/verify_peer_ip_cached/">Loading verify_peer_ip_cached() documentation...</div>
</div>


<!-- crypto_init Section -->
<div id="crypto_init" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/crypto_init/">Loading SecureCrypto.__init__() documentation...</div>
</div>

<!-- derive_session_key Section -->
<div id="derive_session_key" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/derive_session_key/">Loading derive_session_key() documentation...</div>
</div>

<!-- encrypt Section -->
<div id="encrypt" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/encrypt/">Loading encrypt() documentation...</div>
</div>

<!-- decrypt Section -->
<div id="decrypt" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/decrypt/">Loading decrypt() documentation...</div>
</div>

<!-- get_public_key_bytes Section -->
<div id="get_public_key_bytes" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/get_public_key_bytes/">Loading get_public_key_bytes() documentation...</div>
</div>


<!-- generate_token Section -->
<div id="generate_token" class="content-section">
  <div class="loading-placeholder" data-src="/ftransfer/generate_token/">Loading generate_token() documentation...</div>
</div>

</div>

<!-- SPA Navigation JavaScript -->
<script>
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, starting navigation transformation...');
    
    // Add delay to ensure all elements are rendered
    setTimeout(function() {
        // Create navigation container in header if it doesn't exist
        let tableOfContents = document.querySelector('.table-of-contents');
        if (!tableOfContents) {
            // Create navigation in sidebar or header area
            const header = document.querySelector('header');
            if (header) {
                const navContainer = document.createElement('div');
                navContainer.className = 'table-of-contents';
                navContainer.innerHTML = `
                    <div class="nav-section">
                        <h3 class="nav-header" data-target="overview">System Overview</h3>
                    </div>
                    
                    <div class="nav-section">
                        <h4 class="nav-header expandable" data-section="classes">Core Classes</h4>
                        <ul class="nav-items classes-nav" style="display: none;">
                            <li class="class-item">
                                <a href="#tailscaledetector" data-target="tailscaledetector" class="class-link expandable" data-section="tailscaledetector-methods">TailscaleDetector</a>
                                <ul class="nav-items method-nav tailscaledetector-methods-nav" style="display: none;">
                                    <li><a href="#get_tailscale_ip" data-target="get_tailscale_ip">get_tailscale_ip()</a></li>
                                    <li><a href="#verify_peer_ip_cached" data-target="verify_peer_ip_cached">verify_peer_ip_cached()</a></li>
                                </ul>
                            </li>
                            <li class="class-item">
                                <a href="#securecrypto" data-target="securecrypto" class="class-link expandable" data-section="securecrypto-methods">SecureCrypto</a>
                                <ul class="nav-items method-nav securecrypto-methods-nav" style="display: none;">
                                    <li><a href="#crypto_init" data-target="crypto_init">__init__()</a></li>
                                    <li><a href="#derive_session_key" data-target="derive_session_key">derive_session_key()</a></li>
                                    <li><a href="#encrypt" data-target="encrypt">encrypt()</a></li>
                                    <li><a href="#decrypt" data-target="decrypt">decrypt()</a></li>
                                    <li><a href="#get_public_key_bytes" data-target="get_public_key_bytes">get_public_key_bytes()</a></li>
                                </ul>
                            </li>
                            <li class="class-item">
                                <a href="#securetokengenerator" data-target="securetokengenerator" class="class-link expandable" data-section="securetokengenerator-methods">SecureTokenGenerator</a>
                                <ul class="nav-items method-nav securetokengenerator-methods-nav" style="display: none;">
                                    <li><a href="#generate_token" data-target="generate_token">generate_token()</a></li>
                                </ul>
                            </li>
                        </ul>
                    </div>
                    
                    <div class="nav-section">
                        <h4 class="nav-header expandable" data-section="functions">Main Functions</h4>
                        <ul class="nav-items functions-nav" style="display: none;">
                            <li><a href="#send_files" data-target="send_files">send_files()</a></li>
                            <li><a href="#receive_files" data-target="receive_files">receive_files()</a></li>
                            <li><a href="#main" data-target="main">main()</a></li>
                        </ul>
                    </div>
                    
                    <div class="nav-section">
                        <h4 class="nav-header expandable" data-section="utilities">Utility Functions</h4>
                        <ul class="nav-items utilities-nav" style="display: none;">
                            <li><a href="#recv_all" data-target="recv_all">recv_all()</a></li>
                            <li><a href="#validate_files" data-target="validate_files">validate_files()</a></li>
                            <li><a href="#format_speed" data-target="format_speed">format_speed()</a></li>
                            <li><a href="#calculate_speed" data-target="calculate_speed">calculate_speed()</a></li>
                            <li><a href="#collect_files_recursive" data-target="collect_files_recursive">collect_files_recursive()</a></li>
                        </ul>
                    </div>
                `;
                header.appendChild(navContainer);
            }
        }
        
        // Enhanced navigation with dynamic content loading
        function showSection(targetId) {
            console.log('Showing section:', targetId);
            
            // Hide all sections
            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Show target section
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.classList.add('active');
                
                // Check if this section needs dynamic loading
                const placeholder = targetSection.querySelector('.loading-placeholder');
                if (placeholder && !targetSection.dataset.loaded) {
                    loadExternalContent(targetSection, placeholder);
                }
            }
            
            // Update active navigation link
            document.querySelectorAll('[data-target]').forEach(link => {
                link.classList.remove('active');
            });
            const activeLink = document.querySelector(`[data-target="${targetId}"]`);
            if (activeLink) {
                activeLink.classList.add('active');
            }
            
            // Update URL history
            if (targetId !== 'overview') {
                history.pushState({section: targetId}, '', '#' + targetId);
            } else {
                history.pushState({section: 'overview'}, '', '/');
            }
        }
        
        // Dynamic content loading function
        async function loadExternalContent(section, placeholder) {
            const src = placeholder.dataset.src;
            if (!src) return;
            
            try {
                placeholder.textContent = 'Loading comprehensive documentation...';
                
                // Fetch the processed HTML content from Jekyll
                const response = await fetch(src);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const htmlContent = await response.text();
                
                // Parse HTML and extract the main content from Jekyll's section element  
                const parser = new DOMParser();
                const doc = parser.parseFromString(htmlContent, 'text/html');
                
                // Jekyll puts our markdown content inside <section> within the wrapper
                const sectionElement = doc.querySelector('section');
                if (sectionElement) {
                    // Extract everything after the dark mode script
                    let sectionHTML = sectionElement.innerHTML;
                    
                    // Remove the dark mode script at the beginning
                    sectionHTML = sectionHTML.replace(/<script>\s*document\.documentElement\.style\.setProperty.*?<\/script>\s*/gi, '');
                    
                    // Clean up any remaining script tags and navigation
                    sectionHTML = sectionHTML
                        .replace(/<script[\s\S]*?<\/script>/gi, '')
                        .replace(/<nav[\s\S]*?<\/nav>/gi, '')
                        .replace(/href="\/transferfiles\/assets\/js\/dark-mode\.js"/gi, '')
                        .trim();
                    
                    // Replace placeholder with the comprehensive content
                    section.innerHTML = sectionHTML;
                    section.dataset.loaded = 'true';
                    
                    console.log(`Successfully loaded comprehensive documentation for: ${src}`);
                } else {
                    throw new Error('Could not find section element in Jekyll HTML');
                }
            } catch (error) {
                console.error('Failed to load content:', error);
                placeholder.innerHTML = `
                    <div class="error-message">
                        <h3>⚠️ Content Loading Error</h3>
                        <p>Failed to load comprehensive documentation from <code>${src}</code></p>
                        <p class="error-details">${error.message}</p>
                    </div>
                `;
            }
        }
        
        // Enhanced navigation with expand/collapse functionality
        function expandParentSection(targetId) {
            const classItems = ['tailscaledetector', 'securecrypto', 'securetokengenerator'];
            const functionItems = ['send_files', 'receive_files', 'main'];
            const utilityItems = ['recv_all', 'validate_files', 'format_speed', 'calculate_speed', 'collect_files_recursive'];
            const tailscaleMethodItems = ['get_tailscale_ip', 'verify_peer_ip_cached'];
            const securecryptoMethodItems = ['crypto_init', 'derive_session_key', 'encrypt', 'decrypt', 'get_public_key_bytes'];
            const securetokengeneratorMethodItems = ['generate_token'];
            
            if (tailscaleMethodItems.includes(targetId)) {
                // Expand TailscaleDetector methods submenu
                const classesNav = document.querySelector('.classes-nav');
                if (classesNav) {
                    classesNav.style.display = 'block';
                    const header = document.querySelector('[data-section="classes"]');
                    if (header) header.classList.add('expanded');
                }
                
                const methodsNav = document.querySelector('.tailscaledetector-methods-nav');
                if (methodsNav) {
                    methodsNav.style.display = 'block';
                    const classLink = document.querySelector('[data-section="tailscaledetector-methods"]');
                    if (classLink) classLink.classList.add('expanded');
                }
            } else if (securecryptoMethodItems.includes(targetId)) {
                // Expand SecureCrypto methods submenu
                const classesNav = document.querySelector('.classes-nav');
                if (classesNav) {
                    classesNav.style.display = 'block';
                    const header = document.querySelector('[data-section="classes"]');
                    if (header) header.classList.add('expanded');
                }
                
                const methodsNav = document.querySelector('.securecrypto-methods-nav');
                if (methodsNav) {
                    methodsNav.style.display = 'block';
                    const classLink = document.querySelector('[data-section="securecrypto-methods"]');
                    if (classLink) classLink.classList.add('expanded');
                }
            } else if (securetokengeneratorMethodItems.includes(targetId)) {
                // Expand SecureTokenGenerator methods submenu
                const classesNav = document.querySelector('.classes-nav');
                if (classesNav) {
                    classesNav.style.display = 'block';
                    const header = document.querySelector('[data-section="classes"]');
                    if (header) header.classList.add('expanded');
                }
                
                const methodsNav = document.querySelector('.securetokengenerator-methods-nav');
                if (methodsNav) {
                    methodsNav.style.display = 'block';
                    const classLink = document.querySelector('[data-section="securetokengenerator-methods"]');
                    if (classLink) classLink.classList.add('expanded');
                }
            } else if (classItems.includes(targetId)) {
                const classesNav = document.querySelector('.classes-nav');
                if (classesNav) {
                    classesNav.style.display = 'block';
                    const header = document.querySelector('[data-section="classes"]');
                    if (header) header.classList.add('expanded');
                }
            } else if (functionItems.includes(targetId)) {
                const functionsNav = document.querySelector('.functions-nav');
                if (functionsNav) {
                    functionsNav.style.display = 'block';
                    const header = document.querySelector('[data-section="functions"]');
                    if (header) header.classList.add('expanded');
                }
            } else if (utilityItems.includes(targetId)) {
                const utilitiesNav = document.querySelector('.utilities-nav');
                if (utilitiesNav) {
                    utilitiesNav.style.display = 'block';
                    const header = document.querySelector('[data-section="utilities"]');
                    if (header) header.classList.add('expanded');
                }
            }
        }
        
        // Event delegation for navigation clicks
        document.body.addEventListener('click', function(e) {
            // Handle expandable class links FIRST (before generic data-target handler)
            if (e.target.matches('.class-link.expandable')) {
                console.log('Expandable class link clicked:', e.target);
                
                const section = e.target.getAttribute('data-section');
                const navItems = document.querySelector(`.${section}-nav`);
                
                // Determine click area - check if click was on the right side (arrow area)
                const rect = e.target.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const isArrowClick = clickX > (rect.width - 30); // Arrow is in last 30px
                
                console.log('Click position:', clickX, 'Element width:', rect.width, 'Arrow click:', isArrowClick);
                
                if (navItems) {
                    const isCurrentlyHidden = navItems.style.display === 'none' || navItems.style.display === '';
                    
                    // Always toggle submenu when clicking expandable link
                    if (isCurrentlyHidden) {
                        navItems.style.display = 'block';
                        e.target.classList.add('expanded');
                        console.log('Expanded submenu for:', section);
                    } else {
                        navItems.style.display = 'none';
                        e.target.classList.remove('expanded');
                        console.log('Collapsed submenu for:', section);
                    }
                }
                
                // Navigate to class page only if clicking on text area (not arrow)
                if (!isArrowClick) {
                    const targetId = e.target.getAttribute('data-target');
                    if (targetId) {
                        showSection(targetId);
                        expandParentSection(targetId);
                    }
                }
                
                // Prevent the generic data-target handler from running
                e.preventDefault();
                e.stopPropagation();
                return;
            }
            
            // Handle regular navigation expandable headers
            if (e.target.matches('.nav-header.expandable')) {
                const section = e.target.getAttribute('data-section');
                const navItems = document.querySelector(`.${section}-nav`);
                
                if (navItems) {
                    if (navItems.style.display === 'none' || navItems.style.display === '') {
                        navItems.style.display = 'block';
                        e.target.classList.add('expanded');
                    } else {
                        navItems.style.display = 'none';
                        e.target.classList.remove('expanded');
                    }
                }
                return;
            }
            
            // Handle regular navigation links (non-expandable)
            if (e.target.matches('[data-target]') && !e.target.matches('.class-link.expandable')) {
                e.preventDefault();
                const targetId = e.target.getAttribute('data-target');
                console.log('Regular navigation click:', targetId);
                showSection(targetId);
                expandParentSection(targetId);
                return;
            }
        });
        
        // Handle browser back/forward buttons
        window.addEventListener('popstate', function(e) {
            if (e.state && e.state.section) {
                showSection(e.state.section);
                expandParentSection(e.state.section);
            } else {
                showSection('overview');
            }
        });
        
        // Initialize based on hash
        const hash = window.location.hash.substring(1);
        if (hash) {
            showSection(hash);
            expandParentSection(hash);
        } else {
            showSection('overview');
        }
        
        console.log('SPA navigation initialized successfully');
    }, 100);
});
</script>

<script src="/assets/js/dark-mode.js"></script>