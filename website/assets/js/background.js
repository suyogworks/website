/**
 * 3D Animated Background for Matrica Networks
 * Cyberpunk-style binary streams and neural network visualization
 */

class CyberBackground {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.nodes = [];
        this.connections = [];
        this.animationId = null;
        this.theme = 'dark';
        
        this.init();
    }
    
    init() {
        this.createCanvas();
        this.setupParticles();
        this.setupNodes();
        this.setupConnections();
        this.animate();
        this.handleResize();
        this.handleThemeChange();
    }
    
    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'background-canvas';
        this.ctx = this.canvas.getContext('2d');
        document.body.appendChild(this.canvas);
        
        this.resizeCanvas();
    }
    
    resizeCanvas() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }
    
    setupParticles() {
        this.particles = [];
        const particleCount = Math.floor((this.canvas.width * this.canvas.height) / 15000);
        
        for (let i = 0; i < particleCount; i++) {
            this.particles.push(this.createParticle());
        }
    }
    
    createParticle() {
        const direction = Math.random() < 0.5 ? 'left-to-right' : 'right-to-left';
        const isBurst = Math.random() < 0.1; // 10% chance for burst effect
        
        return {
            x: direction === 'left-to-right' ? -50 : this.canvas.width + 50,
            y: Math.random() * this.canvas.height,
            speed: (Math.random() * 2 + 1) * (isBurst ? 3 : 1),
            direction: direction,
            char: Math.random() < 0.5 ? '0' : '1',
            opacity: Math.random() * 0.8 + 0.2,
            size: Math.random() * 12 + 8,
            isBurst: isBurst,
            life: isBurst ? Math.random() * 100 + 50 : Infinity,
            maxLife: isBurst ? Math.random() * 100 + 50 : Infinity
        };
    }
    
    setupNodes() {
        this.nodes = [];
        const nodeCount = Math.floor((this.canvas.width * this.canvas.height) / 50000);
        
        for (let i = 0; i < nodeCount; i++) {
            this.nodes.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                radius: Math.random() * 3 + 2,
                pulse: Math.random() * Math.PI * 2,
                pulseSpeed: Math.random() * 0.02 + 0.01,
                opacity: Math.random() * 0.6 + 0.4
            });
        }
    }
    
    setupConnections() {
        this.connections = [];
        
        // Create connections between nearby nodes
        for (let i = 0; i < this.nodes.length; i++) {
            for (let j = i + 1; j < this.nodes.length; j++) {
                const distance = this.getDistance(this.nodes[i], this.nodes[j]);
                
                if (distance < 150 && Math.random() < 0.3) {
                    this.connections.push({
                        nodeA: this.nodes[i],
                        nodeB: this.nodes[j],
                        opacity: Math.random() * 0.3 + 0.1,
                        pulseOffset: Math.random() * Math.PI * 2
                    });
                }
            }
        }
    }
    
    getDistance(pointA, pointB) {
        return Math.sqrt(
            Math.pow(pointA.x - pointB.x, 2) + 
            Math.pow(pointA.y - pointB.y, 2)
        );
    }
    
    updateParticles() {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const particle = this.particles[i];
            
            // Update position
            if (particle.direction === 'left-to-right') {
                particle.x += particle.speed;
            } else {
                particle.x -= particle.speed;
            }
            
            // Update burst particles
            if (particle.isBurst) {
                particle.life--;
                particle.opacity = (particle.life / particle.maxLife) * 0.8;
            }
            
            // Remove particles that are off-screen or dead
            if (particle.x < -100 || particle.x > this.canvas.width + 100 || 
                (particle.isBurst && particle.life <= 0)) {
                this.particles.splice(i, 1);
                this.particles.push(this.createParticle());
            }
        }
    }
    
    updateNodes() {
        this.nodes.forEach(node => {
            node.pulse += node.pulseSpeed;
        });
    }
    
    drawParticles() {
        const colors = this.getThemeColors();
        
        this.particles.forEach(particle => {
            this.ctx.save();
            
            // Set color based on theme and particle type
            let color = colors.primary;
            if (particle.isBurst) {
                color = colors.burst;
            } else if (Math.random() < 0.3) {
                color = colors.secondary;
            }
            
            this.ctx.fillStyle = `rgba(${color}, ${particle.opacity})`;
            this.ctx.font = `${particle.size}px 'Courier New', monospace`;
            this.ctx.textAlign = 'center';
            
            // Add glow effect
            this.ctx.shadowColor = `rgba(${color}, ${particle.opacity})`;
            this.ctx.shadowBlur = particle.isBurst ? 20 : 10;
            
            this.ctx.fillText(particle.char, particle.x, particle.y);
            
            this.ctx.restore();
        });
    }
    
    drawNodes() {
        const colors = this.getThemeColors();
        
        this.nodes.forEach(node => {
            this.ctx.save();
            
            const pulseIntensity = Math.sin(node.pulse) * 0.5 + 0.5;
            const currentRadius = node.radius + pulseIntensity * 2;
            const currentOpacity = node.opacity * (0.5 + pulseIntensity * 0.5);
            
            // Draw node
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, currentRadius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(${colors.primary}, ${currentOpacity})`;
            this.ctx.shadowColor = `rgba(${colors.primary}, ${currentOpacity})`;
            this.ctx.shadowBlur = 15;
            this.ctx.fill();
            
            this.ctx.restore();
        });
    }
    
    drawConnections() {
        const colors = this.getThemeColors();
        
        this.connections.forEach(connection => {
            this.ctx.save();
            
            const pulseA = Math.sin(connection.nodeA.pulse + connection.pulseOffset);
            const pulseB = Math.sin(connection.nodeB.pulse + connection.pulseOffset);
            const avgPulse = (pulseA + pulseB) / 2;
            const currentOpacity = connection.opacity * (0.3 + Math.abs(avgPulse) * 0.4);
            
            this.ctx.beginPath();
            this.ctx.moveTo(connection.nodeA.x, connection.nodeA.y);
            this.ctx.lineTo(connection.nodeB.x, connection.nodeB.y);
            this.ctx.strokeStyle = `rgba(${colors.tertiary}, ${currentOpacity})`;
            this.ctx.lineWidth = 1;
            this.ctx.shadowColor = `rgba(${colors.tertiary}, ${currentOpacity})`;
            this.ctx.shadowBlur = 5;
            this.ctx.stroke();
            
            this.ctx.restore();
        });
    }
    
    getThemeColors() {
        if (this.theme === 'light') {
            return {
                primary: '0, 102, 204',      // Blue
                secondary: '204, 0, 102',    // Pink
                tertiary: '0, 204, 102',     // Green
                burst: '204, 136, 0'         // Orange
            };
        } else {
            return {
                primary: '0, 255, 255',      // Cyan
                secondary: '255, 0, 255',    // Magenta
                tertiary: '0, 255, 0',       // Lime
                burst: '255, 255, 0'         // Yellow
            };
        }
    }
    
    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.updateParticles();
        this.updateNodes();
        
        this.drawConnections();
        this.drawNodes();
        this.drawParticles();
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    handleResize() {
        window.addEventListener('resize', () => {
            this.resizeCanvas();
            this.setupParticles();
            this.setupNodes();
            this.setupConnections();
        });
    }
    
    handleThemeChange() {
        // Listen for theme changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                    this.theme = document.documentElement.getAttribute('data-theme') || 'dark';
                }
            });
        });
        
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme']
        });
        
        // Initial theme detection
        this.theme = document.documentElement.getAttribute('data-theme') || 'dark';
    }
    
    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }
}

// Initialize background when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.cyberBackground = new CyberBackground();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.cyberBackground) {
        window.cyberBackground.destroy();
    }
});