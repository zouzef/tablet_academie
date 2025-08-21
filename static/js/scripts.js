// Academy Tablet Application - Enhanced JavaScript

// Global variables
let professorMessages = [];
let currentMessageIndex = 0;
let animationIntervals = [];

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Main initialization function
function initializeApp() {
    updateDateTime();
    setInterval(updateDateTime, 1000); // Update every second

    // Initialize professor animation if on no-session page
    if (document.body.classList.contains('no-session-body')) {
        initializeProfessorAnimation();
        initializeFloatingElements();
    }

    // Initialize session progress animations
    initializeProgressBars();

    // Add touch-friendly interactions
    addTouchInteractions();

    // Initialize card animations
    initializeCardAnimations();

    // Initialize countdown timers
    initializeCountdowns();

    // Add parallax effects
    initializeParallaxEffects();
}

// Update current date and time with enhanced formatting
function updateDateTime() {
    const now = new Date();
    const timeElement = document.getElementById('current-time');
    const dateElement = document.getElementById('current-date');

    if (timeElement) {
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });

        // Add subtle animation to time changes
        if (timeElement.textContent !== timeString) {
            timeElement.style.transform = 'scale(1.05)';
            setTimeout(() => {
                timeElement.style.transform = 'scale(1)';
            }, 200);
        }

        timeElement.textContent = timeString;
    }

    if (dateElement) {
        const dateString = now.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        dateElement.textContent = dateString;
    }
}

// Enhanced professor animation system
function initializeProfessorAnimation() {
    const professorImg = document.getElementById('professor-img');
    const speechText = document.getElementById('speech-text');

    if (!professorImg || !speechText) return;

    // Enhanced message array with more variety
    professorMessages = [
        {
            text: "Welcome to the Academy Study Center!<br>Currently, there are no active study sessions.",
            emotion: "welcoming"
        },
        {
            text: "Feel free to schedule your next session<br>through the academy portal.",
            emotion: "helpful"
        },
        {
            text: "The study center will be available<br>for your next appointment.",
            emotion: "reassuring"
        },
        {
            text: "Don't forget to prepare your materials<br>for upcoming sessions!",
            emotion: "encouraging"
        },
        {
            text: "Contact our staff if you need<br>assistance with scheduling.",
            emotion: "supportive"
        },
        {
            text: "Remember to take breaks and stay hydrated<br>during your study sessions!",
            emotion: "caring"
        },
        {
            text: "The library resources are available<br>24/7 through our online portal.",
            emotion: "informative"
        }
    ];

    // Enhanced professor bounce animation with variety
    const bounceInterval = setInterval(() => {
        const bounceType = Math.random();

        if (bounceType < 0.3) {
            // Gentle bounce
            professorImg.style.transform = 'translateY(-8px) scale(1.02)';
            setTimeout(() => {
                professorImg.style.transform = 'translateY(0) scale(1)';
            }, 400);
        } else if (bounceType < 0.6) {
            // Side to side gentle sway
            professorImg.style.transform = 'translateX(-5px) rotate(-1deg)';
            setTimeout(() => {
                professorImg.style.transform = 'translateX(5px) rotate(1deg)';
                setTimeout(() => {
                    professorImg.style.transform = 'translateX(0) rotate(0deg)';
                }, 300);
            }, 300);
        } else {
            // Subtle scale pulse
            professorImg.style.transform = 'scale(1.05)';
            setTimeout(() => {
                professorImg.style.transform = 'scale(1)';
            }, 500);
        }
    }, 4000 + Math.random() * 2000); // Random interval between 4-6 seconds

    animationIntervals.push(bounceInterval);

    // Enhanced message rotation with typing effect
    const messageInterval = setInterval(() => {
        speechText.style.opacity = '0';
        speechText.style.transform = 'translateY(10px)';

        setTimeout(() => {
            currentMessageIndex = (currentMessageIndex + 1) % professorMessages.length;
            const currentMessage = professorMessages[currentMessageIndex];

            // Apply emotion-based styling
            speechText.className = `speech-text emotion-${currentMessage.emotion}`;

            // Typing effect
            typeMessage(speechText, currentMessage.text);

            speechText.style.opacity = '1';
            speechText.style.transform = 'translateY(0)';
        }, 300);
    }, 10000 + Math.random() * 5000); // Random interval between 10-15 seconds

    animationIntervals.push(messageInterval);
}

// Typing effect for professor messages
function typeMessage(element, message) {
    element.innerHTML = '';
    let i = 0;
    const speed = 50;

    function typeChar() {
        if (i < message.length) {
            if (message.substr(i, 4) === '<br>') {
                element.innerHTML += '<br>';
                i += 4;
            } else {
                element.innerHTML += message.charAt(i);
                i++;
            }
            setTimeout(typeChar, speed);
        }
    }

    typeChar();
}

// Initialize floating background elements
function initializeFloatingElements() {
    const body = document.body;

    // Create floating academic icons
    const icons = ['📚', '🎓', '📝', '🔬', '📊', '💡', '🏛️', '📖'];

    for (let i = 0; i < 8; i++) {
        const floatingIcon = document.createElement('div');
        floatingIcon.className = 'floating-icon';
        floatingIcon.textContent = icons[i];
        floatingIcon.style.cssText = `
            position: fixed;
            font-size: 2rem;
            opacity: 0.1;
            pointer-events: none;
            z-index: -1;
            left: ${Math.random() * 100}%;
            top: ${Math.random() * 100}%;
            animation: float ${15 + Math.random() * 10}s infinite linear;
        `;

        body.appendChild(floatingIcon);
    }

    // Add floating animation CSS
    const style = document.createElement('style');
    style.textContent += `
        @keyframes float {
            0% { transform: translateY(100vh) rotate(0deg); }
            100% { transform: translateY(-100px) rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}

// Enhanced progress bar animations with staggered loading
function initializeProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');

    progressBars.forEach((bar, index) => {
        const targetWidth = bar.style.width;
        bar.style.width = '0%';

        setTimeout(() => {
            bar.style.transition = 'width 2s cubic-bezier(0.4, 0, 0.2, 1)';
            bar.style.width = targetWidth;

            // Add pulse effect when complete
            setTimeout(() => {
                bar.style.boxShadow = '0 0 10px rgba(0, 180, 216, 0.5)';
                setTimeout(() => {
                    bar.style.boxShadow = 'none';
                }, 500);
            }, 2000);
        }, index * 300 + 500);
    });
}

// Enhanced touch interactions with haptic-like feedback
function addTouchInteractions() {
    // Enhanced card interactions
    const cards = document.querySelectorAll('.session-card, .info-card');

    cards.forEach(card => {
        let touchStartTime;

        card.addEventListener('touchstart', function(e) {
            touchStartTime = Date.now();
            this.style.transform = 'scale(0.98)';
            this.style.transition = 'transform 0.1s ease-out';

            // Add ripple effect
            createRippleEffect(e, this);
        });

        card.addEventListener('touchend', function() {
            const touchDuration = Date.now() - touchStartTime;

            this.style.transform = 'scale(1)';
            this.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';

            // Long press effect
            if (touchDuration > 500) {
                this.style.boxShadow = '0 8px 25px rgba(0, 61, 167, 0.3)';
                setTimeout(() => {
                    this.style.boxShadow = '';
                }, 1000);
            }
        });

        // Enhanced hover effects for desktop
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
            this.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Enhanced button interactions
    const buttons = document.querySelectorAll('.btn');

    buttons.forEach(button => {
        button.addEventListener('touchstart', function(e) {
            this.style.transform = 'scale(0.95)';
            createRippleEffect(e, this);
        });

        button.addEventListener('touchend', function() {
            this.style.transform = 'scale(1)';
        });

        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.05)';
        });

        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// Create ripple effect for touch interactions
function createRippleEffect(event, element) {
    const ripple = document.createElement('div');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = (event.touches ? event.touches[0].clientX : event.clientX) - rect.left - size / 2;
    const y = (event.touches ? event.touches[0].clientY : event.clientY) - rect.top - size / 2;

    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(0, 180, 216, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
        z-index: 1000;
    `;

    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);

    setTimeout(() => {
        ripple.remove();
    }, 600);

    // Add ripple animation if not exists
    if (!document.querySelector('#ripple-style')) {
        const style = document.createElement('style');
        style.id = 'ripple-style';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize card entrance animations
function initializeCardAnimations() {
    const cards = document.querySelectorAll('.session-card, .info-card');

    // Intersection Observer for scroll-triggered animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = `opacity 0.6s ease-out ${index * 0.1}s, transform 0.6s ease-out ${index * 0.1}s`;

        observer.observe(card);
    });
}

// Initialize countdown timers with real-time updates
function initializeCountdowns() {
    const countdownElements = document.querySelectorAll('.countdown-time');

    countdownElements.forEach(element => {
        const originalText = element.textContent;

        // Simulate countdown (in real app, this would be calculated from actual session times)
        let minutes = parseInt(originalText.match(/\d+/)[0]);

        const countdownInterval = setInterval(() => {
            if (minutes > 0) {
                minutes--;
                element.textContent = `${minutes} minute${minutes !== 1 ? 's' : ''}`;

                // Add urgency styling as time decreases
                if (minutes <= 5) {
                    element.style.color = '#FF6B6B';
                    element.style.fontWeight = '700';
                    element.parentElement.style.background = 'rgba(255, 107, 107, 0.1)';
                }

                if (minutes <= 1) {
                    element.style.animation = 'pulse 1s infinite';
                }
            } else {
                element.textContent = 'Starting now!';
                element.style.color = '#28A745';
                clearInterval(countdownInterval);
            }
        }, 60000); // Update every minute

        animationIntervals.push(countdownInterval);
    });
}

// Initialize parallax effects for enhanced depth
function initializeParallaxEffects() {
    let ticking = false;

    function updateParallax() {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.professor-image, .room-status-banner');

        parallaxElements.forEach((element, index) => {
            const speed = 0.5 + (index * 0.1);
            const yPos = -(scrolled * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });

        ticking = false;
    }

    function requestTick() {
        if (!ticking) {
            requestAnimationFrame(updateParallax);
            ticking = true;
        }
    }

    window.addEventListener('scroll', requestTick);
}

// Enhanced refresh page function with loading states
function refreshPage() {
    const button = event.target;
    const originalText = button.innerHTML;

    // Enhanced loading animation
    button.innerHTML = '<i class="bi bi-arrow-clockwise me-2 spin"></i>Checking for updates...';
    button.disabled = true;
    button.style.background = 'linear-gradient(135deg, #6c757d 0%, #495057 100%)';

    // Add progress bar to button
    const progressBar = document.createElement('div');
    progressBar.style.cssText = `
        position: absolute;
        bottom: 0;
        left: 0;
        height: 3px;
        background: #00B4D8;
        width: 0%;
        transition: width 2s ease-in-out;
    `;
    button.style.position = 'relative';
    button.appendChild(progressBar);

    // Animate progress bar
    setTimeout(() => {
        progressBar.style.width = '100%';
    }, 100);

    // Simulate checking for updates with realistic timing
    setTimeout(() => {
        button.innerHTML = '<i class="bi bi-check-circle me-2"></i>Updated!';
        button.style.background = 'linear-gradient(135deg, #28A745 0%, #20C997 100%)';

        setTimeout(() => {
            location.reload();
        }, 1000);
    }, 2500);
}

// Enhanced view schedule function
function viewSchedule() {
    // Create modal-like overlay for schedule preview
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        opacity: 0;
        transition: opacity 0.3s ease-in-out;
    `;

    const modal = document.createElement('div');
    modal.style.cssText = `
        background: white;
        padding: 2rem;
        border-radius: 12px;
        max-width: 500px;
        width: 90%;
        text-align: center;
        transform: scale(0.8);
        transition: transform 0.3s ease-in-out;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    `;

    modal.innerHTML = `
        <h3 style="color: #003DA7; margin-bottom: 1rem;">
            <i class="bi bi-calendar3 me-2"></i>
            Weekly Schedule Preview
        </h3>
        <p style="margin-bottom: 1.5rem; color: #343A40;">
            In a full application, this would display the complete weekly schedule with all sessions, room assignments, and availability.
        </p>
        <button class="btn btn-primary" onclick="this.parentElement.parentElement.remove()">
            <i class="bi bi-x-circle me-2"></i>
            Close
        </button>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    // Animate in
    setTimeout(() => {
        overlay.style.opacity = '1';
        modal.style.transform = 'scale(1)';
    }, 10);

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.style.opacity = '0';
            modal.style.transform = 'scale(0.8)';
            setTimeout(() => overlay.remove(), 300);
        }
    });
}

// Enhanced session update simulation with smooth transitions
function simulateSessionUpdate() {
    const hasActiveSessions = Math.random() > 0.3;
    const currentPage = window.location.pathname;

    if (hasActiveSessions && currentPage.includes('no-session.html')) {
        // Smooth transition to active sessions
        document.body.style.opacity = '0';
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 500);
    } else if (!hasActiveSessions && currentPage.includes('index.html')) {
        // Smooth transition to no sessions
        document.body.style.opacity = '0';
        setTimeout(() => {
            window.location.href = 'no-session.html';
        }, 500);
    }
}

// Cleanup function for intervals when page unloads
window.addEventListener('beforeunload', () => {
    animationIntervals.forEach(interval => clearInterval(interval));
});

// Auto-refresh functionality with enhanced feedback
setInterval(() => {
    console.log('Checking for session updates...');

    // Add subtle visual indicator of background updates
    const header = document.querySelector('.academy-header');
    if (header) {
        header.style.boxShadow = '0 2px 4px rgba(0, 180, 216, 0.3)';
        setTimeout(() => {
            header.style.boxShadow = '';
        }, 1000);
    }

    // Uncomment for demo mode
    // simulateSessionUpdate();
}, 300000); // 5 minutes

// Add enhanced CSS animations
function addEnhancedAnimationClasses() {
    const style = document.createElement('style');
    style.textContent = `
        .spin {
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .pulse {
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .slide-in-left {
            animation: slideInLeft 0.6s ease-out;
        }

        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-30px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .bounce-in {
            animation: bounceIn 0.8s ease-out;
        }

        @keyframes bounceIn {
            0% { transform: scale(0.3); opacity: 0; }
            50% { transform: scale(1.05); }
            70% { transform: scale(0.9); }
            100% { transform: scale(1); opacity: 1; }
        }

        .emotion-welcoming { color: #003DA7; }
        .emotion-helpful { color: #0077B6; }
        .emotion-reassuring { color: #00B4D8; }
        .emotion-encouraging { color: #28A745; }
        .emotion-supportive { color: #6F42C1; }
        .emotion-caring { color: #E83E8C; }
        .emotion-informative { color: #FD7E14; }
    `;
    document.head.appendChild(style);
}

// Initialize enhanced animations
addEnhancedAnimationClasses();

