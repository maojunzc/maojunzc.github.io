/**
 * ClickLove - 点击爱心特效
 * 点击页面任意位置生成彩色浮动爱心
 * 支持移动端触控
 */
(function() {
  'use strict';

  // 注入爱心样式
  var style = document.createElement('style');
  style.textContent =
    '.heart{width:10px;height:10px;position:fixed;transform:rotate(45deg);' +
    'z-index:99999;pointer-events:none;}' +
    '.heart:after,.heart:before{content:\"\";width:inherit;height:inherit;' +
    'background:inherit;border-radius:50%;position:fixed;}' +
    '.heart:after{top:-5px;}' +
    '.heart:before{left:-5px;}';
  document.head.appendChild(style);

  var hearts = [];
  var isAnimating = false;

  function randomColor() {
    var colors = ['#ff6b6b','#ffa94d','#ffd43b','#69db7c','#4dabf7','#9775fa','#f783ac'];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  function createHeart(x, y) {
    var el = document.createElement('div');
    el.className = 'heart';
    el.style.background = randomColor();
    el.style.left = x + 'px';
    el.style.top = y + 'px';
    document.body.appendChild(el);

    hearts.push({
      el: el,
      x: x,
      y: y,
      scale: 1,
      alpha: 1,
      color: randomColor()
    });

    if (!isAnimating) {
      isAnimating = true;
      animate();
    }
  }

  function animate() {
    for (var i = hearts.length - 1; i >= 0; i--) {
      var h = hearts[i];
      h.y -= 1;
      h.scale += 0.004;
      h.alpha -= 0.013;
      h.el.style.cssText =
        'left:' + h.x + 'px;top:' + h.y + 'px;opacity:' + h.alpha + ';' +
        'transform:scale(' + h.scale + ',' + h.scale + ') rotate(45deg);' +
        'background:' + h.color + ';z-index:99999;pointer-events:none;';

      if (h.alpha <= 0) {
        document.body.removeChild(h.el);
        hearts.splice(i, 1);
      }
    }

    if (hearts.length > 0) {
      requestAnimationFrame(animate);
    } else {
      isAnimating = false;
    }
  }

  // 鼠标点击
  document.addEventListener('click', function(e) {
    createHeart(e.clientX - 5, e.clientY - 5);
  });

  // 移动端触摸
  document.addEventListener('touchstart', function(e) {
    var touch = e.touches[0];
    if (touch) {
      createHeart(touch.clientX - 5, touch.clientY - 5);
    }
  }, { passive: true });
})();
