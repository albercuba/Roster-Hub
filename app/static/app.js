document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;

    document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
        const form = button.closest('form');
        const input = form?.querySelector('[data-theme-input]');
        const syncThemeToggle = () => {
            const currentTheme = root.dataset.theme === 'dark' ? 'dark' : 'light';
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            button.dataset.currentTheme = currentTheme;
            if (input instanceof HTMLInputElement) {
                input.value = nextTheme;
            }
        };

        syncThemeToggle();

        button.addEventListener('click', () => {
            const currentTheme = root.dataset.theme === 'dark' ? 'dark' : 'light';
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            window.localStorage.setItem('roster-hub-theme', nextTheme);
        });
    });
});
