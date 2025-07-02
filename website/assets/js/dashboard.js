/**
 * Admin Dashboard JavaScript for Matrica Networks
 * Handles all CRUD operations for admin panel
 */

class AdminDashboard {
    constructor() {
        this.currentSection = 'contacts';
        this.data = {
            contacts: [],
            team: [],
            careers: [],
            resources: [],
            products: []
        };
        
        this.init();
    }
    
    init() {
        this.setupNavigation();
        this.loadAllData();
        this.setupModals();
    }
    
    setupNavigation() {
        const navButtons = document.querySelectorAll('.admin-nav button');
        navButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const section = e.target.dataset.section;
                this.switchSection(section);
            });
        });
        
        // Set initial active section
        this.switchSection('contacts');
    }
    
    switchSection(section) {
        // Update navigation
        document.querySelectorAll('.admin-nav button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.admin-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}-section`).classList.add('active');
        
        this.currentSection = section;
        this.renderCurrentSection();
    }
    
    async loadAllData() {
        try {
            await Promise.all([
                this.loadContacts(),
                this.loadTeam(),
                this.loadCareers(),
                this.loadResources(),
                this.loadProducts()
            ]);
            this.renderCurrentSection();
        } catch (error) {
            console.error('Failed to load data:', error);
            app.showAlert('Failed to load dashboard data', 'error');
        }
    }
    
    async loadContacts() {
        const result = await app.apiRequest('/cgi-bin/contacts_api.py');
        if (result.success) {
            this.data.contacts = result.data;
        }
    }
    
    async loadTeam() {
        const result = await app.apiRequest('/cgi-bin/team_api.py');
        if (result.success) {
            this.data.team = result.data;
        }
    }
    
    async loadCareers() {
        const result = await app.apiRequest('/cgi-bin/careers_api.py');
        if (result.success) {
            this.data.careers = result.data;
        }
    }
    
    async loadResources() {
        const result = await app.apiRequest('/cgi-bin/resources_api.py');
        if (result.success) {
            this.data.resources = result.data;
        }
    }
    
    async loadProducts() {
        const result = await app.apiRequest('/cgi-bin/products_api.py');
        if (result.success) {
            this.data.products = result.data;
        }
    }
    
    renderCurrentSection() {
        switch (this.currentSection) {
            case 'contacts':
                this.renderContacts();
                break;
            case 'team':
                this.renderTeam();
                break;
            case 'careers':
                this.renderCareers();
                break;
            case 'resources':
                this.renderResources();
                break;
            case 'products':
                this.renderProducts();
                break;
        }
    }
    
    renderContacts() {
        const container = document.getElementById('contacts-list');
        if (!container) return;
        
        if (this.data.contacts.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No contact submissions yet.</p>';
            return;
        }
        
        container.innerHTML = `
            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Phone</th>
                            <th>Subject</th>
                            <th>Message</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.data.contacts.map(contact => `
                            <tr>
                                <td>${contact.name}</td>
                                <td>${contact.email}</td>
                                <td>${contact.phone || 'N/A'}</td>
                                <td>${contact.subject || 'N/A'}</td>
                                <td title="${contact.message}">${this.truncateText(contact.message, 50)}</td>
                                <td>${app.formatDate(contact.timestamp)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    }
    
    renderTeam() {
        const container = document.getElementById('team-list');
        if (!container) return;
        
        container.innerHTML = `
            <div class="mb-2">
                <button class="btn" onclick="dashboard.showAddTeamModal()">Add Team Member</button>
            </div>
            <div class="card-grid">
                ${this.data.team.map(member => `
                    <div class="card">
                        <img src="${member.photo_url || '/assets/images/default-avatar.png'}" 
                             alt="${member.name}" 
                             style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-bottom: 1rem;"
                             onerror="this.src='/assets/images/default-avatar.png'">
                        <h4>${member.name}</h4>
                        <p><strong>${member.title}</strong></p>
                        <p class="text-muted">${this.truncateText(member.bio, 100)}</p>
                        <div style="display: flex; gap: 0.5rem; justify-content: center;">
                            <button class="btn btn-secondary" onclick="dashboard.showEditTeamModal(${member.id})">Edit</button>
                            <button class="btn btn-danger" onclick="dashboard.deleteTeamMember(${member.id})">Delete</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderCareers() {
        const container = document.getElementById('careers-list');
        if (!container) return;
        
        container.innerHTML = `
            <div class="mb-2">
                <button class="btn" onclick="dashboard.showAddCareerModal()">Add Job Opening</button>
            </div>
            <div class="card-grid">
                ${this.data.careers.map(career => `
                    <div class="card">
                        <h4>${career.title}</h4>
                        <p>${this.truncateText(career.description, 150)}</p>
                        <p><strong>Experience:</strong> ${career.experience_required} years</p>
                        <p><strong>Location:</strong> ${career.location}</p>
                        <div style="display: flex; gap: 0.5rem; justify-content: center; margin-top: 1rem;">
                            <button class="btn btn-secondary btn-sm" onclick="dashboard.showEditCareerModal(${career.id})">Edit</button>
                            <button class="btn btn-danger btn-sm" onclick="dashboard.deleteCareer(${career.id})">Delete</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderResources() {
        const container = document.getElementById('resources-list');
        if (!container) return;
        
        container.innerHTML = `
            <div class="mb-2">
                <button class="btn" onclick="dashboard.showAddResourceModal()">Add Resource</button>
            </div>
            <div class="card-grid">
                ${this.data.resources.map(resource => `
                    <div class="card">
                        <h4>${resource.title}</h4>
                        <p><strong>Type:</strong> ${resource.type}</p>
                        <p>${this.truncateText(resource.content, 150)}</p>
                        ${resource.file_path ? `<p><a href="${resource.file_path}" target="_blank" class="btn btn-link">📄 View File</a></p>` : ''}
                        <div style="display: flex; gap: 0.5rem; justify-content: center;">
                            <button class="btn btn-secondary" onclick="dashboard.showEditResourceModal(${resource.id})">Edit</button>
                            <button class="btn btn-danger" onclick="dashboard.deleteResource(${resource.id})">Delete</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    renderProducts() {
        const container = document.getElementById('products-list');
        if (!container) return;
        
        container.innerHTML = `
            <div class="mb-2">
                <button class="btn" onclick="dashboard.showAddProductModal()">Add Product</button>
            </div>
            <div class="card-grid">
                ${this.data.products.map(product => `
                    <div class="card">
                        <img src="${product.logo_url || '/assets/images/default-product.png'}" 
                             alt="${product.name}" 
                             style="width: 100%; height: 150px; object-fit: cover; margin-bottom: 1rem;"
                             onerror="this.src='/assets/images/default-product.png'">
                        <h4>${product.name}</h4>
                        <p>${this.truncateText(product.description, 150)}</p>
                        <div style="display: flex; gap: 0.5rem; justify-content: center;">
                            <button class="btn btn-secondary" onclick="dashboard.showEditProductModal(${product.id})">Edit</button>
                            <button class="btn btn-danger" onclick="dashboard.deleteProduct(${product.id})">Delete</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Modal Management
    setupModals() {
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal();
            }
        });
        
        // Close modal with escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }
    
    showModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }
    
    closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('active');
        });
    }
    
    // Team Management
    showAddTeamModal() {
        this.showModal('team-modal');
        document.getElementById('team-form').reset();
        document.getElementById('team-form').dataset.mode = 'add';
        document.getElementById('team-form').dataset.memberId = '';
        document.querySelector('#team-modal h3').textContent = 'Add Team Member';
    }
    
    showEditTeamModal(id) {
        const member = this.data.team.find(m => m.id === id);
        if (!member) return;
        
        this.showModal('team-modal');
        document.getElementById('team-form').dataset.mode = 'edit';
        document.getElementById('team-form').dataset.memberId = id;
        document.querySelector('#team-modal h3').textContent = 'Edit Team Member';
        
        // Populate form with existing data
        document.getElementById('team-name').value = member.name;
        document.getElementById('team-title').value = member.title;
        document.getElementById('team-bio').value = member.bio;
        document.getElementById('team-photo-url').value = member.photo_url || '';
    }
    
    async addTeamMember(formData) {
        try {
            const form = document.getElementById('team-form');
            const mode = form.dataset.mode;
            const memberId = form.dataset.memberId;
            
            let url = '/cgi-bin/team_api.py';
            let method = 'POST';
            
            if (mode === 'edit' && memberId) {
                url += `?id=${memberId}`;
                method = 'PUT';
            }
            
            const result = await app.apiRequest(url, {
                method: method,
                body: formData
            });
            
            if (result.success) {
                const message = mode === 'edit' ? 'Team member updated successfully' : 'Team member added successfully';
                app.showAlert(message, 'success');
                await this.loadTeam();
                this.renderTeam();
                this.closeModal();
            } else {
                app.showAlert(result.error, 'error');
            }
        } catch (error) {
            const mode = document.getElementById('team-form').dataset.mode;
            const message = mode === 'edit' ? 'Failed to update team member' : 'Failed to add team member';
            app.showAlert(message, 'error');
        }
    }
    
    async deleteTeamMember(id) {
        if (!confirm('Are you sure you want to delete this team member?')) return;
        
        try {
            const result = await app.apiRequest(`/cgi-bin/team_api.py?id=${id}`, {
                method: 'DELETE'
            });
            
            if (result.success) {
                app.showAlert('Team member deleted successfully', 'success');
                await this.loadTeam();
                this.renderTeam();
            } else {
                app.showAlert(result.error, 'error');
            }
        } catch (error) {
            app.showAlert('Failed to delete team member', 'error');
        }
    }
    
    // Career Management
    showAddCareerModal() {
        this.showModal('career-modal');
        const form = document.getElementById('career-form');
        form.reset();
        form.dataset.mode = 'add';
        form.dataset.careerId = '';
        document.querySelector('#career-modal h3').textContent = 'Add Career Opportunity';
        form.querySelector('button[type="submit"]').textContent = 'Add Career Opportunity';
    }

    showEditCareerModal(id) {
        const career = this.data.careers.find(c => c.id === id);
        if (!career) return;

        this.showModal('career-modal');
        const form = document.getElementById('career-form');
        form.reset(); // Reset first then populate
        form.dataset.mode = 'edit';
        form.dataset.careerId = id;

        document.querySelector('#career-modal h3').textContent = 'Edit Career Opportunity';
        document.getElementById('career-title').value = career.title;
        document.getElementById('career-description').value = career.description;
        document.getElementById('career-experience').value = career.experience_required;
        document.getElementById('career-location').value = career.location;
        form.querySelector('button[type="submit"]').textContent = 'Save Changes';
    }

    async saveCareer(formData) { // Renamed from addCareer
        const form = document.getElementById('career-form');
        const mode = form.dataset.mode;
        const careerId = form.dataset.careerId;

        let url = '/cgi-bin/careers_api.py';
        let method = 'POST';

        if (mode === 'edit' && careerId) {
            url += `?id=${careerId}`;
            method = 'PUT';
        }

        try {
            const result = await app.apiRequest(url, {
                method: method,
                body: formData
            });
            
            if (result.success) {
                const message = mode === 'edit' ? 'Job opening updated successfully' : 'Job opening added successfully';
                app.showAlert(message, 'success');
                await this.loadCareers();
                this.renderCareers();
                this.closeModal();
            } else {
                app.showAlert(result.error || 'An unknown error occurred', 'error');
            }
        } catch (error) {
            console.error('Failed to save job opening:', error);
            const message = mode === 'edit' ? 'Failed to update job opening' : 'Failed to add job opening';
            app.showAlert(message, 'error');
        }
    }
    
    async deleteCareer(id) {
        if (!confirm('Are you sure you want to delete this job opening?')) return;
        
        try {
            const result = await app.apiRequest(`/cgi-bin/careers_api.py?id=${id}`, {
                method: 'DELETE'
            });
            
            if (result.success) {
                app.showAlert('Job opening deleted successfully', 'success');
                await this.loadCareers();
                this.renderCareers();
            } else {
                app.showAlert(result.error, 'error');
            }
        } catch (error) {
            app.showAlert('Failed to delete job opening', 'error');
        }
    }
    
    // Resource Management
    showAddResourceModal() {
        this.showModal('resource-modal');
        document.getElementById('resource-form').reset();
        document.getElementById('resource-form').dataset.mode = 'add';
        document.getElementById('resource-form').dataset.resourceId = '';
        document.querySelector('#resource-modal h3').textContent = 'Add Resource';
    }
    
    showEditResourceModal(id) {
        const resource = this.data.resources.find(r => r.id === id);
        if (!resource) return;
        
        this.showModal('resource-modal');
        document.getElementById('resource-form').dataset.mode = 'edit';
        document.getElementById('resource-form').dataset.resourceId = id;
        document.querySelector('#resource-modal h3').textContent = 'Edit Resource';
        
        // Populate form with existing data
        document.getElementById('resource-title').value = resource.title;
        document.getElementById('resource-type').value = resource.type;
        document.getElementById('resource-content').value = resource.content;
    }
    
    async addResource(formData) {
        try {
            const form = document.getElementById('resource-form');
            const mode = form.dataset.mode;
            const resourceId = form.dataset.resourceId;
            
            let url = '/cgi-bin/resources_api.py';
            let method = 'POST';
            
            if (mode === 'edit' && resourceId) {
                url += `?id=${resourceId}`;
                method = 'PUT';
            }
            
            const result = await app.apiRequest(url, {
                method: method,
                body: formData
            });
            
            if (result.success) {
                const message = mode === 'edit' ? 'Resource updated successfully' : 'Resource added successfully';
                app.showAlert(message, 'success');
                await this.loadResources();
                this.renderResources();
                this.closeModal();
            } else {
                app.showAlert(result.error, 'error');
            }
        } catch (error) {
            const mode = document.getElementById('resource-form').dataset.mode;
            const message = mode === 'edit' ? 'Failed to update resource' : 'Failed to add resource';
            app.showAlert(message, 'error');
        }
    }
    
    async deleteResource(id) {
        if (!confirm('Are you sure you want to delete this resource?')) return;
        
        try {
            const result = await app.apiRequest(`/cgi-bin/resources_api.py?id=${id}`, {
                method: 'DELETE'
            });
            
            if (result.success) {
                app.showAlert('Resource deleted successfully', 'success');
                await this.loadResources();
                this.renderResources();
            } else {
                app.showAlert(result.error, 'error');
            }
        } catch (error) {
            app.showAlert('Failed to delete resource', 'error');
        }
    }
    
    // Product Management
    showAddProductModal() {
        this.showModal('product-modal');
        document.getElementById('product-form').reset();
        document.getElementById('product-form').dataset.mode = 'add';
        document.getElementById('product-form').dataset.productId = '';
        document.querySelector('#product-modal h3').textContent = 'Add Product';
    }
    
    showEditProductModal(id) {
        const product = this.data.products.find(p => p.id === id);
        if (!product) return;
        
        this.showModal('product-modal');
        document.getElementById('product-form').dataset.mode = 'edit';
        document.getElementById('product-form').dataset.productId = id;
        document.querySelector('#product-modal h3').textContent = 'Edit Product';
        
        // Populate form with existing data
        document.getElementById('product-name').value = product.name;
        document.getElementById('product-description').value = product.description;
        document.getElementById('product-logo').value = product.logo_url || '';
    }
    
    async addProduct(formData) {
        try {
            const form = document.getElementById('product-form');
            const mode = form.dataset.mode;
            const productId = form.dataset.productId;
            
            let url = '/cgi-bin/products_api.py';
            let method = 'POST';
            
            if (mode === 'edit' && productId) {
                url += `?id=${productId}`;
                method = 'PUT';
            }
            
            const result = await app.apiRequest(url, {
                method: method,
                body: formData
            });
            
            if (result.success) {
                const message = mode === 'edit' ? 'Product updated successfully' : 'Product added successfully';
                app.showAlert(message, 'success');
                await this.loadProducts();
                this.renderProducts();
                this.closeModal();
            } else {
                app.showAlert(result.error, 'error');
            }
        } catch (error) {
            const mode = document.getElementById('product-form').dataset.mode;
            const message = mode === 'edit' ? 'Failed to update product' : 'Failed to add product';
            app.showAlert(message, 'error');
        }
    }
    
    async deleteProduct(id) {
        if (!confirm('Are you sure you want to delete this product?')) return;
        
        try {
            const result = await app.apiRequest(`/cgi-bin/products_api.py?id=${id}`, {
                method: 'DELETE'
            });
            
            if (result.success) {
                app.showAlert('Product deleted successfully', 'success');
                await this.loadProducts();
                this.renderProducts();
            } else {
                app.showAlert(result.error, 'error');
            }
        } catch (error) {
            app.showAlert('Failed to delete product', 'error');
        }
    }
    
    // Utility Functions
    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }
    
    handleFileUpload(input, callback) {
        const file = input.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            callback(e.target.result);
        };
        reader.readAsDataURL(file);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.includes('dashboard.html')) {
        window.dashboard = new AdminDashboard();
    }
});

// Form submission handlers
function handleTeamForm(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    dashboard.addTeamMember(formData);
}

function handleCareerForm(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    dashboard.saveCareer(formData); // Changed from addCareer to saveCareer
}

function handleResourceForm(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    dashboard.addResource(formData);
}

function handleProductForm(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    dashboard.addProduct(formData);
}