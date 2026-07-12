document.addEventListener('change', (event) => {
    const target = event.target;
    if (!(target instanceof HTMLSelectElement)) return;
    if (target.form && (target.name === 'theme' || target.name === 'language_code')) {
        if (target.name === 'theme') {
            window.localStorage.setItem('roster-hub-theme', target.value);
        }
    }
});
