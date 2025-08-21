document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const element = document.documentElement;
        
        if (element.requestFullscreen) {
            element.requestFullscreen().catch(err => {
                // Fail silently (no errors in console)
            });
        } else if (element.webkitRequestFullscreen) { // Safari
            element.webkitRequestFullscreen().catch(err => {});
        } else if (element.msRequestFullscreen) { // IE/Edge
            element.msRequestFullscreen().catch(err => {});
        }
    }, 300); // Short delay helps sometimes
});


// Try to trigger on any click/touch (higher chance of working)
document.body.addEventListener('click', () => {
    document.documentElement.requestFullscreen().catch(err => {});
}, { once: true }); // Only tries once