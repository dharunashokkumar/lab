/**
 * Theme Management System
 * Handles dark/light/auto theme switching with system preference detection
 */

class ThemeManager {
    constructor() {
        this.THEME_KEY = 'selfmade_theme';
        this.VALID_THEMES = ['light', 'dark', 'auto'];
        this.init();
    }

    /**
     * Initialize theme system on page load
     */
    init() {
        const savedTheme = this.getThemePreference();
        this.applyTheme(savedTheme);
        this.setupSystemPreferenceListener();
        this.updateThemeToggleUI();
    }

    /**
     * Get saved theme preference from localStorage
     * @returns {string} Theme name (light|dark|auto)
     */
    getThemePreference() {
        const saved = localStorage.getItem(this.THEME_KEY);
        return this.VALID_THEMES.includes(saved) ? saved : 'auto';
    }

    /**
     * Save theme preference to localStorage
     * @param {string} theme - Theme name to save
     */
    saveThemePreference(theme) {
        if (this.VALID_THEMES.includes(theme)) {
            localStorage.setItem(this.THEME_KEY, theme);
        }
    }

    /**
     * Apply theme to the document
     * @param {string} theme - Theme name to apply
     */
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.saveThemePreference(theme);

        // Dispatch custom event for other components to react
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    /**
     * Get the effective theme (resolves 'auto' to light/dark)
     * @returns {string} Effective theme (light|dark)
     */
    getEffectiveTheme() {
        const preference = this.getThemePreference();

        if (preference === 'auto') {
            return this.getSystemPreference();
        }

        return preference;
    }

    /**
     * Get system color scheme preference
     * @returns {string} System preference (light|dark)
     */
    getSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    /**
     * Setup listener for system preference changes
     */
    setupSystemPreferenceListener() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

            // Modern browsers
            if (mediaQuery.addEventListener) {
                mediaQuery.addEventListener('change', (e) => {
                    const currentTheme = this.getThemePreference();
                    if (currentTheme === 'auto') {
                        // Re-apply auto theme to pick up system change
                        this.applyTheme('auto');
                    }
                });
            } else if (mediaQuery.addListener) {
                // Legacy browsers
                mediaQuery.addListener((e) => {
                    const currentTheme = this.getThemePreference();
                    if (currentTheme === 'auto') {
                        this.applyTheme('auto');
                    }
                });
            }
        }
    }

    /**
     * Toggle between light/dark/auto themes in sequence
     */
    toggleTheme() {
        const current = this.getThemePreference();
        const themeSequence = {
            'light': 'dark',
            'dark': 'auto',
            'auto': 'light'
        };

        const nextTheme = themeSequence[current] || 'auto';
        this.applyTheme(nextTheme);
        this.updateThemeToggleUI();

        return nextTheme;
    }

    /**
     * Set specific theme
     * @param {string} theme - Theme name (light|dark|auto)
     */
    setTheme(theme) {
        if (this.VALID_THEMES.includes(theme)) {
            this.applyTheme(theme);
            this.updateThemeToggleUI();
        }
    }

    /**
     * Update theme toggle button UI
     */
    updateThemeToggleUI() {
        const themeBtn = document.getElementById('themeToggle');
        if (!themeBtn) return;

        const current = this.getThemePreference();
        const iconMap = {
            'light': 'light_mode',
            'dark': 'dark_mode',
            'auto': 'brightness_auto'
        };

        const icon = themeBtn.querySelector('.material-icons-round');
        if (icon) {
            icon.textContent = iconMap[current] || 'brightness_6';
        }

        // Update title/tooltip
        const titleMap = {
            'light': 'Light theme',
            'dark': 'Dark theme',
            'auto': 'Auto theme (system)'
        };
        themeBtn.title = titleMap[current] || 'Toggle theme';
    }

    /**
     * Get theme icon for current theme
     * @returns {string} Material icon name
     */
    getCurrentThemeIcon() {
        const theme = this.getThemePreference();
        const iconMap = {
            'light': 'light_mode',
            'dark': 'dark_mode',
            'auto': 'brightness_auto'
        };
        return iconMap[theme] || 'brightness_6';
    }
}

// Initialize global theme manager
const themeManager = new ThemeManager();

// Expose toggle function globally for inline onclick handlers
function toggleTheme() {
    return themeManager.toggleTheme();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { themeManager, ThemeManager };
}
