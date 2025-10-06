// Theme Toggle System for ftransfer Documentation
// Supports both dark and light modes with theme persistence

class ThemeManager {
    constructor() {
        this.currentTheme = 'dark'; // default
        this.init();
    }

    init() {
        // Load saved theme or detect system preference
        this.loadTheme();
        
        // Apply theme immediately to prevent flash
        this.applyTheme(this.currentTheme, false);
        
        // Set up theme toggle functionality
        this.setupThemeToggle();
        
        // Initialize other features
        this.addCopyButtons();
        this.addSmoothScrolling();
        this.initializeMermaid();
        
        console.log(`Theme Manager initialized with ${this.currentTheme} theme`);
    }

    loadTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem('ftransfer-theme');
        if (savedTheme && (savedTheme === 'dark' || savedTheme === 'light')) {
            this.currentTheme = savedTheme;
            return;
        }

        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            this.currentTheme = 'light';
        } else {
            this.currentTheme = 'dark';
        }
    }

    applyTheme(theme, animate = true) {
        const html = document.documentElement;
        const body = document.body;
        
        // Add transition for smooth theme switching
        if (animate) {
            const elements = [html, body, ...document.querySelectorAll('section, .wrapper, .content-section')];
            elements.forEach(el => {
                if (el) el.style.transition = 'background-color 0.3s ease, color 0.3s ease';
            });
            
            // Remove transition after animation
            setTimeout(() => {
                elements.forEach(el => {
                    if (el) el.style.transition = '';
                });
            }, 300);
        }

        // Set theme attribute on document root
        if (theme === 'light') {
            html.setAttribute('data-theme', 'light');
        } else {
            html.setAttribute('data-theme', 'dark');
        }

        // Force apply theme colors to key elements (override Jekyll theme CSS)
        this.forceApplyThemeColors(theme);

        this.currentTheme = theme;
        this.updateToggleButton();
        
        // Save to localStorage
        localStorage.setItem('ftransfer-theme', theme);
        
        // Apply diagram filters if needed
        this.applyDiagramFilters(theme);
        
        // Apply theme to diagram containers (override hardcoded styles)
        this.applyDiagramContainerStyles(theme);
        
        // Apply theme to dynamically loaded content
        this.applyThemeToLoadedContent(theme);
    }

    applyThemeToLoadedContent(theme) {
        // Wait a bit for any dynamic content to load, then apply theme
        setTimeout(() => {
            this.forceApplyThemeColors(theme);
        }, 100);
    }

    forceApplyThemeColors(theme) {
        // Let CSS variables handle theming instead of JavaScript overrides
        // This function is now minimal since we removed Jekyll theme conflicts
        console.log(`Theme switched to: ${theme}`);
    }

    setupThemeToggle() {
        // Wait for navigation to be created
        setTimeout(() => {
            const toggleButton = document.getElementById('theme-toggle');
            if (toggleButton) {
                toggleButton.addEventListener('click', () => {
                    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
                    this.applyTheme(newTheme, true);
                });
                
                // Initialize button state
                this.updateToggleButton();
            }
        }, 200);
    }

    updateToggleButton() {
        const toggleButton = document.getElementById('theme-toggle');
        if (!toggleButton) return;

        const label = toggleButton.querySelector('.theme-label');
        const darkIcon = toggleButton.querySelector('.dark-icon');
        const lightIcon = toggleButton.querySelector('.light-icon');

        if (this.currentTheme === 'light') {
            if (label) label.textContent = 'Light Mode';
            if (darkIcon) darkIcon.style.opacity = '0.4';
            if (lightIcon) lightIcon.style.opacity = '1';
        } else {
            if (label) label.textContent = 'Dark Mode';
            if (darkIcon) darkIcon.style.opacity = '1';
            if (lightIcon) lightIcon.style.opacity = '0.4';
        }
    }

    applyDiagramFilters(theme) {
        // Apply CSS filters to ALL GraphViz diagrams for light mode
        // Universal selector catches diagrams in any container (.architecture-diagram, .butterfly-diagram, etc.)
        const diagrams = document.querySelectorAll('svg');
        
        diagrams.forEach(svg => {
            // Only apply filters to GraphViz-generated SVGs (they have specific structure/attributes)
            if (svg.querySelector('title') || svg.getAttribute('role') === 'img') {
                if (theme === 'light') {
                    // Gentler transformation for light mode - better readability for yellow elements
                    // Removed hue-rotate that was making colors confusing
                    // Increased brightness to compensate for inversion
                    svg.style.filter = 'invert(1) brightness(1.3) contrast(1.1)';
                    
                    // Override text colors for better readability after inversion
                    // This fixes text contrast on yellow->blue elements
                    const textElements = svg.querySelectorAll('text');
                    textElements.forEach(text => {
                        text.style.fill = 'white';
                        text.style.stroke = 'none';
                        // Add text shadow for better readability on light backgrounds
                        text.style.textShadow = '1px 1px 2px rgba(0,0,0,0.8)';
                    });
                } else {
                    // Reset filters and text styles for dark mode
                    svg.style.filter = '';
                    const textElements = svg.querySelectorAll('text');
                    textElements.forEach(text => {
                        text.style.fill = '';
                        text.style.stroke = '';
                        text.style.textShadow = '';
                    });
                }
            }
        });
    }

    applyDiagramContainerStyles(theme) {
        // Let CSS variables handle diagram container styling
        // CSS custom properties will automatically update based on data-theme attribute
        console.log(`Diagram containers will use CSS variables for ${theme} theme`);
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme, true);
    }

    // Initialize Mermaid with violet color scheme
    initializeMermaid() {
        if (typeof mermaid !== 'undefined') {
            const theme = this.currentTheme === 'light' ? 'default' : 'dark';
            mermaid.initialize({
                theme: theme,
                themeVariables: this.currentTheme === 'light' ? {
                    primaryColor: '#5865F2',
                    primaryTextColor: '#2e3338',
                    primaryBorderColor: '#d1d5db',
                    lineColor: '#6a6d75',
                    secondaryColor: '#f2f3f5',
                    tertiaryColor: '#ffffff',
                    background: '#ffffff',
                    mainBkg: '#5865F2',
                    secondBkg: '#4752C4'
                } : {
                    primaryColor: '#5865F2',
                    primaryTextColor: '#ffffff',
                    primaryBorderColor: '#40444b',
                    lineColor: '#72767d',
                    secondaryColor: '#2f3136',
                    tertiaryColor: '#36393f',
                    background: '#36393f',
                    mainBkg: '#5865F2',
                    secondBkg: '#4752C4'
                }
            });
        }
    }

    addCopyButtons() {
        const codeBlocks = document.querySelectorAll('pre code');
        
        codeBlocks.forEach((codeBlock) => {
            const button = document.createElement('button');
            button.className = 'copy-button';
            button.innerHTML = '📋 Copy';
            button.style.cssText = `
                position: absolute;
                top: 8px;
                right: 8px;
                background: var(--bg-tertiary);
                border: 1px solid var(--border-primary);
                color: var(--text-primary);
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
            `;
            
            button.addEventListener('mouseenter', () => {
                button.style.background = 'var(--violet-primary)';
                button.style.color = '#ffffff';
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.background = 'var(--bg-tertiary)';
                button.style.color = 'var(--text-primary)';
            });
            
            const pre = codeBlock.parentNode;
            pre.style.position = 'relative';
            pre.appendChild(button);
            
            button.addEventListener('click', () => {
                navigator.clipboard.writeText(codeBlock.textContent).then(() => {
                    button.innerHTML = '✅ Copied!';
                    setTimeout(() => {
                        button.innerHTML = '📋 Copy';
                    }, 2000);
                });
            });
        });
    }

    addSmoothScrolling() {
        const links = document.querySelectorAll('a[href^="#"]');
        
        links.forEach((link) => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                const targetId = link.getAttribute('href');
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
}

class LayoutResizer {
    /**
     * Handles resizable panel functionality for the documentation layout
     */
    constructor() {
        this.isDragging = false;
        this.startX = 0;
        this.startWidth = 270; // Default sidebar width
        this.minWidth = 200;   // Minimum sidebar width
        this.maxWidth = 600;   // Maximum sidebar width
        this.wrapper = null;
        this.divider = null;
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be fully loaded
        setTimeout(() => {
            this.wrapper = document.querySelector('.wrapper');
            this.divider = document.getElementById('resize-divider');
            
            if (this.divider && this.wrapper) {
                this.setupEventListeners();
                this.loadSavedLayout();
            }
        }, 100);
    }
    
    setupEventListeners() {
        // Mouse events for dragging
        this.divider.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Touch events for mobile (if needed)
        this.divider.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this));
        
        // Keyboard accessibility
        this.divider.addEventListener('keydown', this.handleKeyDown.bind(this));
        this.divider.setAttribute('tabindex', '0');
        this.divider.setAttribute('role', 'separator');
        this.divider.setAttribute('aria-orientation', 'vertical');
        this.divider.setAttribute('aria-label', 'Resize panels');
    }
    
    handleMouseDown(e) {
        e.preventDefault();
        this.startDrag(e.clientX);
    }
    
    handleTouchStart(e) {
        e.preventDefault();
        if (e.touches.length === 1) {
            this.startDrag(e.touches[0].clientX);
        }
    }
    
    startDrag(clientX) {
        this.isDragging = true;
        this.startX = clientX;
        this.startWidth = parseInt(getComputedStyle(this.wrapper).getPropertyValue('--sidebar-width') || '270');
        
        // Add visual feedback
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        this.divider.style.background = 'var(--violet-primary)';
    }
    
    handleMouseMove(e) {
        if (this.isDragging) {
            this.updateWidth(e.clientX);
        }
    }
    
    handleTouchMove(e) {
        if (this.isDragging && e.touches.length === 1) {
            e.preventDefault();
            this.updateWidth(e.touches[0].clientX);
        }
    }
    
    updateWidth(clientX) {
        const deltaX = clientX - this.startX;
        const newWidth = Math.max(this.minWidth, Math.min(this.maxWidth, this.startWidth + deltaX));
        
        // Update CSS custom property
        this.wrapper.style.setProperty('--sidebar-width', `${newWidth}px`);
    }
    
    handleMouseUp() {
        this.endDrag();
    }
    
    handleTouchEnd() {
        this.endDrag();
    }
    
    endDrag() {
        if (this.isDragging) {
            this.isDragging = false;
            
            // Remove visual feedback
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            this.divider.style.background = '';
            
            // Save the new layout
            this.saveLayout();
        }
    }
    
    handleKeyDown(e) {
        const step = 10; // 10px per keystroke
        let currentWidth = parseInt(getComputedStyle(this.wrapper).getPropertyValue('--sidebar-width') || '270');
        let newWidth = currentWidth;
        
        switch (e.key) {
            case 'ArrowLeft':
                newWidth = Math.max(this.minWidth, currentWidth - step);
                break;
            case 'ArrowRight':
                newWidth = Math.min(this.maxWidth, currentWidth + step);
                break;
            case 'Home':
                newWidth = this.minWidth;
                break;
            case 'End':
                newWidth = this.maxWidth;
                break;
            case 'Space':
            case 'Enter':
                newWidth = 270; // Reset to default
                break;
            default:
                return; // Don't prevent default for other keys
        }
        
        e.preventDefault();
        this.wrapper.style.setProperty('--sidebar-width', `${newWidth}px`);
        this.saveLayout();
    }
    
    saveLayout() {
        const sidebarWidth = getComputedStyle(this.wrapper).getPropertyValue('--sidebar-width');
        localStorage.setItem('ftransfer-sidebar-width', sidebarWidth);
    }
    
    loadSavedLayout() {
        const savedWidth = localStorage.getItem('ftransfer-sidebar-width');
        if (savedWidth && savedWidth !== 'undefined') {
            this.wrapper.style.setProperty('--sidebar-width', savedWidth);
        }
    }
    
    resetLayout() {
        this.wrapper.style.setProperty('--sidebar-width', '270px');
        localStorage.removeItem('ftransfer-sidebar-width');
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
    window.layoutResizer = new LayoutResizer();
});

// Listen for system theme changes
if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('ftransfer-theme')) {
            // Only auto-switch if user hasn't manually set a preference
            const newTheme = e.matches ? 'dark' : 'light';
            if (window.themeManager) {
                window.themeManager.applyTheme(newTheme, true);
            }
        }
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Alt + T to toggle theme
    if (e.altKey && e.key.toLowerCase() === 't') {
        e.preventDefault();
        if (window.themeManager) {
            window.themeManager.toggleTheme();
        }
    }
    
    // Alt + S to focus search (placeholder for future implementation)
    if (e.altKey && e.key.toLowerCase() === 's') {
        console.log('Search focus - not implemented yet');
    }
});