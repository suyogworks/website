// Main JavaScript file for Matrica Networks website

// Global app object for utility functions
window.app = {
    // API request utility
    async apiRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                method: options.method || 'GET',
                body: options.body,
                headers: options.headers || {}
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },
    
    // Format date utility
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },
    
    // Show alert utility
    showAlert(message, type = 'info') {
        alert(message); // Simple alert for now
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the website
    initializeWebsite();

    // Theme toggle
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    }
    const themeToggleBtn = document.querySelector('.theme-toggle');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }
});

function initializeWebsite() {
    // Add smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Add mobile menu toggle functionality
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');
        });
    }

    // Add form validation
    const contactForm = document.querySelector('#contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', handleContactForm);
    }

    // Load products if on products page
    if (document.getElementById('products-container')) {
        loadProducts();
    }

    // Load resources if on resources page
    if (document.getElementById('resources-container')) {
        loadResources();
    }

    // Load careers if on careers page
    if (document.getElementById('careers-container')) {
        loadCareers();
    }
}

async function loadCareers() {
    const container = document.getElementById('careers-container');
    if (!container) return;

    try {
        const response = await app.apiRequest('/cgi-bin/careers_api.py');
        if (response.success && response.data) {
            container.innerHTML = ''; // Clear loading message
            if (response.data.length === 0) {
                container.innerHTML = '<div class="card"><p>No open positions at the moment. Please check back later.</p></div>';
                return;
            }
            response.data.forEach(career => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <h3>${career.title}</h3>
                    <p>${career.description}</p>
                    <div class="career-details" style="margin: 1rem 0;">
                        <span><strong>Experience:</strong> ${career.experience_required} years</span><br>
                        <span><strong>Location:</strong> ${career.location}</span>
                    </div>
                    <a href="mailto:matricanetworks@gmail.com?subject=Application for ${career.title}" class="btn">Apply Now</a>
                `;
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<div class="card"><p>Error loading career opportunities. Please try again later.</p></div>';
        }
    } catch (error) {
        console.error('Error fetching careers:', error);
        container.innerHTML = '<div class="card"><p>Error loading career opportunities. Please try again later.</p></div>';
    }
}

async function loadProducts() {
    const container = document.getElementById('products-container');
    if (!container) return;

    try {
        const response = await app.apiRequest('/cgi-bin/products_api.py');
        if (response.success && response.data) {
            container.innerHTML = ''; // Clear loading message
            if (response.data.length === 0) {
                container.innerHTML = '<p>No products found.</p>';
                return;
            }
            response.data.forEach(product => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <img src="${product.logo_url || 'assets/images/default-product.png'}" alt="${product.name}" style="width:100%; height:200px; object-fit:cover; border-radius:8px;">
                    <h3>${product.name}</h3>
                    <p>${product.description}</p>
                    <button class="btn">Learn More</button>
                `;
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<p>Error loading products.</p>';
        }
    } catch (error) {
        console.error('Error fetching products:', error);
        container.innerHTML = '<p>Error loading products. Please try again later.</p>';
    }
}

async function loadResources() {
    const container = document.getElementById('resources-container');
    if (!container) return;

    try {
        const response = await app.apiRequest('/cgi-bin/resources_api.py');
        if (response.success && response.data) {
            container.innerHTML = ''; // Clear loading message
            if (response.data.length === 0) {
                container.innerHTML = '<p>No resources found.</p>';
                return;
            }
            // Group resources by type
            const resourcesByType = response.data.reduce((acc, resource) => {
                if (!acc[resource.type]) {
                    acc[resource.type] = [];
                }
                acc[resource.type].push(resource);
                return acc;
            }, {});

            for (const type in resourcesByType) {
                const categoryDiv = document.createElement('div');
                categoryDiv.className = 'resource-category';
                categoryDiv.innerHTML = `<h3>${type}</h3>`;

                const gridDiv = document.createElement('div');
                gridDiv.className = 'card-grid';

                resourcesByType[type].forEach(resource => {
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.innerHTML = `
                        <h4>${resource.title}</h4>
                        <p>${resource.content}</p>
                        ${resource.file_url ? `<a href="${resource.file_url}" class="btn btn-secondary" target="_blank">View Resource</a>` : ''}
                    `;
                    gridDiv.appendChild(card);
                });
                categoryDiv.appendChild(gridDiv);
                container.appendChild(categoryDiv);
            }
        } else {
            container.innerHTML = '<p>Error loading resources.</p>';
        }
    } catch (error) {
        console.error('Error fetching resources:', error);
        container.innerHTML = '<p>Error loading resources. Please try again later.</p>';
    }
}

function handleContactForm(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    // Basic validation
    if (!data.name || !data.email || !data.message) {
        alert('Please fill in all required fields');
        return;
    }
    
    // Submit form data
    fetch('/cgi-bin/submit_contact.py', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Thank you for your message! We will get back to you soon.');
            e.target.reset();
        } else {
            alert('Error: ' + (data.error || 'Something went wrong'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while sending your message.');
    });
}

// Theme toggle logic
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
} 