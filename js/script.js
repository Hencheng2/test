// js/script.js

document.addEventListener('DOMContentLoaded', () => {
    // Mobile Menu Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.getElementById('navLinks');
    const header = document.getElementById('header');

    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            // Toggle icon between bars and times
            mobileMenuBtn.innerHTML = navLinks.classList.contains('active') ? 
                                     '<i class="fas fa-times"></i>' : 
                                     '<i class="fas fa-bars"></i>';
        });

        // Close mobile menu when clicking a nav link
        const navItems = navLinks.querySelectorAll('a');
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                if (navLinks.classList.contains('active')) {
                    navLinks.classList.remove('active');
                    mobileMenuBtn.innerHTML = '<i class="fas fa-bars"></i>';
                }
            });
        });
    }

    // Sticky Header
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 100) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }

    // Back to Top Button
    const backToTopBtn = document.getElementById('backToTop');
    if (backToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                backToTopBtn.style.display = 'flex';
            } else {
                backToTopBtn.style.display = 'none';
            }
        });
        
        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Custom Modal for Alerts (Instead of alert())
    function showModal(message) {
        const existingModal = document.getElementById('customAlertModal');
        if (existingModal) {
            existingModal.remove(); // Remove any existing modal to prevent duplicates
        }

        const modalHtml = `
            <div id="customAlertModal" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
            ">
                <div style="
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
                    text-align: center;
                    max-width: 400px;
                    width: 90%;
                    font-family: 'Poppins', sans-serif;
                ">
                    <p style="font-size: 1.1rem; margin-bottom: 20px;">${message}</p>
                    <button id="closeAlertModal" style="
                        background-color: var(--primary);
                        color: white;
                        border: none;
                        padding: 10px 25px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 1rem;
                        transition: background-color 0.3s ease;
                    ">
                        OK
                    </button>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        document.getElementById('closeAlertModal').addEventListener('click', () => {
            document.getElementById('customAlertModal').remove();
        });
    }

    // Form Submission (Contact Form)
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Get form values
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const subject = document.getElementById('subject').value;
            const message = document.getElementById('message').value;
            
            // Simple validation - Using a modal for alerts
            if (!name || !email || !subject || !message) {
                showModal('Please fill in all required fields.');
                return;
            }
            
            // Show success message - Using a modal for alerts
            showModal('Thank you for your message! We will get back to you soon.');
            contactForm.reset();
        });
    }
    
    // Newsletter Form Submission
    const newsletterForms = document.querySelectorAll('.newsletter-form');
    newsletterForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const emailInput = form.querySelector('input[type="email"]');
            
            if (emailInput && emailInput.value) {
                showModal('Thank you for subscribing to our newsletter!');
                emailInput.value = '';
            } else {
                showModal('Please enter a valid email address.');
            }
        });
    });

    // Live Chat Button (if exists)
    const liveChatBtn = document.getElementById('liveChatBtn');
    if (liveChatBtn) {
        liveChatBtn.addEventListener('click', function() {
            const now = new Date();
            const day = now.getDay();
            const hour = now.getHours();
            
            // Check if it's business hours (Mon-Fri 8-5)
            if (day >= 1 && day <= 5 && hour >= 8 && hour < 17) {
                showModal('Connecting you to our live chat support...');
            } else {
                showModal('Our live chat is currently offline. Please use WhatsApp for immediate assistance or email us and we\'ll respond within 24 hours.');
            }
        });
    }

    // WhatsApp click tracking (if needed)
    const whatsappLinks = document.querySelectorAll('a[href*="whatsapp"]');
    whatsappLinks.forEach(link => {
        link.addEventListener('click', function() {
            console.log('WhatsApp contact initiated');
        });
    });
    
    // Email click tracking (if needed)
    const emailLinks = document.querySelectorAll('a[href^="mailto:"]');
    emailLinks.forEach(link => {
        link.addEventListener('click', function() {
            console.log('Email contact initiated');
        });
    });
    
    // Phone click tracking (if needed)
    const phoneLinks = document.querySelectorAll('a[href^="tel:"]');
    phoneLinks.forEach(link => {
        link.addEventListener('click', function() {
            console.log('Phone contact initiated');
        });
    });
});
