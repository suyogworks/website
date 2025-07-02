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
            products: [],
            employees: [],
            companyHandbook: null // Added company handbook data
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
                this.loadProducts(),
                this.loadEmployees(),
                this.loadCompanyHandbook() // Added call to load handbook
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

    async loadEmployees() {
        // This will be implemented once the employee_admin_api.py is ready
        // For now, simulate empty or mock data if needed for UI testing
        try {
            const result = await app.apiRequest('/cgi-bin/employee_admin_api.py');
            if (result.success) {
                this.data.employees = result.data;
            } else {
                this.data.employees = [];
                console.error("Failed to load employees:", result.error);
            }
        } catch (error) {
            this.data.employees = [];
            console.error("Error fetching employees:", error);
        }
    }

    async loadCompanyHandbook() {
        try {
            const result = await app.apiRequest('/cgi-bin/handbook_api.py'); // API to be created
            if (result.success && result.data) {
                this.data.companyHandbook = result.data;
            } else {
                this.data.companyHandbook = null;
                // console.info("No company handbook found or error loading:", result.error);
            }
        } catch (error) {
            this.data.companyHandbook = null;
            console.error("Error fetching company handbook:", error);
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
            case 'employees':
                this.renderEmployees();
                break;
            case 'settings': // Added case for settings
                this.renderCompanySettings();
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

// Employee Management Methods
AdminDashboard.prototype.renderEmployees = function() {
    const container = document.getElementById('employees-list');
    if (!container) return;

    container.innerHTML = `
        <div class="mb-2">
            <button class="btn" onclick="dashboard.showAddEmployeeModal()">Add New Employee</button>
        </div>
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Full Name</th>
                        <th>Username</th>
                        <th>Designation</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${this.data.employees && this.data.employees.length > 0 ? this.data.employees.map(emp => `
                        <tr>
                            <td>${emp.id}</td>
                            <td>${emp.full_name}</td>
                            <td>${emp.username}</td>
                            <td>${emp.designation || 'N/A'}</td>
                            <td>${emp.email || 'N/A'}</td>
                            <td>${emp.phone || 'N/A'}</td>
                            <td>
                                <button class="btn btn-secondary btn-sm" onclick="dashboard.showEditEmployeeModal(${emp.id})">Edit</button>
                                <button class="btn btn-danger btn-sm" onclick="dashboard.deleteEmployee(${emp.id})">Delete</button>
                                <button class="btn btn-warning btn-sm" onclick="dashboard.showResetPasswordModal(${emp.id}, '${emp.username}')">Reset Password</button>
                            </td>
                        </tr>
                    `).join('') : '<tr><td colspan="7" class="text-center">No employees found.</td></tr>'}
                </tbody>
            </table>
        </div>
    `;
};

AdminDashboard.prototype.showAddEmployeeModal = function() {
    this.showModal('employee-modal');
    const form = document.getElementById('employee-form');
    form.reset();
    document.getElementById('employee-id').value = '';
    form.dataset.mode = 'add';
    document.getElementById('employee-modal-title').textContent = 'Add New Employee';
    document.getElementById('employee-form-submit-btn').textContent = 'Add Employee';
    // Password field should be required for add
    document.getElementById('employee-password').setAttribute('required', 'required');
};

AdminDashboard.prototype.showEditEmployeeModal = function(id) {
    const employee = this.data.employees.find(emp => emp.id === id);
    if (!employee) {
        app.showAlert('Employee not found.', 'error');
        return;
    }
    this.showModal('employee-modal');
    const form = document.getElementById('employee-form');
    form.reset();
    form.dataset.mode = 'edit';

    document.getElementById('employee-modal-title').textContent = 'Edit Employee';
    document.getElementById('employee-form-submit-btn').textContent = 'Save Changes';

    document.getElementById('employee-id').value = employee.id;
    document.getElementById('employee-full-name').value = employee.full_name;
    document.getElementById('employee-username').value = employee.username;
    // Password is not pre-filled for security; only set if changing.
    document.getElementById('employee-password').value = '';
    document.getElementById('employee-password').removeAttribute('required'); // Not required for edit unless changing
    document.getElementById('employee-designation').value = employee.designation || '';
    document.getElementById('employee-email').value = employee.email || '';
    document.getElementById('employee-phone').value = employee.phone || '';
    document.getElementById('employee-profile-picture-url').value = employee.profile_picture_url || '';
};

AdminDashboard.prototype.saveEmployee = async function(formData) {
    const form = document.getElementById('employee-form');
    const mode = form.dataset.mode;
    const employeeId = formData.get('id'); // Get ID from hidden input in form data

    let url = '/cgi-bin/employee_admin_api.py';
    let method = 'POST';

    // If it's an edit and there's an employeeId, change method to PUT and append ID to URL
    if (mode === 'edit' && employeeId) {
        url += `?id=${employeeId}`;
        method = 'PUT';
    } else if (mode === 'add') {
        // Ensure password is provided for add mode
        if (!formData.get('password')) {
            app.showAlert('Password is required for new employees.', 'error');
            return;
        }
    }


    // Remove 'id' from FormData if it's empty (for 'add' mode)
    // The Python API for POST (add) won't expect an ID.
    if (mode === 'add' && !employeeId) {
        formData.delete('id');
    }

    // If password field is empty during edit, remove it from formData so it's not sent
    if (mode === 'edit' && !formData.get('password')) {
        formData.delete('password');
    }


    try {
        const result = await app.apiRequest(url, {
            method: method,
            body: formData // FormData handles multipart/form-data for file uploads
        });

        if (result.success) {
            const message = mode === 'edit' ? 'Employee updated successfully' : 'Employee added successfully';
            app.showAlert(message, 'success');
            await this.loadEmployees(); // Reload employee list
            this.renderEmployees();     // Re-render the list
            this.closeModal();
        } else {
            app.showAlert(result.error || 'An unknown error occurred', 'error');
        }
    } catch (error) {
        console.error('Failed to save employee:', error);
        const message = mode === 'edit' ? 'Failed to update employee' : 'Failed to add employee';
        app.showAlert(message, 'error');
    }
};

AdminDashboard.prototype.deleteEmployee = async function(id) {
    if (!confirm('Are you sure you want to delete this employee? This action cannot be undone.')) return;

    try {
        const result = await app.apiRequest(`/cgi-bin/employee_admin_api.py?id=${id}`, {
            method: 'DELETE'
        });

        if (result.success) {
            app.showAlert('Employee deleted successfully', 'success');
            await this.loadEmployees();
            this.renderEmployees();
        } else {
            app.showAlert(result.error || 'Failed to delete employee', 'error');
        }
    } catch (error) {
        console.error('Error deleting employee:', error);
        app.showAlert('Failed to delete employee', 'error');
    }
};

// Placeholder for Reset Password Modal - to be detailed in a later step
AdminDashboard.prototype.showResetPasswordModal = function(employeeId, username) {
    // This will be implemented when working on the password reset feature
    const newPassword = prompt(`Enter new password for ${username}:`);
    if (newPassword && newPassword.trim() !== "") {
        const confirmPassword = prompt(`Confirm new password for ${username}:`);
        if (newPassword === confirmPassword) {
            this.resetEmployeePassword(employeeId, newPassword);
        } else if (confirmPassword !== null) { // only show error if confirm was not cancelled
            alert("Passwords do not match.");
        }
    } else if (newPassword !== null) { // only show error if prompt was not cancelled
        alert("Password cannot be empty.");
    }
};

AdminDashboard.prototype.resetEmployeePassword = async function(employeeId, newPassword) {
    // This will call a specific API endpoint or action
    // For now, using a PUT to employee_admin_api.py with an action flag
    try {
        const result = await app.apiRequest(`/cgi-bin/employee_admin_api.py?action=reset_password&id=${employeeId}`, {
            method: 'PUT', // Or POST, depends on API design
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ password: newPassword })
        });

        if (result.success) {
            app.showAlert('Password reset successfully.', 'success');
        } else {
            app.showAlert(result.error || 'Failed to reset password.', 'error');
        }
    } catch (error) {
        console.error('Error resetting password:', error);
        app.showAlert('Failed to reset password.', 'error');
    }
};


function handleEmployeeForm(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    // Clear the file input value from FormData if no file is selected,
    // to prevent sending an empty "profile_picture_file" field which might confuse the backend.
    const profilePicFile = formData.get('profile_picture_file');
    if (profilePicFile && profilePicFile.name === "") {
        formData.delete('profile_picture_file');
    }
    dashboard.saveEmployee(formData);
}

// Company Handbook Management Methods
AdminDashboard.prototype.renderCompanySettings = function() {
    this.renderCompanyHandbook();
    // Other settings can be rendered here if added later
};

AdminDashboard.prototype.renderCompanyHandbook = function() {
    const handbookInfoDiv = document.getElementById('handbook-info');
    const deleteButton = document.getElementById('delete-handbook-btn');
    const uploadForm = document.getElementById('handbook-upload-form');

    if (!handbookInfoDiv || !deleteButton || !uploadForm) return;

    if (this.data.companyHandbook && this.data.companyHandbook.file_path) {
        handbookInfoDiv.innerHTML = `
            <p><strong>Current Handbook:</strong> <a href="${this.data.companyHandbook.file_path}" target="_blank">${this.data.companyHandbook.file_name}</a></p>
            <p><small>Uploaded: ${app.formatDate(this.data.companyHandbook.uploaded_at)}</small></p>
        `;
        deleteButton.style.display = 'inline-block';
    } else {
        handbookInfoDiv.innerHTML = '<p>No company handbook has been uploaded yet.</p>';
        deleteButton.style.display = 'none';
    }

    // Ensure event listeners are (re)attached here or in a more global setup
    // For simplicity, re-attaching if they might be destroyed by innerHTML changes or section switching.
    // A more robust solution might use event delegation or attach once in init().
    if (!uploadForm.dataset.listenerAttached) {
        uploadForm.addEventListener('submit', this.handleHandbookUpload.bind(this));
        uploadForm.dataset.listenerAttached = 'true';
    }
    if (!deleteButton.dataset.listenerAttached) {
        deleteButton.addEventListener('click', this.deleteCompanyHandbook.bind(this));
        deleteButton.dataset.listenerAttached = 'true';
    }
};

AdminDashboard.prototype.handleHandbookUpload = async function(event) {
    event.preventDefault();
    const form = event.target;
    const fileInput = form.querySelector('#handbook-file');

    if (!fileInput.files || fileInput.files.length === 0) {
        app.showAlert('Please select a PDF file to upload.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('handbook_file', fileInput.files[0]);

    try {
        const result = await app.apiRequest('/cgi-bin/handbook_api.py', {
            method: 'POST',
            body: formData
        });

        if (result.success) {
            app.showAlert('Company handbook uploaded successfully.', 'success');
            await this.loadCompanyHandbook();
            this.renderCompanyHandbook();
            form.reset();
        } else {
            app.showAlert(result.error || 'Failed to upload handbook.', 'error');
        }
    } catch (error) {
        console.error('Error uploading handbook:', error);
        app.showAlert('An error occurred during handbook upload.', 'error');
    }
};

AdminDashboard.prototype.deleteCompanyHandbook = async function() {
    if (!confirm('Are you sure you want to delete the current company handbook?')) return;

    try {
        const result = await app.apiRequest('/cgi-bin/handbook_api.py', {
            method: 'DELETE'
        });

        if (result.success) {
            app.showAlert('Company handbook deleted successfully.', 'success');
            await this.loadCompanyHandbook();
            this.renderCompanyHandbook();
        } else {
            app.showAlert(result.error || 'Failed to delete handbook.', 'error');
        }
    } catch (error) {
        console.error('Error deleting handbook:', error);
        app.showAlert('An error occurred while deleting the handbook.', 'error');
    }
};