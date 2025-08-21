// Sidebar toggle for mobile

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    function openSidebar() {
        sidebar.classList.add('open');
        sidebarOverlay.style.display = 'block';
    }
    function closeSidebar() {
        sidebar.classList.remove('open');
        sidebarOverlay.style.display = 'none';
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            if (sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            closeSidebar();
        });
    }
    // Optional: close sidebar on resize to desktop
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });
});