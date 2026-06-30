/**
 * Particles Network Background Effect
 * Interactive particle connection lines
 */
(function() {
  'use strict';

  var canvas = document.createElement('canvas');
  canvas.id = 'particles-canvas';
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;';
  document.body.appendChild(canvas);

  var ctx = canvas.getContext('2d');
  var particles = [];
  var mouseX = 0;
  var mouseY = 0;
  var isMouseMoving = false;
  var mouseTimer = null;

  var CONFIG = {
    particleCount: 60,
    maxDistance: 180,
    particleRadius: 1.5,
    lineWidth: 0.5,
    color1: { r: 108, g: 92, b: 231 },   // #6c5ce7 purple
    color2: { r: 253, g: 121, b: 168 },   // #fd79a8 pink
    speed: 0.2
  };

  // 移动端降低粒子数以优化性能
  if (window.innerWidth < 768) {
    CONFIG.particleCount = 30;
    CONFIG.maxDistance = 120;
    CONFIG.speed = 0.15;
  }

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function random(min, max) {
    return Math.random() * (max - min) + min;
  }

  function createParticle() {
    return {
      x: random(0, canvas.width),
      y: random(0, canvas.height),
      vx: random(-CONFIG.speed, CONFIG.speed),
      vy: random(-CONFIG.speed, CONFIG.speed),
      radius: random(1, CONFIG.particleRadius * 1.5)
    };
  }

  function init() {
    resize();
    particles = [];
    for (var i = 0; i < CONFIG.particleCount; i++) {
      particles.push(createParticle());
    }
    animate();
  }

  function lerpColor(t) {
    return {
      r: Math.round(CONFIG.color1.r + (CONFIG.color2.r - CONFIG.color1.r) * t),
      g: Math.round(CONFIG.color1.g + (CONFIG.color2.g - CONFIG.color1.g) * t),
      b: Math.round(CONFIG.color1.b + (CONFIG.color2.b - CONFIG.color1.b) * t)
    };
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update and draw particles
    for (var i = 0; i < particles.length; i++) {
      var p = particles[i];

      // Move
      p.x += p.vx;
      p.y += p.vy;

      // Boundary bounce
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

      // Draw connections
      for (var j = i + 1; j < particles.length; j++) {
        var q = particles[j];
        var dx = p.x - q.x;
        var dy = p.y - q.y;
        var dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < CONFIG.maxDistance) {
          var alpha = (1 - dist / CONFIG.maxDistance) * 0.3;
          var color = lerpColor(dist / CONFIG.maxDistance);
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = 'rgba(' + color.r + ',' + color.g + ',' + color.b + ',' + alpha + ')';
          ctx.lineWidth = CONFIG.lineWidth * (1 - dist / CONFIG.maxDistance);
          ctx.stroke();
        }
      }

      // Draw particle dot with glow
      var glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius * 3);
      glow.addColorStop(0, 'rgba(108, 92, 231, 0.6)');
      glow.addColorStop(0.5, 'rgba(253, 121, 168, 0.2)');
      glow.addColorStop(1, 'rgba(0, 206, 201, 0)');
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius * 2.5, 0, Math.PI * 2);
      ctx.fillStyle = glow;
      ctx.fill();
      
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
      ctx.fill();
    }

    // Mouse interaction
    if (isMouseMoving) {
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        var dx = p.x - mouseX;
        var dy = p.y - mouseY;
        var dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < CONFIG.maxDistance) {
          var alpha = (1 - dist / CONFIG.maxDistance) * 0.6;
          var color = lerpColor(dist / CONFIG.maxDistance);
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(mouseX, mouseY);
          ctx.strokeStyle = 'rgba(' + color.r + ',' + color.g + ',' + color.b + ',' + alpha + ')';
          ctx.lineWidth = 1.2 * (1 - dist / CONFIG.maxDistance);
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(animate);
  }

  // Mouse event listeners
  document.addEventListener('mousemove', function(e) {
    mouseX = e.clientX;
    mouseY = e.clientY;
    isMouseMoving = true;
    clearTimeout(mouseTimer);
    mouseTimer = setTimeout(function() {
      isMouseMoving = false;
    }, 200);
  });

  // Resize event
  window.addEventListener('resize', function() {
    resize();
  });

  // Start
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
