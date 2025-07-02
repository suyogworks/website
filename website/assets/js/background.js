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
        this.mouse = { x: null, y: null, radius: 100 };
        this.ripples = [];
        this.sparkles = []; // Added sparkles array
        
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
        this.handleMouseMove();
        this.handleMouseClick(); // Added mouse click listener
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
        let char = Math.random() < 0.5 ? '0' : '1';
        const commonChars = ['0', '1'];
        const rareChars = ['#', '$', '%', '&', '*', '@', '>', '<', '/']; // Cyberpunk-ish symbols
        
        if (isBurst) {
            char = rareChars[Math.floor(Math.random() * rareChars.length)];
        } else if (Math.random() < 0.05) { // 5% chance for a non-0/1 character normally
            char = rareChars[Math.floor(Math.random() * rareChars.length)];
        }

        return {
            x: direction === 'left-to-right' ? -50 : this.canvas.width + 50,
            y: Math.random() * this.canvas.height,
            speed: (Math.random() * 2 + 1) * (isBurst ? 3 : 1.5), // Burst particles are faster
            direction: direction,
            char: char,
            opacity: Math.random() * 0.8 + 0.2,
            size: Math.random() * 12 + (isBurst ? 10 : 8), // Burst particles can be slightly larger
            isBurst: isBurst,
            life: isBurst ? Math.random() * 80 + 40 : Infinity, // Slightly shorter life for bursts
            maxLife: isBurst ? Math.random() * 80 + 40 : Infinity
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
                
                // Vary connection probability based on distance (closer nodes more likely to connect)
                // And add a general randomness factor
                const baseConnectionProbability = 0.1; // Base chance to connect
                const distanceFactor = Math.max(0, 1 - (distance / 200)); // Higher for closer nodes, max dist 200

                if (distance < 200 && Math.random() < (baseConnectionProbability + distanceFactor * 0.4)) { // Max prob ~0.5 for very close
                    this.connections.push({
                        nodeA: this.nodes[i],
                        nodeB: this.nodes[j],
                        opacity: (Math.random() * 0.2 + 0.05) * (distanceFactor + 0.5), // Closer connections can be slightly more opaque
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

            // Mouse interaction
            if (this.mouse.x !== null && this.mouse.y !== null) {
                const dx = particle.x - this.mouse.x;
                const dy = particle.y - this.mouse.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < this.mouse.radius) {
                    const forceDirectionX = dx / distance;
                    const forceDirectionY = dy / distance;
                    const force = (this.mouse.radius - distance) / this.mouse.radius;

                    // Make particles move away from cursor
                    particle.x += forceDirectionX * force * 5; // Adjust multiplier for strength
                    particle.y += forceDirectionY * force * 5;

                    // Optional: slightly increase opacity or change color when near mouse
                    particle.opacity = Math.min(1, particle.opacity + force * 0.5);
                }
            }

            // Ripple interaction for particles
            this.ripples.forEach(ripple => {
                if (ripple.life > 0) { // Only interact with active ripples
                    const dx = particle.x - ripple.x;
                    const dy = particle.y - ripple.y;
                    const distanceToRippleCenter = Math.sqrt(dx * dx + dy * dy);

                    // Check if particle is near the ripple's expanding edge
                    const rippleEffectRadius = 20; // How far from the edge the effect is felt
                    if (Math.abs(distanceToRippleCenter - ripple.currentRadius) < rippleEffectRadius) {
                        const force = (rippleEffectRadius - Math.abs(distanceToRippleCenter - ripple.currentRadius)) / rippleEffectRadius;
                        if (distanceToRippleCenter > 0) { // Avoid division by zero if particle is at ripple center
                            const forceDirectionX = dx / distanceToRippleCenter;
                            const forceDirectionY = dy / distanceToRippleCenter;
                            // Push particle away from ripple center
                            particle.x += forceDirectionX * force * 1.5; // Adjust strength
                            particle.y += forceDirectionY * force * 1.5;
                        }
                    }
                }
            });
            
            // Remove particles that are off-screen or dead
            if (particle.x < -100 || particle.x > this.canvas.width + 100 || 
                particle.y < -100 || particle.y > this.canvas.height + 100 || // Check Y bounds too
                (particle.isBurst && particle.life <= 0)) {
                this.particles.splice(i, 1);
                this.particles.push(this.createParticle());
            }
        }
    }
    
    updateNodes() {
        this.nodes.forEach(node => {
            node.pulse += node.pulseSpeed;

            // Mouse interaction for nodes
            if (this.mouse.x !== null && this.mouse.y !== null) {
                const dx = node.x - this.mouse.x;
                const dy = node.y - this.mouse.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const hoverRadius = node.radius + 20; // Make hover area a bit larger than node

                if (distance < hoverRadius) {
                    // Node is being hovered
                    node.isHovered = true;
                    node.hoverEffect = (hoverRadius - distance) / hoverRadius; // 0 to 1
                } else {
                    node.isHovered = false;
                    node.hoverEffect = 0;
                }
            } else {
                node.isHovered = false;
                node.hoverEffect = 0;
            }

            // Ripple interaction for nodes
            this.ripples.forEach(ripple => {
                if (ripple.life > 0) { // Only interact with active ripples
                    const dxNode = node.x - ripple.x;
                    const dyNode = node.y - ripple.y;
                    const distanceNodeToRippleCenter = Math.sqrt(dxNode * dxNode + dyNode * dyNode);

                    const rippleEffectRadius = 25; // How far from the edge the effect is felt for nodes
                    if (Math.abs(distanceNodeToRippleCenter - ripple.currentRadius) < rippleEffectRadius) {
                        const force = (rippleEffectRadius - Math.abs(distanceNodeToRippleCenter - ripple.currentRadius)) / rippleEffectRadius;
                         if (distanceNodeToRippleCenter > 0) { // Avoid division by zero
                            const forceDirectionX = dxNode / distanceNodeToRippleCenter;
                            const forceDirectionY = dyNode / distanceNodeToRippleCenter;
                            // Push node away from ripple center
                            node.x += forceDirectionX * force * 1.0; // Adjust strength (make it less than particles)
                            node.y += forceDirectionY * force * 1.0;
                        }
                        // Optionally, make node pulse once or change color briefly
                        node.pulse += force * 0.5; // Add a bit of energy to its pulse
                        if (Math.random() < 0.1 * force) { // Small chance to sparkle from ripple
                            this.createSparkle(node.x, node.y, this.getThemeColors().burst);
                        }
                    }
                }
            });

            // Sparkle on strong hover
            if (node.isHovered && node.hoverEffect > 0.7 && Math.random() < 0.05) {
                 this.createSparkle(node.x, node.y, this.getThemeColors().burst);
            }
        });
    }

    handleMouseClick() {
        this.canvas.addEventListener('click', (event) => {
            this.ripples.push({
                x: event.clientX,
                y: event.clientY,
                currentRadius: 0,
                maxRadius: 80, // Max radius of ripple
                speed: 2,       // How fast radius expands
                life: 60,       // How long ripple lasts (frames)
                opacity: 0.8
            });
        });
    }

    updateRipples() {
        for (let i = this.ripples.length - 1; i >= 0; i--) {
            const ripple = this.ripples[i];
            ripple.currentRadius += ripple.speed;
            ripple.life--;
            ripple.opacity = (ripple.life / 60) * 0.5; // Fade out

            if (ripple.life <= 0 || ripple.currentRadius > ripple.maxRadius) {
                this.ripples.splice(i, 1);
            }
        }
    }

    drawRipples() {
        const colors = this.getThemeColors();
        this.ripples.forEach(ripple => {
            this.ctx.save();
            this.ctx.beginPath();
            this.ctx.arc(ripple.x, ripple.y, ripple.currentRadius, 0, Math.PI * 2);
            this.ctx.strokeStyle = `rgba(${colors.burst}, ${ripple.opacity})`; // Use burst color for ripples
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
            this.ctx.restore();
        });
    }

    createSparkle(x, y, color) {
        const count = Math.floor(Math.random() * 3) + 2; // 2-4 sparkles
        for (let i = 0; i < count; i++) {
            this.sparkles.push({
                x: x,
                y: y,
                size: Math.random() * 2 + 1,
                speedX: (Math.random() - 0.5) * 3,
                speedY: (Math.random() - 0.5) * 3,
                life: Math.random() * 30 + 20, // Short life
                color: color,
                opacity: 1
            });
        }
    }

    updateSparkles() {
        for (let i = this.sparkles.length - 1; i >= 0; i--) {
            const sparkle = this.sparkles[i];
            sparkle.x += sparkle.speedX;
            sparkle.y += sparkle.speedY;
            sparkle.life--;
            sparkle.opacity = sparkle.life / 30; // Fade out

            if (sparkle.life <= 0) {
                this.sparkles.splice(i, 1);
            }
        }
    }

    drawSparkles() {
        this.sparkles.forEach(sparkle => {
            this.ctx.save();
            this.ctx.fillStyle = `rgba(${sparkle.color}, ${sparkle.opacity})`;
            this.ctx.beginPath();
            this.ctx.arc(sparkle.x, sparkle.y, sparkle.size, 0, Math.PI * 2);
            this.ctx.fill();
            this.ctx.restore();
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
            
            if (particle.isBurst && particle.speed > 3) { // Tracer effect for fast burst particles
                this.ctx.beginPath();
                const trailLength = particle.size * 1.5;
                if (particle.direction === 'left-to-right') {
                    this.ctx.moveTo(particle.x - trailLength, particle.y);
                } else {
                    this.ctx.moveTo(particle.x + trailLength, particle.y);
                }
                this.ctx.lineTo(particle.x, particle.y);
                this.ctx.strokeStyle = `rgba(${color}, ${particle.opacity * 0.7})`; // Trail is slightly fainter
                this.ctx.lineWidth = particle.size / 4 > 1 ? particle.size / 4 : 1; // Thin trail
                this.ctx.stroke();
            }
            this.ctx.fillText(particle.char, particle.x, particle.y); // Still draw the character at the head
            
            this.ctx.restore();
        });
    }
    
    drawNodes() {
        const colors = this.getThemeColors();
        
        this.nodes.forEach(node => {
            this.ctx.save();
            
            let pulseIntensity = Math.sin(node.pulse) * 0.5 + 0.5;
            let baseRadius = node.radius;
            let baseOpacity = node.opacity;
            let nodeColor = colors.primary;

            if (node.isHovered) {
                pulseIntensity = Math.max(pulseIntensity, node.hoverEffect * 0.8 + 0.2); // Stronger pulse when hovered
                baseRadius += node.hoverEffect * 3; // Node gets larger
                baseOpacity = Math.min(1, baseOpacity + node.hoverEffect * 0.5); // More opaque
                nodeColor = colors.burst; // Highlight color like burst particles
            }

            const currentRadius = baseRadius + pulseIntensity * 2;
            const currentOpacity = baseOpacity * (0.5 + pulseIntensity * 0.5);
            
            // Draw node
            this.ctx.beginPath();
            this.ctx.arc(node.x, node.y, currentRadius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(${nodeColor}, ${currentOpacity})`;
            this.ctx.shadowColor = `rgba(${nodeColor}, ${currentOpacity})`;
            this.ctx.shadowBlur = node.isHovered ? 25 : 15; // More glow when hovered
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
            let baseConnectionOpacity = connection.opacity;
            let connectionColor = colors.tertiary;
            let lineWidth = 1;

            if (connection.nodeA.isHovered || connection.nodeB.isHovered) {
                const hoverEffect = Math.max(connection.nodeA.hoverEffect || 0, connection.nodeB.hoverEffect || 0);
                baseConnectionOpacity = Math.min(1, baseConnectionOpacity + hoverEffect * 0.7);
                connectionColor = colors.secondary; // Highlight color for connections
                lineWidth = 1 + hoverEffect * 1.5; // Thicker line
            }

            const currentOpacity = baseConnectionOpacity * (0.3 + Math.abs(avgPulse) * 0.4);
            
            this.ctx.beginPath();
            this.ctx.moveTo(connection.nodeA.x, connection.nodeA.y);
            this.ctx.lineTo(connection.nodeB.x, connection.nodeB.y);
            this.ctx.strokeStyle = `rgba(${connectionColor}, ${currentOpacity})`;
            this.ctx.lineWidth = lineWidth;
            this.ctx.shadowColor = `rgba(${connectionColor}, ${currentOpacity * 0.7})`; // Slightly less blur for main line
            this.ctx.shadowBlur = (connection.nodeA.isHovered || connection.nodeB.isHovered) ? 8 : 4;
            this.ctx.stroke();

            // Energy pulse along connection
            const pulsePosition = (Math.sin(Date.now() * 0.001 + connection.pulseOffset * 5) + 1) / 2; // Normalized 0-1 position along line
            const pulseX = connection.nodeA.x + (connection.nodeB.x - connection.nodeA.x) * pulsePosition;
            const pulseY = connection.nodeA.y + (connection.nodeB.y - connection.nodeA.y) * pulsePosition;
            const pulseRadius = lineWidth + 1; // Slightly larger than the line
            const pulseOpacity = currentOpacity * 1.5 > 1 ? 1 : currentOpacity * 1.5; // Brighter pulse

            this.ctx.beginPath();
            this.ctx.arc(pulseX, pulseY, pulseRadius, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(${connectionColor}, ${pulseOpacity})`;
            this.ctx.shadowColor = `rgba(${connectionColor}, ${pulseOpacity})`;
            this.ctx.shadowBlur = pulseRadius * 2;
            this.ctx.fill();
            
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
        this.updateRipples();
        this.updateSparkles(); // Added
        
        this.drawConnections();
        this.drawNodes();
        this.drawParticles();
        this.drawRipples();
        this.drawSparkles(); // Added
        
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

    handleMouseMove() {
        this.canvas.addEventListener('mousemove', (event) => {
            this.mouse.x = event.clientX;
            this.mouse.y = event.clientY;
        });
        this.canvas.addEventListener('mouseleave', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
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