document.addEventListener('DOMContentLoaded', function() {
  const sidebar = document.getElementById('nav-bar');
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const mainContent = document.querySelector('.main-content');

  // Check localStorage for sidebar state
  const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';

  // Set initial state
  if (isCollapsed) {
      sidebar.classList.add('collapsed');
      mainContent.classList.add('collapsed');
  }

  // Toggle sidebar
  sidebarToggle.addEventListener('click', function() {
      sidebar.classList.toggle('collapsed');
      mainContent.classList.toggle('collapsed');

      // Save state to localStorage
      localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
  });
});

