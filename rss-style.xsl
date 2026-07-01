<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:atom="http://www.w3.org/2005/Atom">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title><xsl:value-of select="atom:feed/atom:title"/> - RSS Feed</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0a0a1a;
      color: #d4d4d4;
      max-width: 720px;
      margin: 0 auto;
      padding: 2rem 1.5rem;
      line-height: 1.6;
    }
    h1 { color: #a29bfe; font-size: 1.8rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem; }
    h1 a { color: #a29bfe; text-decoration: none; }
    .feed-desc { color: rgba(255,255,255,0.5); font-size: 0.9rem; margin-bottom: 2rem; }
    .entry { 
      background: rgba(255,255,255,0.03); 
      border: 1px solid rgba(255,255,255,0.06);
      border-radius: 12px; 
      padding: 1.2rem 1.5rem; 
      margin-bottom: 1rem;
      transition: all 0.3s ease;
    }
    .entry:hover { border-color: rgba(108,92,231,0.3); }
    .entry-title { margin: 0 0 0.3rem; font-size: 1.2rem; }
    .entry-title a { color: #f0f0f0; text-decoration: none; }
    .entry-title a:hover { color: #a29bfe; }
    .entry-meta { color: rgba(255,255,255,0.35); font-size: 0.8rem; }
    .entry-summary { color: rgba(255,255,255,0.6); font-size: 0.9rem; margin-top: 0.5rem; }
    .back { display: inline-block; margin-top: 1.5rem; color: #a29bfe; text-decoration: none; }
    .back:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1><a href="/"><xsl:value-of select="atom:feed/atom:title"/></a></h1>
  <p class="feed-desc">最新文章更新</p>
  
  <xsl:for-each select="atom:feed/atom:entry">
    <div class="entry">
      <h2 class="entry-title">
        <a href="{atom:link[@rel='alternate']/@href}"><xsl:value-of select="atom:title"/></a>
      </h2>
      <p class="entry-meta">
        <xsl:value-of select="substring(atom:published, 1, 10)"/>
        <xsl:text> </xsl:text>
        <xsl:if test="atom:author">
          <xsl:value-of select="atom:author/atom:name"/>
        </xsl:if>
      </p>
      <div class="entry-summary">
        <xsl:value-of select="atom:summary" disable-output-escaping="yes"/>
      </div>
    </div>
  </xsl:for-each>
  
  <a class="back" href="/">← 返回博客</a>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
