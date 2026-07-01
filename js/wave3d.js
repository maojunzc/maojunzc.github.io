/**
 * Wave3D - 3D 水波动效
 * 使用 Canvas 绘制可交互的 3D 波浪网格
 * 鼠标移动改变波浪视角和扰动
 */
(function() {
  'use strict';

  // ---- 只在 cover 区域显示 ----
  var coverEl = document.querySelector('.cover');
  if (!coverEl) return;

  var canvas = document.createElement('canvas');
  canvas.id = 'wave3d-canvas';
  canvas.style.cssText = 'position:absolute;inset:0;z-index:1;width:100%;height:100%;pointer-events:none;';
  coverEl.appendChild(canvas);

  var ctx = canvas.getContext('2d');
  var W, H;
  var mouseX = 0.5, mouseY = 0.5;
  var time = 0;

  // ---- 3D 波浪参数 ----
  var GRID_SIZE = 30;          // 网格密度
  var SPACING = 20;            // 点间距(px)
  var AMPLITUDE = 18;          // 波幅
  var FREQUENCY = 0.02;        // 波频率
  var SPEED = 0.8;             // 动画速度

  // 视角倾斜参数
  var TILT_X = 0.3;            // X轴倾斜
  var TILT_Y = 0.4;            // Y轴倾斜
  var PERSPECTIVE = 1.2;       // 透视强度

  var cols, rows;

  function resize() {
    W = canvas.width = coverEl.offsetWidth;
    H = canvas.height = coverEl.offsetHeight;

    // 移动端降低质量
    if (W < 768) {
      GRID_SIZE = 18;
      AMPLITUDE = 12;
    } else {
      GRID_SIZE = 30;
      AMPLITUDE = 18;
    }

    // 计算网格
    SPACING = Math.max(W, H) / GRID_SIZE;
    cols = Math.floor(W / SPACING) + 2;
    rows = Math.floor(H / SPACING) + 2;
  }

  function init() {
    resize();
    window.addEventListener('resize', resize);

    // 鼠标交互
    document.addEventListener('mousemove', function(e) {
      var rect = coverEl.getBoundingClientRect();
      mouseX = (e.clientX - rect.left) / rect.width;
      mouseY = (e.clientY - rect.top) / rect.height;
    });

    // 触摸交互（移动端）
    document.addEventListener('touchmove', function(e) {
      var touch = e.touches[0];
      if (touch) {
        var rect = coverEl.getBoundingClientRect();
        mouseX = (touch.clientX - rect.left) / rect.width;
        mouseY = (touch.clientY - rect.top) / rect.height;
      }
    }, { passive: true });

    animate();
  }

  function getHeight(x, y, t) {
    // 多个叠加的正弦波产生复杂水纹效果
    var h = 0;
    h += Math.sin(x * FREQUENCY + t * SPEED) * AMPLITUDE;
    h += Math.sin(y * FREQUENCY * 0.8 + t * SPEED * 0.6) * AMPLITUDE * 0.6;
    h += Math.sin((x + y) * FREQUENCY * 0.5 + t * SPEED * 0.4) * AMPLITUDE * 0.4;
    h += Math.sin((x - y * 0.3) * FREQUENCY * 1.2 + t * SPEED * 0.7) * AMPLITUDE * 0.3;
    return h;
  }

  function animate() {
    time += 0.016; // ~60fps
    ctx.clearRect(0, 0, W, H);

    // ---- 绘制波浪 ----
    var centerX = mouseX * 0.4 + 0.3;
    var centerY = mouseY * 0.3 + 0.4;

    // 画线条（水平方向）
    for (var r = 0; r < rows; r++) {
      ctx.beginPath();
      for (var c = 0; c < cols; c++) {
        var x = c * SPACING;
        var y = r * SPACING;

        // 3D 转换
        var h = getHeight(x, y, time);

        // 透视投影
        var perspectiveFactor = PERSPECTIVE / (PERSPECTIVE + h * 0.01);
        var px = (x - W * centerX) * perspectiveFactor + W * centerX + h * TILT_X;
        var py = (y - H * centerY) * perspectiveFactor + H * centerY + h * TILT_Y - h * 0.5;

        if (c === 0) {
          ctx.moveTo(px, py);
        } else {
          ctx.lineTo(px, py);
        }
      }
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
      ctx.lineWidth = 0.8;
      ctx.stroke();
    }

    // 画线条（垂直方向）
    for (var c = 0; c < cols; c++) {
      ctx.beginPath();
      for (var r = 0; r < rows; r++) {
        var x = c * SPACING;
        var y = r * SPACING;

        var h = getHeight(x, y, time);

        var perspectiveFactor = PERSPECTIVE / (PERSPECTIVE + h * 0.01);
        var px = (x - W * centerX) * perspectiveFactor + W * centerX + h * TILT_X;
        var py = (y - H * centerY) * perspectiveFactor + H * centerY + h * TILT_Y - h * 0.5;

        if (r === 0) {
          ctx.moveTo(px, py);
        } else {
          ctx.lineTo(px, py);
        }
      }
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
      ctx.lineWidth = 0.8;
      ctx.stroke();
    }

    // ---- 画光点（波峰波谷发光） ----
    if (W >= 768) {
      for (var r = 1; r < rows - 1; r += 2) {
        for (var c = 1; c < cols - 1; c += 2) {
          var x = c * SPACING;
          var y = r * SPACING;
          var h = getHeight(x, y, time);

          var perspectiveFactor = PERSPECTIVE / (PERSPECTIVE + h * 0.01);
          var px = (x - W * centerX) * perspectiveFactor + W * centerX + h * TILT_X;
          var py = (y - H * centerY) * perspectiveFactor + H * centerY + h * TILT_Y - h * 0.5;

          // 只画波峰的点
          if (h > AMPLITUDE * 0.5) {
            var brightness = (h - AMPLITUDE * 0.5) / (AMPLITUDE * 0.5);
            ctx.beginPath();
            ctx.arc(px, py, 1.5 + brightness * 2, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(162, 155, 254, ' + (brightness * 0.4) + ')';
            ctx.fill();

            // 外发光
            ctx.beginPath();
            ctx.arc(px, py, 4 + brightness * 6, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(162, 155, 254, ' + (brightness * 0.08) + ')';
            ctx.fill();
          }
        }
      }
    }

    requestAnimationFrame(animate);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
