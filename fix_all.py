import glob, os

# ===== 1. Rewrite index.html completely =====
index_html = """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
    <title>maojunzc</title>
    <meta name="generator" content="hexo-theme-ayer" />
    <link rel="shortcut icon" href="/favicon.ico" />
    <link rel="stylesheet" href="/dist/main.css" />
    <link rel="stylesheet" href="/css/fonts/remixicon.css" />
    <link rel="stylesheet" href="/css/custom.css" />
    <script src="https://cdn.staticfile.org/pace/1.2.4/pace.min.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@sweetalert2/theme-bulma@5.0.1/bulma.min.css" />
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11.0.19/dist/sweetalert2.min.js"></script>
    <style>.swal2-styled.swal2-confirm { font-size: 1.6rem; }</style>
    <link rel="alternate" href="/atom.xml" title="maojunzc" type="application/atom+xml" />
  </head>
  <body>
    <div id="app">
      <canvas width="1777" height="841" style="position: fixed; left: 0px; top: 0px; z-index: 99999; pointer-events: none;"></canvas>
      <main class="content on">
        <section class="cover">
          <a class="forkMe" href="https://github.com/maojunzc" target="_blank">
            <img width="149" height="149" src="/images/forkme.png" class="attachment-full size-full" alt="Fork me on GitHub" data-recalc-dims="1" />
          </a>
          <div class="cover-frame">
            <div class="bg-box"><img src="/images/cover1.jpg" alt="image frame" /></div>
            <div class="cover-inner text-center text-white">
              <h1><a href="/">maojunzc</a></h1>
              <div id="subtitle-box"><span id="subtitle"></span></div>
              <div></div>
            </div>
          </div>
          <div class="cover-learn-more">
            <a href="javascript:void(0)" class="anchor"><i class="ri-arrow-down-line"></i></a>
          </div>
        </section>

        <script src="https://cdn.staticfile.org/typed.js/2.0.12/typed.min.js"></script>
        <script>
          try {
            var typed = new Typed("#subtitle", {
              strings: ['面向大海，春暖花开', '愿你一生努力，一生被爱', '喜欢就争取，得到就珍惜，错过就忘记'],
              startDelay: 0, typeSpeed: 200, loop: true, backSpeed: 100, showCursor: true
            });
          } catch (err) { console.log(err); }
        </script>

        <div id="main">
          <section class="outer">
            <ul class="ads">
              <li>
                <a target="_blank" rel="noopener" href="http://wpa.qq.com/msgrd?v=3&uin=26198573&site=qq&menu=yes">
                  <img src="https://s1.ax1x.com/2023/02/14/pSoIsmQ.jpg" width="300" alt="maojunzc0" />
                </a>
              </li>
              <li>
                <a target="_blank" rel="noopener" href="https://gitee.com/enterprises?invite_code=Z2l0ZWUtNzkwODYxOA">
                  <img src="https://s1.ax1x.com/2023/02/14/pSoI2Yq.jpg" width="300" alt="maojunzc1" />
                </a>
              </li>
            </ul>

            <div class="notice" style="margin-top:50px">
              <i class="ri-heart-fill"></i>
              <div class="notice-content" id="broad"></div>
            </div>
            <script>
              fetch('https://v1.hitokoto.cn')
                .then(r => r.json())
                .then(d => { document.getElementById("broad").innerHTML = d.hitokoto; })
                .catch(console.error);
            </script>

            <article class="articles">
              <article class="article article-type-page" data-scroll-reveal>
                <div class="article-inner">
                  <header class="article-header">
                    <h2><a class="article-title" href="/about/">欢迎来到 maojunzc 的博客</a></h2>
                  </header>
                  <div class="article-meta">
                    <a class="article-date"><time datetime="2023-02-15">2023-02-15</time></a>
                  </div>
                  <div class="article-entry">
                    <p>这里分享技术教程、软件资源、开发经验和日常生活。</p>
                    <p>可以通过以下方式联系我：</p>
                    <ul>
                      <li>GitHub: <a href="https://github.com/maojunzc">@maojunzc</a></li>
                      <li>QQ: 2316562571</li>
                    </ul>
                  </div>
                </div>
              </article>
            </article>
          </section>
        </div>

        <footer class="footer">
          <div class="outer">
            <ul><li>Copyrights &copy; 2023 <i class="ri-heart-fill heart_icon"></i> maojunzc</li></ul>
            <ul>
              <li>
                <span><i class="ri-user-3-fill"></i>Visitors:<span id="busuanzi_value_site_uv"></span></span>
                <span class="division">|</span>
                <span><i class="ri-eye-fill"></i>Views:<span id="busuanzi_value_page_pv"></span></span>
              </li>
            </ul>
          </div>
        </footer>
        <center>网站已运行 <span id="run_time" style="color:black"></span></center>
        <script>
          function runTime() {
            var d = new Date(), str = '';
            BirthDay = new Date("February 15,2023");
            today = new Date();
            timeold = (today.getTime() - BirthDay.getTime());
            msPerDay = 24 * 60 * 60 * 1000;
            daysold = Math.floor(timeold / msPerDay);
            str += daysold + '\u5929';
            str += d.getHours() + '\u65f6';
            str += d.getMinutes() + '\u5206';
            str += d.getSeconds() + '\u79d2';
            return str;
          }
          setInterval(function() { $('#run_time').html(runTime()); }, 1000);
        </script>
      </main>

      <div class="float_btns">
        <div class="totop" id="totop"><i class="ri-arrow-up-line"></i></div>
        <div class="todark" id="todark"><i class="ri-moon-line"></i></div>
      </div>

      <aside class="sidebar on">
        <button class="navbar-toggle"></button>
        <nav class="navbar">
          <div class="logo"><a href="/"><img src="/images/ayer-side.svg" alt="maojunzc" /></a></div>
          <ul class="nav nav-main">
            <li class="nav-item"><a class="nav-item-link" href="/">首页</a></li>
            <li class="nav-item"><a class="nav-item-link" href="/archives">归档</a></li>
            <li class="nav-item"><a class="nav-item-link" href="/categories">分类</a></li>
            <li class="nav-item"><a class="nav-item-link" href="/tags">标签</a></li>
            <li class="nav-item"><a class="nav-item-link" target="_blank" rel="noopener" href="http://shenyu-vip.lofter.com">相册</a></li>
            <li class="nav-item"><a class="nav-item-link" href="/tags/maojunzc">maojunzc</a></li>
            <li class="nav-item"><a class="nav-item-link" href="/tags/PMP">PMP</a></li>
            <li class="nav-item"><a class="nav-item-link" href="/guestbook">留言板</a></li>
            <li class="nav-item"><a class="nav-item-link" href="/friends">友链</a></li>
            <li class="nav-item"><a class="nav-item-link" href="/about">关于我</a></li>
          </ul>
        </nav>
        <nav class="navbar navbar-bottom">
          <ul class="nav">
            <li class="nav-item">
              <a class="nav-item-link nav-item-search" title="Search"><i class="ri-search-line"></i></a>
              <a class="nav-item-link" target="_blank" href="/atom.xml" title="RSS Feed"><i class="ri-rss-line"></i></a>
            </li>
          </ul>
        </nav>
        <div class="search-form-wrap">
          <div class="local-search local-search-plugin">
            <input type="search" id="local-search-input" class="local-search-input" placeholder="Search..." />
            <div id="local-search-result" class="local-search-result"></div>
          </div>
        </div>
      </aside>
      <div id="mask"></div>

      <div id="reward">
        <span class="close"><i class="ri-close-line"></i></span>
        <p class="reward-p"><i class="ri-cup-line"></i>请我喝杯咖啡吧</p>
        <div class="reward-box">
          <div class="reward-item"><img class="reward-img" src="/images/alipay.jpg" /><span class="reward-type">支付宝</span></div>
          <div class="reward-item"><img class="reward-img" src="/images/wechat.jpg" /><span class="reward-type">微信</span></div>
        </div>
      </div>

      <script src="/js/jquery-3.6.0.min.js"></script>
      <script src="/js/lazyload.min.js"></script>
      <script src="https://cdn.staticfile.org/jquery-modal/0.9.2/jquery.modal.min.js"></script>
      <link rel="stylesheet" href="https://cdn.staticfile.org/jquery-modal/0.9.2/jquery.modal.min.css" />
      <script src="https://cdn.staticfile.org/justifiedGallery/3.8.1/js/jquery.justifiedGallery.min.js"></script>
      <script src="/dist/main.js"></script>

      <div class="pswp" tabindex="-1" role="dialog" aria-hidden="true">
        <div class="pswp__bg"></div>
        <div class="pswp__scroll-wrap">
          <div class="pswp__container"><div class="pswp__item"></div><div class="pswp__item"></div><div class="pswp__item"></div></div>
          <div class="pswp__ui pswp__ui--hidden">
            <div class="pswp__top-bar">
              <div class="pswp__counter"></div>
              <button class="pswp__button pswp__button--close" title="Close (Esc)"></button>
              <button class="pswp__button pswp__button--share" style="display:none" title="Share"></button>
              <button class="pswp__button pswp__button--fs" title="Toggle fullscreen"></button>
              <button class="pswp__button pswp__button--zoom" title="Zoom in/out"></button>
              <div class="pswp__preloader"><div class="pswp__preloader__icn"><div class="pswp__preloader__cut"><div class="pswp__preloader__donut"></div></div></div></div>
            </div>
            <div class="pswp__share-modal pswp__share-modal--hidden pswp__single-tap"><div class="pswp__share-tooltip"></div></div>
            <button class="pswp__button pswp__button--arrow--left" title="Previous (arrow left)"></button>
            <button class="pswp__button pswp__button--arrow--right" title="Next (arrow right)"></button>
            <div class="pswp__caption"><div class="pswp__caption__center"></div></div>
          </div>
        </div>
      </div>

      <link rel="stylesheet" href="https://cdn.staticfile.org/photoswipe/4.1.3/photoswipe.min.css" />
      <link rel="stylesheet" href="https://cdn.staticfile.org/photoswipe/4.1.3/default-skin/default-skin.min.css" />
      <script src="https://cdn.staticfile.org/photoswipe/4.1.3/photoswipe.min.js"></script>
      <script src="https://cdn.staticfile.org/photoswipe/4.1.3/photoswipe-ui-default.min.js"></script>
      <script src="/js/busuanzi-2.3.pure.min.js"></script>
      <script src="/js/clickBoom2.js"></script>

      <link rel="stylesheet" href="/css/clipboard.css" />
      <script src="https://cdn.staticfile.org/clipboard.js/2.0.10/clipboard.min.js"></script>
      <script>
        function wait(callback, seconds) { window.setTimeout(callback, seconds); }
        !function() {
          var copyHtml = '<button class="btn-copy" data-clipboard-snippet=""><i class="ri-file-copy-2-line"></i><span>COPY</span></button>';
          $(".highlight .code pre").before(copyHtml);
          $(".article pre code").before(copyHtml);
          var clipboard = new ClipboardJS('.btn-copy', { target: function(t) { return t.nextElementSibling; } });
          clipboard.on('success', function(e) {
            var btn = $(e.trigger); btn.addClass('copied');
            var icon = btn.find('i'); icon.removeClass('ri-file-copy-2-line').addClass('ri-checkbox-circle-line');
            btn.find('span')[0].innerText = 'COPIED';
            wait(function() { icon.removeClass('ri-checkbox-circle-line').addClass('ri-file-copy-2-line'); btn.find('span')[0].innerText = 'COPY'; }, 2000);
          });
          clipboard.on('error', function(e) {
            e.clearSelection(); var btn = $(e.trigger); btn.addClass('copy-failed');
            var icon = btn.find('i'); icon.removeClass('ri-file-copy-2-line').addClass('ri-time-line');
            btn.find('span')[0].innerText = 'COPY FAILED';
            wait(function() { icon.removeClass('ri-time-line').addClass('ri-file-copy-2-line'); btn.find('span')[0].innerText = 'COPY'; }, 2000);
          });
        }();
      </script>
      <script>if (window.mermaid) { mermaid.initialize({ theme: "forest" }); }</script>
    </div>
  </body>
</html>"""

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(index_html)
print('index.html rewritten - clean')

# ===== 2. Fix corrupted Chinese in all other HTML files =====
html_files = glob.glob('**/*.html', recursive=True)

emoji_fixes = {
    'tv_浜蹭翰': 'tv_亲亲', 'tv_鍋风瑧': 'tv_偷笑',
    'tv_鍐嶈': 'tv_再见', 'tv_鍐锋紶': 'tv_冷漠',
    'tv_鍙戞€': 'tv_发呆', 'tv_鍙戣储': 'tv_发财',
    'tv_鍙埍': 'tv_可爱', 'tv_鍚愯': 'tv_吐血',
    'tv_鍛': 'tv_皱眉', 'tv_鍛曞悙': 'tv_呕吐',
    'tv_鍥': 'tv_困', 'tv_鍧忕瑧': 'tv_坏笑',
    'tv_澶т浆': 'tv_大佬', 'tv_澶у摥': 'tv_大哭',
    'tv_濮斿眻': 'tv_委屈', 'tv_瀹崇緸': 'tv_害羞',
    'tv_灏村艾': 'tv_尴尬', 'tv_寰瑧': 'tv_微笑',
    'tv_鎬濊€': 'tv_思考', 'tv_鎯婂悡': 'tv_惊悚',
    'tv_鎵撹劯': 'tv_打脸', 'tv_鎶撶媯': 'tv_抓狂',
    'tv_鎶犻蓟': 'tv_抠鼻', 'tv_鏂滅溂绗': 'tv_斜眼笑',
    'tv_鏃犲': 'tv_无奈', 'tv_鏅': 'tv_捂脸',
    'tv_娴佹睏': 'tv_流汗', 'tv_娴佹唱': 'tv_流泪',
    'tv_娴侀蓟琛€': 'tv_流鼻血', 'tv_鐐硅禐': 'tv_点赞',
    'tv_鐢熸皵': 'tv_生气', 'tv_鐢熺梾': 'tv_生病',
    'tv_鐤戦棶': 'tv_疑问', 'tv_鐧界溂': 'tv_白眼',
    'tv_鐨辩湁': 'tv_皱眉', 'tv_鐩灙鍙ｅ憜': 'tv_目瞪口呆',
    'tv_鐫＄潃': 'tv_睡着', 'tv_绗戝摥': 'tv_笑哭',
    'tv_鑵艰厗': 'tv_尴尬', 'tv_鑹': 'tv_色',
    'tv_璋冧緝': 'tv_调皮', 'tv_璋冪毊': 'tv_调皮',
    'tv_閯欒': 'tv_鄙视', 'tv_闂槾': 'tv_闭嘴',
    'tv_闅捐繃': 'tv_难过', 'tv_棣': 'tv_香',
    'tv_楝艰劯': 'tv_鬼脸', 'tv_榛戜汉闂彿': 'tv_黑人问号',
    'tv_榧撴帉': 'tv_鼓掌',
}

common_fixes = {
    '缁欐垜鐨勬枃绔犲姞鐐硅瘎璁哄惂~': '给我的文章加点评论吧~',
    'Copyright锛': 'Copyright：',
    '鍒嗕韩': '分享',
    '鎵竴鎵': '扫一扫',
    '鍒嗕韩鍒板井淇': '分享到微信',
    '微信鍒嗕韩浜岀淮鐮': '微信分享二维码',
    '璇勮': '评论',
    'valine璇勮': 'valine评论',
    'Hexo鍥捐〃鎻掍欢': 'Hexo图表插件',
    'cnzz缁熻': 'cnzz统计',
    '/img_url': 'https://via.placeholder.com/800x600',
    'img_caption': 'photo',
}

all_fixes = {}
all_fixes.update(emoji_fixes)
all_fixes.update(common_fixes)

for filepath in html_files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        changed = False
        for old, new in all_fixes.items():
            if old in content:
                content = content.replace(old, new)
                changed = True
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'  Fixed: {filepath}')
    except Exception as e:
        print(f'  Error: {filepath}: {e}')

print('\nAll fixes done!')
