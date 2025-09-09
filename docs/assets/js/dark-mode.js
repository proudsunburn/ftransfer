// Dark Mode enhancements for Transfer Files API Docs


function getBasePath() {
  // Handle both local development and GitHub Pages paths
  const path = window.location.pathname;
  if (path.includes('/transferfiles/')) {
    return '/transferfiles/';
  }
  return '/';
}

document.addEventListener('DOMContentLoaded', function() {
  // Add dark mode class to body
  document.body.classList.add('dark-mode');
  
  // Initialize Mermaid with dark theme if present
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      theme: 'dark',
      themeVariables: {
        primaryColor: '#58a6ff',
        primaryTextColor: '#f0f6fc',
        primaryBorderColor: '#30363d',
        lineColor: '#8b949e',
        secondaryColor: '#21262d',
        tertiaryColor: '#161b22'
      }
    });
  }
  
  // Add copy buttons to code blocks
  addCopyButtons();
  
  // Add smooth scrolling for anchor links
  addSmoothScrolling();
  
  // Table of contents disabled - using SPA navigation instead
});

function addCopyButtons() {
  const codeBlocks = document.querySelectorAll('pre code');
  
  codeBlocks.forEach(function(codeBlock) {
    const button = document.createElement('button');
    button.className = 'copy-button';
    button.innerHTML = '📋 Copy';
    button.style.cssText = `
      position: absolute;
      top: 8px;
      right: 8px;
      background: #21262d;
      border: 1px solid #30363d;
      color: #f0f6fc;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      cursor: pointer;
    `;
    
    const pre = codeBlock.parentNode;
    pre.style.position = 'relative';
    pre.appendChild(button);
    
    button.addEventListener('click', function() {
      navigator.clipboard.writeText(codeBlock.textContent).then(function() {
        button.innerHTML = '✅ Copied!';
        setTimeout(function() {
          button.innerHTML = '📋 Copy';
        }, 2000);
      });
    });
  });
}

function addSmoothScrolling() {
  const links = document.querySelectorAll('a[href^="#"]');
  
  links.forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      
      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
}

function addTableOfContents() {
  const headers = document.querySelectorAll('h2, h3, h4');
  
  if (headers.length > 3) {
    const toc = document.createElement('div');
    toc.className = 'table-of-contents';
    toc.innerHTML = '<h3>📚 Table of Contents</h3>';
    
    const tocList = document.createElement('ul');
    tocList.style.cssText = `
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 6px;
      padding: 16px;
      margin: 20px 0;
      list-style: none;
    `;
    
    headers.forEach(function(header) {
      if (!header.id) {
        header.id = header.textContent.toLowerCase()
          .replace(/[^\w\s-]/g, '')
          .replace(/\s+/g, '-');
      }
      
      const tocItem = document.createElement('li');
      const tocLink = document.createElement('a');
      
      tocLink.href = '#' + header.id;
      tocLink.textContent = header.textContent;
      tocLink.style.cssText = `
        color: #58a6ff;
        text-decoration: none;
        padding: 2px 0;
        display: block;
        padding-left: ${(parseInt(header.tagName.slice(1)) - 2) * 20}px;
      `;
      
      tocItem.appendChild(tocLink);
      tocList.appendChild(tocItem);
    });
    
    toc.appendChild(tocList);
    
    // Insert TOC after first paragraph
    const firstParagraph = document.querySelector('.post-content p, .wrapper p');
    if (firstParagraph) {
      firstParagraph.parentNode.insertBefore(toc, firstParagraph.nextSibling);
    }
  }
}

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
  // Alt + D to toggle between light/dark (for future implementation)
  if (e.altKey && e.key === 'd') {
    console.log('Dark mode toggle - currently always dark');
  }
  
  // Alt + S to focus search (if search is added later)
  if (e.altKey && e.key === 's') {
    console.log('Search focus - not implemented yet');
  }
});