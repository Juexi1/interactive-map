import os, json, re, time, urllib.request, urllib.parse, urllib.error, xml.etree.ElementTree as ET
import hmac, datetime, threading, math, tempfile, subprocess, email.utils
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

NAMES=["The Diary of a CEO","The Joe Rogan Experience","The Rest Is History","The Daily","The Mel Robbins Podcast","Good Hang with Amy Poehler","Crime Junkie","Dateline NBC","The Shawn Ryan Show","This Past Weekend with Theo Von","Up First from NPR","声动早咖啡"]
FEEDS={0:"https://rss2.flightcast.com/xmsftuzjjykcmqwolaqn6mdn",2:"https://feeds.megaphone.fm/GLT4787413333",3:"https://feeds.simplecast.com/Sl5CSM3S",4:"https://feeds.simplecast.com/UCwaTX1J",6:"https://feeds.simplecast.com/qm_9xx0g",9:"https://feeds.megaphone.fm/thispastweekend",10:"https://feeds.npr.org/510318/podcast.xml",11:"https://www.ximalaya.com/album/51076156.xml"}
CACHE={}
AI_DAILY={}
AI_LOCK=threading.Lock()
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 EchoPod/1.0","Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=30) as res:
        data=res.read(48*1024*1024+1)
        if len(data)>48*1024*1024:raise ValueError("RSS feed exceeds 48 MB; cannot parse complete XML")
        return data
def cache(k,fn):
    old=CACHE.get(k)
    if old and time.time()-old[0]<3600:return old[1]
    x=fn();CACHE[k]=(time.time(),x);return x
def local(el,tag):
    for c in el:
        if c.tag.split("}")[-1].lower()==tag.lower():return (c.text or "").strip()
    return ""
def parse(raw, newest_first=False):
    root=ET.fromstring(raw)
    items=root.findall("./channel/item")
    if newest_first:
        def published(item):
            try:
                parsed=email.utils.parsedate_to_datetime(local(item,"pubDate"))
                return parsed.timestamp()
            except (ValueError,TypeError,OverflowError):
                return 0
        items.sort(key=published,reverse=True)
    output=[]
    for item in items[:35]:
        url=""
        for e in item.iter():
            if e.tag.split("}")[-1]=="enclosure":
                url=e.get("url","")
                if url:break
        transcripts=[]
        for e in item.iter():
            if e.tag.split("}")[-1]=="transcript":
                link=e.get("url",""); fmt=e.get("type","")
                if link.startswith("https://") and fmt in ("text/vtt","application/x-subrip","application/srt","text/plain"):
                    transcripts.append({"url":link,"type":fmt,"language":e.get("language","")})
        duration=local(item,"duration")
        if url and url.startswith("https://"):output.append({"duration":duration,"title":local(item,"title"),"date":local(item,"pubDate"),"audio":url,"description":re.sub("<[^>]+>"," ",local(item,"description"))[:260],"transcripts":transcripts})
    return output
def episodes(i):
    errors=[]; feed=FEEDS.get(i)
    if not feed:
        try:
            u="https://itunes.apple.com/search?"+urllib.parse.urlencode({"term":NAMES[i],"entity":"podcast","limit":8})
            data=json.loads(fetch(u)); results=data.get("results",[])
            target=NAMES[i].lower().replace(" with theo von","")
            results.sort(key=lambda x: int(target in x.get("collectionName","").lower()),reverse=True)
            feed=results[0].get("feedUrl") if results else None
        except Exception as e:errors.append("Podcast directory: "+str(e))
    if feed:
        try:
            out=cache("rss-v4:"+feed,lambda:parse(fetch(feed),newest_first=(i==11)))
            if out:return {"episodes":out,"feed":feed,"errors":errors}
            errors.append("RSS contained no playable audio")
        except Exception as e:errors.append("RSS: "+str(e))
    return {"episodes":[],"errors":errors}
HTML=r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0c1014"><title>EchoPod — Listen beyond the noise</title><link rel="manifest" href="/manifest.webmanifest"><link rel="preconnect" href="https://is1-ssl.mzstatic.com"><style>
:root{--bg:#0c1014;--panel:#161e24;--border:#29333b;--fg:#f7f8f8;--soft:#9eabb5;--mint:#b6f26a;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--fg);background:var(--bg)}*{box-sizing:border-box}body{margin:0;padding-bottom:182px}button{font:inherit;cursor:pointer}.shell{max-width:1270px;padding:32px 35px;margin:auto}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:50px}.logo{font-size:25px;letter-spacing:-1.3px;font-weight:850}.logo span{color:var(--mint)}.topright{font-size:12px;border:1px solid #364249;border-radius:30px;padding:9px 14px;color:var(--soft)}.dot{display:inline-block;background:var(--mint);width:7px;height:7px;border-radius:50%;margin-right:7px}.eyebrow{letter-spacing:2px;color:var(--mint);font-size:12px;font-weight:750;margin-bottom:13px}.hero{display:flex;justify-content:space-between;align-items:end;gap:20px}.hero h1{font-size:clamp(36px,6vw,70px);letter-spacing:-3.5px;line-height:1.06;margin:0 0 17px;font-weight:850}.hero p{color:var(--soft);max-width:490px;line-height:1.6;font-size:15px;margin:0}.pill{border:0;color:#0c1014;background:var(--mint);padding:15px 22px;border-radius:40px;font-size:14px;font-weight:800;white-space:nowrap}.pill:hover{background:#d4ff9b}.sectionhead{display:flex;justify-content:space-between;align-items:center;margin:55px 0 22px}.sectionhead h2{font-size:23px;letter-spacing:-.7px;margin:0}.subtle{color:var(--soft);font-size:12px}.grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px}.tile{border:1px solid transparent;background:transparent;text-align:left;padding:0;color:var(--fg);border-radius:15px;min-width:0}.tile.active .art{outline:2px solid var(--mint);outline-offset:3px}.art{width:100%;aspect-ratio:1;border-radius:14px;background:linear-gradient(135deg,#2e404c,#182329);object-fit:cover;display:block}.art-wrap{position:relative}.number{position:absolute;top:9px;left:9px;background:#10171dd9;color:#fff;border-radius:8px;padding:5px 9px;font-size:12px;font-weight:750}.faux{display:grid;place-items:center;font-size:50px;color:#c1e09b;font-weight:900}.tile .name{font-size:14px;font-weight:750;line-height:1.4;margin:12px 0 5px}.tile .cat{color:var(--soft);font-size:12px}.focus{background:linear-gradient(130deg,#1c2930,#11191e);border:1px solid var(--border);border-radius:22px;padding:25px;display:flex;gap:28px;align-items:center}.focus-cover{width:165px;height:165px;flex-shrink:0;object-fit:cover;border-radius:14px;background:#30424b}.focus h3{font-size:clamp(22px,3vw,32px);margin:8px 0;letter-spacing:-1px}.focus p{color:var(--soft);font-size:13px;line-height:1.6}#episodes{min-height:440px;overflow-anchor:none}.grid,.focus{overflow-anchor:none}html{scroll-behavior:auto}.line{height:1px;background:var(--border);margin:32px 0 10px}.episode{display:flex;align-items:center;padding:16px 0;gap:16px;border-bottom:1px solid #283039}.episode .n{color:#71848d;font-size:12px;width:22px;flex-shrink:0}.episode .details{flex:1;min-width:0}.episode .title{font-size:14px;font-weight:700;line-height:1.5}.episode .meta{font-size:12px;color:var(--soft);margin-top:5px}.epbtn{border:1px solid #526167;background:transparent;color:#fff;border-radius:50%;width:38px;height:38px;flex-shrink:0;font-size:14px}.epbtn:hover{color:#111;background:var(--mint)}.error{color:#ffb9a8;line-height:1.6}.footer{position:fixed;bottom:0;left:0;right:0;z-index:10;background:#182228f5;border-top:1px solid #2e4148;padding:14px max(20px,calc((100vw - 1200px)/2))}.now{display:flex;align-items:center;gap:10px;font-size:12px;margin-bottom:7px;color:var(--soft)}.now b{color:#fff;font-size:13px;white-space:nowrap;text-overflow:ellipsis;overflow:hidden;max-width:85vw}audio{width:100%;height:35px;accent-color:var(--mint)}.footer a{color:var(--mint)}@media(max-width:850px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}.shell{padding:24px 19px}.top{margin-bottom:37px}.hero{align-items:start;flex-direction:column}.hero h1{letter-spacing:-2px}.sectionhead{margin-top:40px}.focus-cover{height:105px;width:105px}.focus{padding:15px;gap:16px}}@media(max-width:500px){body{overflow-anchor:none;-webkit-text-size-adjust:100%}.footer{background:#182228;backdrop-filter:none;-webkit-backdrop-filter:none;transform:translateZ(0)}.tile{-webkit-tap-highlight-color:transparent;touch-action:manipulation}.art,.focus-cover{content-visibility:visible}.focus{min-height:128px}#episodes{min-height:460px}.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 13px}.focus-cover{height:95px;width:95px}.focus h3{font-size:21px}.tile .name{font-size:13px}.art{border-radius:11px}.faux{font-size:37px}.hero h1{font-size:44px}}


/* EchoPod immersive player */
body{background:radial-gradient(ellipse at 70% -15%,#26383e 0%,#0b141a 43%,#090e14 100%);color:#f5f6f7}
.tile .art{border-radius:15px;box-shadow:0 14px 34px #0007}.tile{transition:transform .25s ease}.tile:hover{transform:translateY(-5px)}
.focus{background:linear-gradient(125deg,#28353e,#131d25);border:1px solid #ffffff16;border-radius:23px;box-shadow:0 16px 60px #0003}
.episode{border-bottom:1px solid #ffffff14}.episode:hover{background:#ffffff0b}
.footer{padding:10px 20px 12px!important;background:#171d24ef!important;border-top:1px solid #ffffff2c!important;box-shadow:0 -12px 55px #0008;z-index:90}
.footer .now,.footer>audio,.footer>div:not(#minibar){display:none!important}
#minibar{display:flex;align-items:center;gap:13px;max-width:950px;margin:auto;cursor:pointer;padding:4px 0}
#miniArt{width:49px;height:49px;object-fit:cover;border-radius:10px;background:#29343b;box-shadow:0 5px 17px #0007}
#miniTitle{font-weight:700;font-size:13px;white-space:nowrap;text-overflow:ellipsis;overflow:hidden}
#miniShow{color:#a8adb5;font-size:11px;margin-top:3px}
#miniPlay{border:0;background:transparent;color:white;font-size:24px;min-width:44px;cursor:pointer}
#playerOverlay{position:fixed;inset:0;z-index:200;background:linear-gradient(150deg,#28363b 0%,#171f28 40%,#0b1018 100%);display:none;overflow:auto;color:#fafafa;padding:env(safe-area-inset-top) 0 env(safe-area-inset-bottom)}
#playerOverlay.open{display:block}
#playerShell{max-width:680px;margin:auto;padding:22px 25px 60px}
#closePlayer{border:0;background:#ffffff18;border-radius:999px;color:#fff;width:42px;height:42px;font-size:22px;cursor:pointer}
#playerArtwork{width:min(65vw,300px);aspect-ratio:1;object-fit:cover;border-radius:19px;box-shadow:0 25px 55px #0009;display:block;margin:12px auto 27px}
#playerHeading{font-size:23px;letter-spacing:-.6px;line-height:1.2}
#playerShow{color:#b7bec8;margin-top:7px;font-size:13px}
#playerProgress{width:100%;accent-color:#f8f8fa;margin-top:26px}
#playerControls{display:flex;align-items:center;justify-content:space-between;margin:15px auto 28px;max-width:310px}
#playerControls button{border:0;background:none;color:#fff;font-size:27px;cursor:pointer;padding:9px}
#playerControls #fullPlay{font-size:42px}
#lyricsView{background:#ffffff0b;border:1px solid #ffffff19;border-radius:23px;padding:23px 18px;min-height:210px;max-height:43vh;overflow:auto;scroll-behavior:smooth}
#lyricsView .lyric{font-size:clamp(18px,4.8vw,25px);font-weight:700;line-height:1.38;color:#ffffff66;padding:10px 3px;cursor:pointer;transition:color .2s}
#lyricsView .lyric.current{color:#fff}
#lyricsView .lyric:hover{color:#ffffffcc}
#lyricsView .placeholder{color:#c7cbd0;font-size:16px;line-height:1.6}
#fullGenerate{background:#fff;color:#111822;border:0;border-radius:999px;padding:12px 17px;font-weight:750;cursor:pointer}
#fullCaptionStatus{font-size:12px;color:#b9c3ca}
#playerOverlay .barline{display:flex;align-items:center;justify-content:space-between;gap:12px}
@media(max-width:600px){#playerShell{padding:14px 22px 50px}#playerArtwork{width:min(63vw,270px)}#lyricsView{max-height:41vh}body{padding-bottom:80px}}
#albumPage{animation:albumEnter .25s ease}#albumPage .focus{margin-top:3px}#albumPage .sectionhead{margin-top:27px!important}@keyframes albumEnter{from{opacity:.4;transform:translateX(14px)}to{opacity:1;transform:translateX(0)}}body.album-mode .hero,body.album-mode #grid,body.album-mode .library-heading{display:none!important}body.album-mode #albumPage{display:block!important}@media(max-width:600px){.shell{padding-top:max(28px,env(safe-area-inset-top))!important}.top{padding-top:10px}#albumPage .focus{display:flex;flex-direction:column;align-items:center;text-align:center}#albumPage .focus-cover{height:190px;width:190px;border-radius:18px;box-shadow:0 18px 35px #0008}#albumPage .focus h3{font-size:29px}}

/* Refined transitions and accessible bold controls */
:root{--ease-smooth:cubic-bezier(.22,1,.36,1)}
#albumPage{animation:albumSlide .44s var(--ease-smooth) both}
@keyframes albumSlide{from{opacity:0;transform:translate3d(28px,0,0) scale(.985)}to{opacity:1;transform:translate3d(0,0,0) scale(1)}}
#grid .tile{transition:transform .32s var(--ease-smooth),filter .25s ease}
#grid .tile:active{transform:scale(.96)}
#playerOverlay{display:block!important;visibility:hidden;opacity:0;pointer-events:none;transform:translate3d(0,42px,0) scale(.985);transition:opacity .32s ease,transform .48s var(--ease-smooth),visibility 0s linear .48s;will-change:transform,opacity}
#playerOverlay.open{visibility:visible;opacity:1;pointer-events:auto;transform:translate3d(0,0,0) scale(1);transition:opacity .28s ease,transform .45s var(--ease-smooth),visibility 0s}
#playerArtwork{transition:transform .45s var(--ease-smooth)}
#playerOverlay.open #playerArtwork{animation:coverRise .55s var(--ease-smooth) both}
@keyframes coverRise{from{transform:translateY(17px) scale(.94);opacity:.5}to{transform:translateY(0) scale(1);opacity:1}}
#miniPlay,#fullPlay,#closePlayer,#playerControls button{display:inline-flex;align-items:center;justify-content:center;transition:transform .15s ease,background .2s}
#miniPlay:active,#fullPlay:active,#closePlayer:active,#playerControls button:active{transform:scale(.88)}
#miniPlay{width:46px;height:46px;min-width:46px;border-radius:50%;background:#ffffff12;font-size:0}
#fullPlay{width:80px;height:80px;border-radius:50%;background:#fff!important;color:#13171d!important;font-size:0!important;box-shadow:0 8px 28px #0005}
#closePlayer{background:#ffffff25;width:46px;height:46px}
#playerControls button:not(#fullPlay){background:#ffffff12;border-radius:50%;min-width:58px;min-height:58px;font-weight:800;font-size:20px}
#miniPlay svg{width:23px;height:23px}#fullPlay svg{width:35px;height:35px}#closePlayer svg{width:24px;height:24px}
#playerProgress{height:7px;cursor:pointer}
#lyricsView .lyric{transition:color .28s ease,transform .28s var(--ease-smooth);transform-origin:left center}
#lyricsView .lyric.current{transform:scale(1.035)}
@media(prefers-reduced-motion:reduce){#playerOverlay,#albumPage,#playerArtwork,.tile,.lyric{animation:none!important;transition:none!important}}

.librarySearch{display:flex;align-items:center;gap:12px;background:#ffffff0c;border:1px solid #ffffff1f;padding:0 16px;border-radius:15px;margin:17px 0 22px;color:#b4bbc2;font-size:25px}
.librarySearch:focus-within{border-color:#d0fa9b66;background:#ffffff12}
.librarySearch input{width:100%;font:inherit;font-size:15px;border:none;outline:none;background:transparent;color:#fff;padding:15px 0;min-height:50px}
.librarySearch input::placeholder{color:#87939e}
body.album-mode .librarySearch{display:none}
#grid .tile[hidden]{display:none!important}
.episode{cursor:pointer;transition:background .16s ease,transform .18s ease}
.episode:active{background:#ffffff16;transform:scale(.993)}
.episode:focus-visible{outline:2px solid #caf498;outline-offset:3px}
.speedRow{display:flex;justify-content:space-between;align-items:center;color:#adb8c1;font-size:13px;margin:-8px 0 23px}
#speedBtn{border-radius:12px;padding:9px 18px;color:#fff;background:#ffffff19;border:1px solid #ffffff20;font-size:15px;font-weight:800;min-width:65px}
#speedBtn:active{transform:scale(.94)}
.footer{padding-bottom:max(13px,env(safe-area-inset-bottom))!important}
body{padding-bottom:110px}
@media(max-width:600px){.hero{padding-top:max(26px,env(safe-area-inset-top))}.hero h1{font-size:clamp(35px,10vw,49px)}.librarySearch{margin-top:13px}}
.favBar{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}.favBar button,.favAction{border:1px solid #ffffff2c;background:#ffffff13;color:#f5f5f5;border-radius:999px;padding:11px 15px;font-weight:750;font-size:13px;cursor:pointer}.favBar button:active,.favAction:active{transform:scale(.96)}.favAction{margin-top:13px;background:#c0f69b20;color:#d0ffa6}.favBar #resumeBtn{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}body.album-mode .favBar{display:none}
/* Refined black mini-player and responsive now-playing stage */
.footer{background:#000!important;background-image:none!important;border-top:1px solid #242424!important;box-shadow:0 -10px 35px #0008!important;color:#f8f8f8!important}
#minibar{max-width:1180px;min-height:56px}
#miniCover{width:52px;height:52px;flex:none;overflow:hidden;border-radius:12px;background:#252525;display:grid;place-items:center}
#miniCover #miniArt{width:100%;height:100%;object-fit:cover;border-radius:0}
#miniFallback{width:100%;height:100%;display:grid;place-items:center;font-size:25px;font-weight:800;color:#eee}
#miniTitle{color:#f8f8f8!important;font-weight:750}
#miniShow{color:#a2a2a7!important}
#miniPlay{background:#292929!important;color:#fff}
#playerShell{max-width:700px}
#playerLeft,#playerRight{min-width:0}
#playerArtwork{max-width:100%;height:auto}
@media(min-width:800px){
#playerShell{max-width:1230px;min-height:100vh;padding:30px clamp(30px,5vw,80px) 60px;display:grid;grid-template-columns:minmax(280px,460px) minmax(360px,1fr);grid-template-rows:auto 1fr;column-gap:clamp(35px,5vw,88px);align-items:start}
#playerShell>.barline:first-child{grid-column:1/-1;margin-bottom:28px}
#playerLeft{grid-column:1;grid-row:2;position:sticky;top:60px}
#playerRight{grid-column:2;grid-row:2;align-self:stretch;display:flex;flex-direction:column;min-height:560px}
#playerArtwork{width:min(100%,400px);margin:0 auto 30px}
#playerHeading{font-size:clamp(25px,2.4vw,37px);line-height:1.14}
#playerShow{font-size:15px}
#lyricsView{flex:1;max-height:calc(100vh - 190px);min-height:390px;padding:25px 30px}
#lyricsView .lyric{font-size:clamp(20px,2vw,29px);line-height:1.5}
#playerControls{max-width:360px}
}
@media(min-width:800px) and (max-width:1040px){
#playerShell{grid-template-columns:minmax(260px,.85fr) minmax(320px,1fr);column-gap:30px;padding-inline:28px}
#playerRight{min-height:500px}#lyricsView{padding:17px;max-height:calc(100vh - 160px)}
}
@media(max-width:799px){#playerShell{width:100%;max-width:640px;padding-inline:clamp(17px,5vw,36px)}#playerLeft,#playerRight{width:100%}#playerArtwork{width:min(60vw,300px)}}
@media(prefers-reduced-motion:reduce){#playerOverlay,#playerArtwork{transition:none!important;animation:none!important}}
</style></head><body><main class="shell"><header class="top"><div class="logo">echo<span>pod.</span></div><div class="topright"><span class="dot"></span>YOUR DAILY LISTEN</div></header><section class="hero"><div><div class="eyebrow">DISCOVER · LISTEN · REPEAT</div><h1>Good morning.<br>Great listening.</h1><p>Discover the world's most talked-about podcasts. Fresh perspectives, brilliant conversations, and stories worth your time.</p></div><button class="pill" onclick="morning()">▶ &nbsp; Start morning listen</button></section><div class="sectionhead library-heading"><h2>Global Top 10 + Morning Picks</h2><span class="subtle">Curated chart snapshot ↗</span></div><div class="favBar"><button id="favFilter" onclick="toggleFavoritesFilter()">♡ Favorites</button><button id="resumeBtn" onclick="resumeListening()" style="display:none">↺ Continue listening</button></div><div class="librarySearch"><span aria-hidden="true">⌕</span><input id="podcastSearch" type="search" placeholder="Search your podcasts" aria-label="Search podcasts" oninput="filterPodcasts(this.value)"></div><div id="grid" class="grid"></div><section id="albumPage" style="display:none"><button id="albumBack" onclick="closeAlbum()" style="border:0;background:#ffffff15;color:#fff;padding:11px 17px;border-radius:999px;margin:8px 0 25px;font-weight:700">‹ Back to Library</button><div class="sectionhead"><h2>Now exploring</h2><span id="loading" class="subtle">Select a podcast</span></div><section class="focus"><img id="focusArt" class="focus-cover" alt="Podcast cover"><div><div class="eyebrow">FEATURED PODCAST</div><h3 id="focusName">The Daily</h3><p id="focusDesc">Latest episodes and stories, ready to play.</p><div class="subtle" id="count"></div><button id="favoriteAlbum" onclick="toggleFavorite(chosen)" class="favAction">♡ Add to favorites</button></div></section><div class="sectionhead" style="margin-top:36px"><h2>Latest episodes</h2><span class="subtle">PLAY ANY EPISODE</span></div><div id="episodes"></div></section><p class="subtle" style="margin-top:30px">Podcast artwork is provided by publishers and directory listings. <a style="color:var(--mint)" href="/api/diagnostics" target="_blank">Connection diagnostics</a></p></main><footer class="footer"><div id="minibar" onclick="openPlayer()"><div id="miniCover"><img id="miniArt" alt="" style="display:none"><span id="miniFallback" aria-hidden="true">♫</span></div><div style="min-width:0;flex:1"><div id="miniTitle">EchoPod</div><div id="miniShow">Choose a podcast to start listening</div></div><button id="miniPlay" onclick="event.stopPropagation();togglePlayback()" aria-label="Play or pause">▶</button><span style="color:#c7cbd0;font-size:20px">⌃</span></div><audio id="audio" controls playsinline preload="none" style="display:none"></audio><span id="playing" style="display:none"></span><span id="captionText" style="display:none">Choose an episode</span><button id="generateBtn" style="display:none"></button><button id="captionBtn" style="display:none"></button><button id="transcriptBtn" style="display:none"></button><div id="transcriptPanel" style="display:none"><div id="transcriptLines"></div></div></footer><div id="playerOverlay" role="dialog" aria-label="Now Playing"><div id="playerShell"><div class="barline"><button id="closePlayer" onclick="closePlayer()" aria-label="Close player">⌄</button><div style="font-size:12px;font-weight:750;letter-spacing:2px">NOW PLAYING</div><span style="width:42px"></span></div><div id="playerLeft"><img id="playerArtwork" alt="Podcast album artwork"><div id="playerHeading">Choose an episode</div><div id="playerShow">EchoPod</div><input id="playerProgress" type="range" min="0" max="100" value="0" oninput="seekPlayback(this.value)" aria-label="Playback position"><div class="barline" style="color:#aeb8c2;font-size:12px"><span id="elapsed">0:00</span><span id="duration">0:00</span></div><div id="playerControls"><button onclick="skipAudio(-15)" aria-label="Back 15 seconds">↶15</button><button id="fullPlay" onclick="togglePlayback()" aria-label="Play or pause">▶</button><button onclick="skipAudio(30)" aria-label="Forward 30 seconds">30↷</button></div><div class="speedRow"><span>Playback speed</span><button id="speedBtn" onclick="cycleSpeed()" aria-label="Change playback speed">1×</button></div></div><div id="playerRight"><div class="barline" style="margin:4px 0 14px"><div><div style="font-weight:800;font-size:18px">Lyrics & Captions</div><div id="fullCaptionStatus">Synchronized podcast transcript</div></div><button id="fullGenerate" onclick="generateAI()">Generate AI subtitles</button></div><div id="lyricsView"><div class="placeholder">Select an episode to see captions. Tap “Generate AI subtitles” if the publisher did not provide them.</div></div></div></div></div><script>

const names=__SHOWS__;const types=['Business · Interviews','Conversation · Culture','History','Daily News','Self Improvement','Comedy · Interviews','True Crime','True Crime · News','Conversations','Comedy · Interviews','Daily News · NPR','Business & Tech · 中文'];let art=names.map(()=>''), links=names.map(()=>''),chosen=3, latest=[], selectionToken=0, allEpisodes=Array(names.length).fill(null), allPromise=null;
const $=id=>document.getElementById(id);
const FAVORITES_KEY='echopod-favorites-v1',PROGRESS_KEY='echopod-playback-v1';
let favorites=[],favoritesOnly=false,lastSavedAt=0;
try{favorites=JSON.parse(localStorage.getItem(FAVORITES_KEY)||'[]').filter(x=>Number.isInteger(x)&&x>=0&&x<names.length)}catch(e){}
function updateFavButton(){const b=$('favoriteAlbum');if(b)b.textContent=favorites.includes(chosen)?'♥ Favorited':'♡ Add to favorites';const f=$('favFilter');if(f)f.textContent=favoritesOnly?'♥ Favorites · On':'♡ Favorites'}
function toggleFavorite(i){favorites=favorites.includes(i)?favorites.filter(x=>x!==i):[...favorites,i];localStorage.setItem(FAVORITES_KEY,JSON.stringify(favorites));updateFavButton();filterPodcasts($('podcastSearch').value)}
function toggleFavoritesFilter(){favoritesOnly=!favoritesOnly;updateFavButton();filterPodcasts($('podcastSearch').value)}
function readProgress(){try{return JSON.parse(localStorage.getItem(PROGRESS_KEY)||'null')}catch(e){return null}}
function saveProgress(){const a=$('audio');if(!a.src||!activeEpisode||activeShow===null)return;const state={show:activeShow,episode:activeEpisode.index,audio:a.currentSrc||a.src,time:a.currentTime||0,title:$('playerHeading').textContent,updated:Date.now()};try{localStorage.setItem(PROGRESS_KEY,JSON.stringify(state))}catch(e){}showResume()}
function showResume(){const p=readProgress(),b=$('resumeBtn');if(b){b.style.display=p&&p.audio?'inline-flex':'none';if(p)b.textContent='↺ Continue · '+p.title}}
async function resumeListening(){const p=readProgress();if(!p)return;await select(p.show);const e=latest.find(x=>x.audio===p.audio);if(!e){alert('This episode is no longer available in the feed.');return}playEpisode(e,p.time)}

function filterPodcasts(text){const q=text.toLocaleLowerCase().trim();document.querySelectorAll('#grid .tile').forEach((tile,i)=>{tile.hidden=(favoritesOnly&&!favorites.includes(i))||(!!q&&!((names[i]+' '+types[i]).toLocaleLowerCase().includes(q)))})}
const SPEEDS=[1,1.25,1.5,1.75,2,.75];let speedIndex=0;
function cycleSpeed(){speedIndex=(speedIndex+1)%SPEEDS.length;$('audio').playbackRate=SPEEDS[speedIndex];$('speedBtn').textContent=SPEEDS[speedIndex]+'×'}


const iconPlay='<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 4.5c0-1.1 1.2-1.8 2.2-1.2l11 7c1.2.8 1.2 2.6 0 3.4l-11 7C9.2 21.3 8 20.6 8 19.5z"/></svg>';
const iconPause='<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="5" y="3" width="5.5" height="18" rx="1.4"/><rect x="13.5" y="3" width="5.5" height="18" rx="1.4"/></svg>';
const iconDown='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 9 7 7 7-7"/></svg>';
let playerShown=false,currentPlayingTitle='',currentPlayingShow='';
function openPlayer(){if(!$('audio').src)return;playerShown=true;$('playerOverlay').classList.add('open');document.body.style.overflow='hidden';refreshLyrics()}
function closePlayer(){playerShown=false;$('playerOverlay').classList.remove('open');document.body.style.overflow=''}
function togglePlayback(){const a=$('audio');if(!a.src)return;if(a.paused)a.play().catch(()=>{});else a.pause();syncButtons()}
function syncButtons(){const v=$('audio').paused?iconPlay:iconPause;$('miniPlay').innerHTML=v;$('fullPlay').innerHTML=v}
function skipAudio(seconds){const a=$('audio');a.currentTime=Math.max(0,Math.min(a.duration||Infinity,a.currentTime+seconds))}
function seekPlayback(pct){const a=$('audio');if(a.duration)a.currentTime=Number(pct)*a.duration/100}
function fmtTime(t){if(!Number.isFinite(t))return '0:00';return Math.floor(t/60)+':'+String(Math.floor(t%60)).padStart(2,'0')}
function refreshLyrics(){const view=$('lyricsView');view.replaceChildren();if(!activeCues.length){const el=document.createElement('div');el.className='placeholder';el.textContent=$('captionText').textContent||'AI subtitles not generated yet.';view.append(el);return}const frag=document.createDocumentFragment();activeCues.forEach((cue,index)=>{const el=document.createElement('div');el.className='lyric';el.textContent=cue.text;el.dataset.cue=index;el.onclick=()=>{$('audio').currentTime=cue.start};frag.append(el)});view.append(frag);syncLyrics()}
let previousLyric=-1;
function syncLyrics(){if(!playerShown||!activeCues.length)return;const t=$('audio').currentTime;let i=activeCues.findIndex(c=>t>=c.start&&t<c.end);if(i<0)i=activeCues.findIndex(c=>c.start>t);if(i<0)i=activeCues.length-1;if(i===previousLyric)return;previousLyric=i;const prev=$('lyricsView').querySelector('.current');if(prev)prev.classList.remove('current');const line=$('lyricsView').children[i];if(line){line.classList.add('current');line.scrollIntoView({block:'center',behavior:'smooth'})}}
$('audio').addEventListener('play',syncButtons);$('audio').addEventListener('pause',syncButtons);
$('audio').addEventListener('timeupdate',()=>{const a=$('audio');$('elapsed').textContent=fmtTime(a.currentTime);$('duration').textContent=fmtTime(a.duration);$('playerProgress').value=a.duration?100*a.currentTime/a.duration:0;syncLyrics()});
$('audio').addEventListener('loadedmetadata',()=>{$('duration').textContent=fmtTime($('audio').duration)});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&playerShown)closePlayer()});syncButtons();$('closePlayer').innerHTML=iconDown;


const CACHE_KEY='echopod-v6-local-cache';
function saveLocal(){try{localStorage.setItem(CACHE_KEY,JSON.stringify({art,links,allEpisodes,updated:Date.now()}))}catch(e){}}
function restoreLocal(){try{const d=JSON.parse(localStorage.getItem(CACHE_KEY)||'null');if(!d)return false;if(Array.isArray(d.art)&&d.art.length===names.length)art=d.art;if(Array.isArray(d.links)&&d.links.length===names.length)links=d.links;if(Array.isArray(d.allEpisodes)&&d.allEpisodes.length===names.length)allEpisodes=d.allEpisodes;return true}catch(e){return false}}
function refreshCoverNodes(){if(activeShow!==null&&art[activeShow]){$('miniArt').src=art[activeShow];$('miniArt').style.display='block';$('miniFallback').style.display='none';$('playerArtwork').src=art[activeShow]}document.querySelectorAll('#grid .tile').forEach((tile,i)=>{if(!art[i])return;const img=tile.querySelector('img.art');if(img&&img.getAttribute('src')!==art[i]){img.src=art[i];img.style.display='block';const fallback=tile.querySelector('.faux');if(fallback)fallback.remove()}});setFocus()}
function applyEpisodes(d){const token=++selectionToken;latest=d.episodes||[];$('episodes').replaceChildren();if(!latest.length){$('loading').textContent='No episodes available';return}$('loading').textContent='Ready to play';$('count').textContent=latest.length+' available episodes';latest.forEach((e,j)=>{const row=document.createElement('div');row.className='episode';const idx=document.createElement('div');idx.className='n';idx.textContent=String(j+1).padStart(2,'0');const info=document.createElement('div');info.className='details';const t=document.createElement('div');t.className='title';t.textContent=e.title;const m=document.createElement('div');m.className='meta';m.textContent=e.date||'Latest episode';info.append(t,m);const play=document.createElement('button');play.className='epbtn';play.textContent='▶';play.setAttribute('aria-label','Play '+e.title);play.onclick=ev=>{ev.stopPropagation();playEpisode(e)};row.onclick=()=>playEpisode(e);row.tabIndex=0;row.setAttribute('role','button');row.setAttribute('aria-label','Play '+e.title);row.onkeydown=ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();playEpisode(e)}};row.append(idx,info,play);$('episodes').append(row)})}

function draw(){const g=$('grid');g.replaceChildren();names.forEach((name,i)=>{const b=document.createElement('button');b.className='tile'+(i===chosen?' active':'');const w=document.createElement('div');w.className='art-wrap';const cover=document.createElement('img');cover.className='art';cover.alt=name+' podcast cover';cover.loading='lazy';if(art[i])cover.src=art[i];else{cover.style.display='none';const fallback=document.createElement('div');fallback.className='art faux';fallback.textContent=name.slice(0,1);w.appendChild(fallback)}cover.onerror=()=>{cover.style.display='none';if(!w.querySelector('.faux')){const e=document.createElement('div');e.className='art faux';e.textContent=name[0];w.append(e)}};w.append(cover);const no=document.createElement('span');no.className='number';no.textContent='#'+(i+1);w.append(no);const title=document.createElement('div');title.className='name';title.textContent=name;const cat=document.createElement('div');cat.className='cat';cat.textContent=types[i];b.append(w,title,cat);b.onclick=()=>openAlbum(i);g.append(b)})}
async function getCovers(){try{const r=await fetch('/api/covers');if(!r.ok)throw Error('covers unavailable');const data=await r.json();data.forEach((o,i)=>{if(o.art)art[i]=o.art;links[i]=o.apple||links[i]});saveLocal();refreshCoverNodes()}catch(e){console.warn('Artwork refresh skipped',e)}}
function setFocus(){if(art[chosen]){if($('focusArt').getAttribute('src')!==art[chosen])$('focusArt').src=art[chosen]}else $('focusArt').removeAttribute('src');$('focusName').textContent=names[chosen];$('focusDesc').textContent=types[chosen]+' · Listen to the latest episodes.'}
function openAlbum(i){document.body.classList.add('album-mode');$('albumPage').style.display='block';select(i);window.scrollTo({top:0,behavior:'auto'});history.pushState({album:i},'', '#album-'+i)}
function closeAlbum(){document.body.classList.remove('album-mode');$('albumPage').style.display='none';window.scrollTo({top:0,behavior:'instant'});if(location.hash.startsWith('#album-'))history.back()}
window.addEventListener('popstate',()=>{if(location.hash.startsWith('#album-')){const i=Number(location.hash.slice(7));if(Number.isInteger(i)&&i>=0&&i<names.length){document.body.classList.add('album-mode');$('albumPage').style.display='block';select(i)}}else closeAlbum()});
async function select(i){chosen=i;document.querySelectorAll('#grid .tile').forEach((tile,j)=>tile.classList.toggle('active',i===j));setFocus();updateFavButton();const d=allEpisodes[i];if(d&&d.episodes?.length){applyEpisodes(d);return}const token=++selectionToken;$('loading').textContent='Loading episodes…';$('episodes').textContent='Loading episodes…';try{const r=await fetch('/api/episodes/'+i);if(!r.ok)throw Error('Network unavailable');const fresh=await r.json();if(fresh.episodes?.length){allEpisodes[i]=fresh;saveLocal()}if(token!==selectionToken)return;if(fresh.episodes?.length)applyEpisodes(fresh);else{$('loading').textContent='Feed unavailable';$('episodes').textContent=(fresh.errors||[]).join(' · ')||'No episodes found'}}catch(e){if(token===selectionToken){$('loading').textContent='Connection unavailable';$('episodes').textContent=e.message}}}
let activeCues=[],subtitleOn=true,activeEpisode=null,activeShow=null,transcriptRequestId=0;
async function generateAI(){if(!activeEpisode){$('captionText').textContent='Choose an episode first.';return}const requestId=++transcriptRequestId;$('captionText').textContent='Generating AI transcript…';$('fullCaptionStatus').textContent='AI transcription in progress';refreshLyrics();$('generateBtn').disabled=true;try{const r=await fetch('/api/ai-transcribe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({show:activeShow,episode:activeEpisode.index})});const data=await r.json();if(!r.ok)throw Error(data.error||'Transcription failed');if(requestId!==transcriptRequestId)return;activeCues=data.segments||[];previousLyric=-1;renderTranscript();refreshLyrics();$('fullCaptionStatus').textContent='AI transcript · Tap any line to seek';$('captionText').textContent=activeCues.length?'AI transcript ready — playback synchronized.':data.text||'No timestamped text available.'}catch(err){if(requestId===transcriptRequestId){$('captionText').textContent=err.message;$('fullCaptionStatus').textContent='Transcription unavailable';refreshLyrics()}}finally{$('generateBtn').disabled=false}}

let transcriptOpen=false;function toggleTranscript(){transcriptOpen=!transcriptOpen;$('transcriptPanel').style.display=transcriptOpen?'block':'none';$('transcriptBtn').textContent=transcriptOpen?'Close subtitles':'Open subtitles';renderTranscript()}
function renderTranscript(){if(!transcriptOpen)return;const box=$('transcriptLines');box.replaceChildren();if(!activeCues.length){box.textContent=$('captionText').textContent;return}activeCues.forEach((cue,i)=>{const line=document.createElement('div');line.textContent=cue.text;line.dataset.index=i;line.style.padding='3px 5px';line.style.cursor='pointer';line.onclick=()=>{$('audio').currentTime=cue.start};box.appendChild(line)})}
function stamp(s){const p=s.replace(',','.').trim().split(':').map(Number);return p.reduce((a,b)=>a*60+b,0)}
function parseCaptions(text){return text.replace(/\\r/g,'').split(/\\n\\s*\\n/).flatMap(block=>{const lines=block.split('\\n').filter(Boolean),idx=lines.findIndex(x=>x.includes('-->'));if(idx<0)return [];const match=lines[idx].match(/(\\d{1,2}:)?\\d{2}:\\d{2}[.,]\\d{3}\\s*-->\\s*((\\d{1,2}:)?\\d{2}:\\d{2}[.,]\\d{3})/);if(!match)return [];const times=lines[idx].split('-->').map(x=>stamp(x.trim().split(' ')[0]));return [{start:times[0],end:times[1],text:lines.slice(idx+1).join(' ').replace(/<[^>]*>/g,'')}]})}
async function loadTranscript(show,ep,e){activeCues=[];if(!e.transcripts?.length){$('captionText').textContent='No official transcript yet. Tap Generate AI subtitles.';refreshLyrics();return} $('captionText').textContent='Loading official transcript…';try{const r=await fetch('/api/transcript?show='+show+'&episode='+ep);if(!r.ok)throw Error('Transcript unavailable');const text=await r.text();if(e.transcripts[0].type==='text/plain'){$('captionText').textContent=text.slice(0,6000);return}activeCues=parseCaptions(text);previousLyric=-1;renderTranscript();refreshLyrics();$('fullCaptionStatus').textContent='Official captions';$('captionText').textContent=activeCues.length?'Captions ready — press play.':'Transcript has no supported timestamps.'}catch(err){$('captionText').textContent=err.message}}
function playEpisode(e,resumeAt=0){++transcriptRequestId;activeCues=[];previousLyric=-1;renderTranscript();activeShow=chosen;activeEpisode={index:latest.findIndex(x=>x.audio===e.audio)};$('audio').src=e.audio;if(resumeAt>0){$('audio').addEventListener('loadedmetadata',function resumeOnce(){this.removeEventListener('loadedmetadata',resumeOnce);this.currentTime=Math.min(resumeAt,Math.max(0,(this.duration||resumeAt+1)-2))},{once:true})}$('playing').textContent=e.title;$('miniTitle').textContent=e.title;$('playerHeading').textContent=e.title;$('miniShow').textContent=names[chosen];$('playerShow').textContent=names[chosen];$('miniArt').src=art[chosen]||'';$('miniArt').style.display=art[chosen]?'block':'none';$('miniFallback').style.display=art[chosen]?'none':'grid';$('playerArtwork').src=art[chosen]||'';loadTranscript(chosen,latest.findIndex(x=>x.audio===e.audio),e);openPlayer();saveProgress();$('audio').play().catch(()=>{})}
$('audio').addEventListener('timeupdate',()=>{if(!activeCues.length||!subtitleOn)return;const t=$('audio').currentTime;const cue=activeCues.find(x=>t>=x.start&&t<x.end);if(cue && $('captionText').textContent!==cue.text){$('captionText').textContent=cue.text;if(transcriptOpen){const i=activeCues.indexOf(cue),lines=$('transcriptLines').children;for(let j=0;j<lines.length;j++)lines[j].style.background=j===i?'#31534a':'transparent';lines[i]?.scrollIntoView({block:'nearest'})}}});
function toggleCaptions(){subtitleOn=!subtitleOn;$('captionBtn').textContent=subtitleOn?'CC On':'CC Off';$('captionText').style.display=subtitleOn?'block':'none'}
async function morning(){openAlbum(3);await select(3);if(latest[0])playEpisode(latest[0]);$('episodes').scrollIntoView({behavior:'smooth'})}
const hadCache=restoreLocal();draw();setFocus();updateFavButton();showResume();if(allEpisodes[chosen]?.episodes?.length)applyEpisodes(allEpisodes[chosen]);else {$('loading').textContent='Loading podcasts…';$('episodes').textContent='Fetching episodes for the first time…'}getCovers();
allPromise=fetch('/api/all-episodes').then(r=>{if(!r.ok)throw Error('RSS temporarily unavailable');return r.json()}).then(data=>{let changed=false;data.forEach((feed,i)=>{if(feed?.episodes?.length){const old=JSON.stringify((allEpisodes[i]?.episodes||[]).map(x=>x.audio));const now=JSON.stringify(feed.episodes.map(x=>x.audio));if(old!==now){allEpisodes[i]=feed;changed=true}}});if(changed){saveLocal();if(allEpisodes[chosen]?.episodes?.length)applyEpisodes(allEpisodes[chosen])}else if(allEpisodes[chosen]?.episodes?.length){$('loading').textContent='Up to date'}else select(chosen)}).catch(err=>{console.warn(err);if(!allEpisodes[chosen]?.episodes?.length)select(chosen);else $('loading').textContent='Offline · showing saved episodes'});
$('audio').addEventListener('timeupdate',()=>{if(Date.now()-lastSavedAt>5000){lastSavedAt=Date.now();saveProgress()}});
$('audio').addEventListener('pause',saveProgress);
window.addEventListener('pagehide',saveProgress);
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
</script></body></html>""".replace("__SHOWS__",json.dumps(NAMES))
SW=b"self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>self.clients.claim());"
def covers():
    def obtain():
        def one(pair):
            i,name=pair
            art=""; apple=""; publisher=""
            try:
                u=("https://itunes.apple.com/lookup?id=1222114325" if i==10 else "https://itunes.apple.com/lookup?id=1573189055" if i==11 else "https://itunes.apple.com/lookup?id=1190981360" if i==9 else "https://itunes.apple.com/search?"+urllib.parse.urlencode({"term":name,"entity":"podcast","limit":12,"country":"us"}))
                results=json.loads(fetch(u)).get("results",[])
                def score(x):
                    n=x.get("collectionName","").lower(); q=name.lower()
                    return (100 if n==q else 50 if q in n else 20 if n in q else 0)+(2 if "podcast" in x.get("kind","") else 0)
                if results:
                    match=max(results,key=score)
                    if i in (9,10,11) or score(match)>=20:
                        art=match.get("artworkUrl600") or match.get("artworkUrl100") or ""
                        apple=match.get("collectionViewUrl","")
                        publisher=match.get("artistName","")
            except Exception:pass
            return {"name":name,"art":art,"apple":apple,"publisher":publisher}
        with ThreadPoolExecutor(max_workers=10) as pool:
            return list(pool.map(one,enumerate(NAMES)))
    return cache("covers_v3",obtain)



def resolved_audio_url(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 EchoPod/1.0","Accept":"*/*"},method="HEAD")
    try:
        with urllib.request.urlopen(req,timeout=15) as resp:return resp.geturl()
    except Exception:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 EchoPod/1.0","Range":"bytes=0-0"})
        with urllib.request.urlopen(req,timeout=15) as resp:return resp.geturl()

def upload_audio_request(url, key):
    import shutil, sys, csv, glob
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg:
        try:import imageio_ffmpeg
        except ImportError:
            subprocess.run([sys.executable,"-m","pip","install","--quiet","--target","/tmp/echopod_ffmpeg","imageio-ffmpeg"],check=True,timeout=120)
            sys.path.insert(0,"/tmp/echopod_ffmpeg")
            import imageio_ffmpeg
        ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    def send_file(path):
        boundary="EchoPodFileBoundary86532"
        fields={"model":"whisper-large-v3-turbo","response_format":"verbose_json","timestamp_granularities[]":"segment"}
        with open(path,"rb") as fp:data=fp.read()
        if len(data)>24*1024*1024:raise RuntimeError("Audio chunk exceeds 24 MB")
        parts=[('--'+boundary+'\r\nContent-Disposition: form-data; name="'+k+'"\r\n\r\n'+v+'\r\n').encode() for k,v in fields.items()]
        parts.append(('--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="clip.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n').encode()+data+b'\r\n')
        parts.append(('--'+boundary+'--\r\n').encode())
        req=urllib.request.Request("https://api.groq.com/openai/v1/audio/transcriptions",data=b"".join(parts),headers={"Authorization":"Bearer "+key,"Content-Type":"multipart/form-data; boundary="+boundary,"User-Agent":"EchoPod/1.0"},method="POST")
        with urllib.request.urlopen(req,timeout=115) as resp:return json.loads(resp.read(2000000))
    with tempfile.TemporaryDirectory() as folder:
        source=os.path.join(folder,"original")
        request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 EchoPod/1.0"})
        with urllib.request.urlopen(request,timeout=90) as stream,open(source,"wb") as output:
            total=0
            while True:
                part=stream.read(1024*1024)
                if not part:break
                total+=len(part)
                if total>180*1024*1024:raise RuntimeError("Podcast exceeds 180 MB download limit")
                output.write(part)
        if total<=24*1024*1024:return send_file(source)
        # Stream-copy the original audio into short clips, without re-encoding/compression.
        pattern=os.path.join(folder,"clip_%04d.mp3")
        manifest=os.path.join(folder,"segments.csv")
        cmd=[ffmpeg,"-nostdin","-loglevel","error","-y","-i",source,"-vn","-c:a","copy","-f","segment","-segment_time","180","-reset_timestamps","1","-segment_list",manifest,"-segment_list_type","csv",pattern]
        job=subprocess.run(cmd,capture_output=True,timeout=95)
        if job.returncode:raise RuntimeError("Audio segmentation failed: "+job.stderr.decode("utf-8","replace")[:180])
        with open(manifest,newline="") as fp: entries=list(csv.reader(fp))
        if not entries:raise RuntimeError("No audio segments created")
        if len(entries)>80:raise RuntimeError("Podcast too long for automatic transcription")
        # Limit parallel requests to protect Render memory and Groq rate limits.
        def transcribe_chunk(entry):
            filename,start,_end=entry
            res=send_file(os.path.join(folder,os.path.basename(filename)))
            offset=float(start)
            return {"segments":[{"start":round(float(s.get("start",0))+offset,3),"end":round(float(s.get("end",0))+offset,3),"text":s.get("text","")} for s in res.get("segments",[])],"text":res.get("text","")}
        with ThreadPoolExecutor(max_workers=2) as pool:
            chunks=list(pool.map(transcribe_chunk,entries))
        return {"segments":[s for piece in chunks for s in piece["segments"]],"text":" ".join(piece["text"] for piece in chunks)}

def ai_transcribe(show, episode):
    if not (0 <= show < len(NAMES) and 0 <= episode < 35):raise ValueError("Invalid episode")
    key=os.environ.get("GROQ_API_KEY","")
    if not key:raise RuntimeError("Groq API key not configured")
    found=episodes(show)["episodes"]
    if episode>=len(found):raise ValueError("Episode not found")
    item=found[episode]
    audio=item["audio"]
    cache_key="groq:"+audio
    existing=CACHE.get(cache_key)
    if existing:return existing[1]
    def duration_minutes(s):
        try:
            parts=[int(x) for x in str(s).split(":")]
            if len(parts)==1:return max(1,math.ceil(parts[0]/60))
            if len(parts)==2:return max(1,math.ceil((parts[0]*60+parts[1])/60))
            if len(parts)==3:return max(1,math.ceil((parts[0]*3600+parts[1]*60+parts[2])/60))
        except (ValueError,TypeError):pass
        return 60
    minutes=duration_minutes(item.get("duration",""))
    day=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    with AI_LOCK:
        stats=AI_DAILY.setdefault(day,{"minutes":0,"requests":0})
        if stats["minutes"]+minutes>480:raise RuntimeError("Daily audio budget reached (480 minutes)")
        if stats["requests"]>=2000:raise RuntimeError("Daily request limit reached (2000)")
        stats["minutes"]+=minutes
        stats["requests"]+=1
    final_audio=resolved_audio_url(audio)
    fields={"model":"whisper-large-v3-turbo","response_format":"verbose_json","timestamp_granularities[]":"segment","url":final_audio}
    boundary="EchoPodBoundary86532"
    body=b"".join(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+k+"\"\r\n\r\n"+v+"\r\n").encode() for k,v in fields.items())+("--"+boundary+"--\r\n").encode()
    req=urllib.request.Request("https://api.groq.com/openai/v1/audio/transcriptions",data=body,headers={"Authorization":"Bearer "+key,"Content-Type":"multipart/form-data; boundary="+boundary,"User-Agent":"EchoPod/1.0"},method="POST")
    try:
        try:
            with urllib.request.urlopen(req,timeout=115) as response:result=json.loads(response.read(2000000))
        except urllib.error.HTTPError as e:
            msg=e.read(1200).decode("utf-8","replace")
            if e.code==400 and ("302" in msg or "media_fetch_failed" in msg or "media_too_large" in msg):result=upload_audio_request(audio,key)
            else:raise RuntimeError("Groq API error "+str(e.code)+": "+msg[:260])
    except urllib.error.HTTPError as e:
        with AI_LOCK:stats["minutes"]-=minutes
        detail=e.read(1500).decode("utf-8","replace")
        raise RuntimeError("Groq API rejected this audio ("+str(e.code)+"). It may exceed the free-tier audio limit. "+detail[:250])
    except Exception:
        with AI_LOCK:stats["minutes"]-=minutes
        raise
    segments=[{"start":s.get("start",0),"end":s.get("end",0),"text":s.get("text","")} for s in result.get("segments",[]) if isinstance(s,dict)]
    output={"segments":segments,"text":result.get("text",""),"show":show,"episode":episode}
    CACHE[cache_key]=(time.time(),output)
    return output

class Handler(BaseHTTPRequestHandler):
    def reply(self,v,typ="application/json",status=200):
        data=v if isinstance(v,bytes) else v.encode() if isinstance(v,str) else json.dumps(v).encode()
        self.send_response(status);self.send_header("Content-Type",typ);self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
    def do_POST(self):
        p=urllib.parse.urlsplit(self.path).path
        if p!="/api/ai-transcribe":return self.reply({"error":"Not found"},status=404)
        key=os.environ.get("GROQ_API_KEY","")
        if not key:return self.reply({"error":"AI transcription requires GROQ_API_KEY in Render settings."},status=503)
        try:
            size=int(self.headers.get("Content-Length","0"))
            if size<1 or size>1000:raise ValueError("Invalid request")
            params=json.loads(self.rfile.read(size))
            result=ai_transcribe(int(params["show"]),int(params["episode"]))
            return self.reply(result)
        except Exception as e:return self.reply({"error":str(e)},status=422)
    def do_GET(self):
        p=urllib.parse.urlsplit(self.path).path
        if p in ("/","/index.html"):return self.reply(HTML,"text/html; charset=utf-8")
        if p=="/sw.js":return self.reply(SW,"text/javascript")
        if p=="/manifest.webmanifest":return self.reply({"name":"EchoPod Morning","short_name":"EchoPod","start_url":"/","display":"standalone","background_color":"#07141a","theme_color":"#07141a"})
        if p=="/api/health":return self.reply({"status":"ok"})
        if p=="/api/transcript":
            qs=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            try:
                i=int(qs.get("show",["-1"])[0]); n=int(qs.get("episode",["-1"])[0]); t=int(qs.get("track",["0"])[0])
                if not (0<=i<len(NAMES) and 0<=n<35 and 0<=t<5):raise ValueError("Invalid transcript reference")
                result=episodes(i)["episodes"][n]["transcripts"][t]
                raw=cache("transcript:"+result["url"],lambda:fetch(result["url"]))
                if len(raw)>2000000:raise ValueError("Transcript too large")
                return self.reply(raw,"text/plain; charset=utf-8")
            except Exception as e:return self.reply({"error":str(e)},status=404)
        if p=="/api/covers":return self.reply(covers())
        if p=="/api/all-episodes":
            with ThreadPoolExecutor(max_workers=10) as pool:
                result=list(pool.map(episodes,range(len(NAMES))))
            return self.reply(result)
        if p=="/api/diagnostics":
            try:raw=fetch(FEEDS[3]);return self.reply({"rss":"ok","bytes":len(raw),"episodes":len(parse(raw))})
            except Exception as e:return self.reply({"rss":"failed","error":str(e)},status=502)
        m=re.fullmatch("/api/episodes/([0-9]+)",p)
        if m:
            i=int(m[1])
            if i>=len(NAMES):return self.reply({"error":"Not found"},status=404)
            return self.reply(episodes(i))
        return self.reply({"error":"Not found"},status=404)
ThreadingHTTPServer(("0.0.0.0",int(os.environ.get("PORT","10000"))),Handler).serve_forever()
