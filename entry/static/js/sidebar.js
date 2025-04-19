document.addEventListener('DOMContentLoaded', (event) => {
    const headerToggle = document.getElementById('header-toggle');
    const navbar = document.getElementById('nav-bar');
    const mainContent = document.querySelector('.assyn');
    const header = document.getElementById('header');
    const sidebarStateKey = 'sidebarState';

    const applyState = (state) => {
        if (navbar && mainContent && header) {
            if (state === 'closed') {
                navbar.classList.add('collapsed');
                mainContent.classList.add('collapsed');
                mainContent.classList.remove('expanded');
                header.classList.add('collapsed');
                header.classList.remove('expanded');
            } else {
                navbar.classList.remove('collapsed');
                mainContent.classList.remove('collapsed');
                mainContent.classList.add('expanded');
                header.classList.remove('collapsed');
                header.classList.add('expanded');
            }
        }
    };

    const toggleSidebar = () => {
        if (navbar && mainContent && header) {
            navbar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
            mainContent.classList.toggle('collapsed');
            header.classList.toggle('expanded');
            header.classList.toggle('collapsed');

            const newState = navbar.classList.contains('collapsed') ? 'closed' : 'open';
            try {
                localStorage.setItem(sidebarStateKey, newState);
            } catch (e) {
                console.error('Failed to save sidebar state to localStorage', e);
            }
        }
    };

    let initialState = 'open';
    try {
        const savedState = localStorage.getItem(sidebarStateKey);
        if (savedState === 'closed') {
            initialState = 'closed';
        }
    } catch (e) {
        console.error('Failed to read sidebar state from localStorage', e);
    }
    applyState(initialState);


    if (headerToggle) {
        headerToggle.addEventListener('click', toggleSidebar);
    }
});
