/**
 * ClickBoom2 - 优雅粒子爆炸特效
 * 点击页面任意位置触发彩色粒子扩散效果
 * 优化版：消除突兀方块，粒子更细腻自然
 */
(function() {
  'use strict';

  // ---- Canvas setup ----
  var canvas = document.createElement('canvas');
  var ctx = canvas.getContext('2d');
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:99999;';
  document.body.appendChild(canvas);

  var W, H;
  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  // ---- Particle pool ----
  var particles = [];
  var COLORS = [
    '#ff6b6b', '#ffa94d', '#ffd43b', '#69db7c',
    '#4dabf7', '#9775fa', '#f783ac', '#20c997'
  ];

  function createParticles(x, y, count) {
    for (var i = 0; i < count; i++) {
      var angle = Math.random() * Math.PI * 2;
      var speed = 2 + Math.random() * 6;
      var size = 2 + Math.random() * 4;
      particles.push({
        x: x,
        y: y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 2,
        life: 1.0,
        decay: 0.012 + Math.random() * 0.02,
        size: size,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        gravity: 0.08 + Math.random() * 0.04
      });
    }
  }

  // ---- Mouse click handler ----
  document.addEventListener('click', function(e) {
    // 移动端减少粒子数
    var count = window.innerWidth < 768 ? 14 : 28;
    createParticles(e.clientX, e.clientY, count);
    if (!animating) {
      animating = true;
      animate();
    }
  });

  // ---- Animation loop ----
  var animating = false;

  function animate() {
    ctx.clearRect(0, 0, W, H);

    for (var i = particles.length - 1; i >= 0; i--) {
      var p = particles[i];

      // Update
      p.x += p.vx;
      p.y += p.vy;
      p.vy += p.gravity;
      p.vx *= 0.98;
      p.life -= p.decay;

      if (p.life <= 0) {
        particles.splice(i, 1);
        continue;
      }

      // Draw with glow
      ctx.globalAlpha = p.life;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();

      // Outer glow
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size * p.life * 2, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.life * 0.2;
      ctx.fill();
    }

    ctx.globalAlpha = 1;

    if (particles.length > 0) {
      requestAnimationFrame(animate);
    } else {
      animating = false;
      ctx.clearRect(0, 0, W, H);
    }
  }
})();
