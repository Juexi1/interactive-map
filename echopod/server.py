import os, json, re, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

NAMES=["The Diary of a CEO","The Joe Rogan Experience","The Rest Is History","The Daily","The Mel Robbins Podcast","Good Hang with Amy Poehler","Crime Junkie","Dateline NBC","The Shawn Ryan Show","This Past Weekend with Theo Von"]
FEEDS={0:"https://rss2.flightcast.com/xmsftuzjjykcmqwolaqn6mdn",2:"https://feeds.megaphone.fm/GLT4787413333",3:"https://feeds.simplecast.com/Sl5CSM3S",4:"https://feeds.simplecast.com/UCwaTX1J",6:"https://feeds.simplecast.com/qm_9xx0g",9:"https://feeds.megaphone.fm/thispastweekend"}
CACHE={}
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 EchoPod/1.0","Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=14) as res:return res.read(8000000)
def cache(k,fn):
    old=CACHE.get(k)
    if old and time.time()-old[0]<3600:return old[1]
    x=fn();CACHE[k]=(time.time(),x);return x
def local(el,tag):
    for c in el:
        if c.tag.split("}")[-1].lower()==tag.lower():return (c.text or "").strip()
    return ""
def parse(raw):
    root=ET.fromstring(raw)
    items=root.findall("./channel/item")
    output=[]
    for item in items[:35]:
        url=""
        for e in item.iter():
            if e.tag.split("}")[-1]=="enclosure":
                url=e.get("url","")
                if url:break
        if url and url.startswith("https://"):output.append({"title":local(item,"title"),"date":local(item,"pubDate"),"audio":url,"description":re.sub("<[^>]+>"," ",local(item,"description"))[:260]})
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
            out=cache(feed,lambda:parse(fetch(feed)))
            if out:return {"episodes":out,"feed":feed,"errors":errors}
            errors.append("RSS contained no playable audio")
        except Exception as e:errors.append("RSS: "+str(e))
    return {"episodes":[],"errors":errors}
HTML=r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0c1014"><title>EchoPod — Listen beyond the noise</title><link rel="manifest" href="/manifest.webmanifest"><link rel="preconnect" href="https://is1-ssl.mzstatic.com"><style>
:root{--bg:#0c1014;--panel:#161e24;--border:#29333b;--fg:#f7f8f8;--soft:#9eabb5;--mint:#b6f26a;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--fg);background:var(--bg)}*{box-sizing:border-box}body{margin:0;padding-bottom:142px}button{font:inherit;cursor:pointer}.shell{max-width:1270px;padding:32px 35px;margin:auto}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:50px}.logo{font-size:25px;letter-spacing:-1.3px;font-weight:850}.logo span{color:var(--mint)}.topright{font-size:12px;border:1px solid #364249;border-radius:30px;padding:9px 14px;color:var(--soft)}.dot{display:inline-block;background:var(--mint);width:7px;height:7px;border-radius:50%;margin-right:7px}.eyebrow{letter-spacing:2px;color:var(--mint);font-size:12px;font-weight:750;margin-bottom:13px}.hero{display:flex;justify-content:space-between;align-items:end;gap:20px}.hero h1{font-size:clamp(36px,6vw,70px);letter-spacing:-3.5px;line-height:1.06;margin:0 0 17px;font-weight:850}.hero p{color:var(--soft);max-width:490px;line-height:1.6;font-size:15px;margin:0}.pill{border:0;color:#0c1014;background:var(--mint);padding:15px 22px;border-radius:40px;font-size:14px;font-weight:800;white-space:nowrap}.pill:hover{background:#d4ff9b}.sectionhead{display:flex;justify-content:space-between;align-items:center;margin:55px 0 22px}.sectionhead h2{font-size:23px;letter-spacing:-.7px;margin:0}.subtle{color:var(--soft);font-size:12px}.grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:16px}.tile{border:1px solid transparent;background:transparent;text-align:left;padding:0;color:var(--fg);border-radius:15px;min-width:0}.tile.active .art{outline:2px solid var(--mint);outline-offset:3px}.art{width:100%;aspect-ratio:1;border-radius:14px;background:linear-gradient(135deg,#2e404c,#182329);object-fit:cover;display:block}.art-wrap{position:relative}.number{position:absolute;top:9px;left:9px;background:#10171dd9;color:#fff;border-radius:8px;padding:5px 9px;font-size:12px;font-weight:750}.faux{display:grid;place-items:center;font-size:50px;color:#c1e09b;font-weight:900}.tile .name{font-size:14px;font-weight:750;line-height:1.4;margin:12px 0 5px}.tile .cat{color:var(--soft);font-size:12px}.focus{background:linear-gradient(130deg,#1c2930,#11191e);border:1px solid var(--border);border-radius:22px;padding:25px;display:flex;gap:28px;align-items:center}.focus-cover{width:165px;height:165px;flex-shrink:0;object-fit:cover;border-radius:14px;background:#30424b}.focus h3{font-size:clamp(22px,3vw,32px);margin:8px 0;letter-spacing:-1px}.focus p{color:var(--soft);font-size:13px;line-height:1.6}#episodes{min-height:440px;overflow-anchor:none}.grid,.focus{overflow-anchor:none}html{scroll-behavior:auto}.line{height:1px;background:var(--border);margin:32px 0 10px}.episode{display:flex;align-items:center;padding:16px 0;gap:16px;border-bottom:1px solid #283039}.episode .n{color:#71848d;font-size:12px;width:22px;flex-shrink:0}.episode .details{flex:1;min-width:0}.episode .title{font-size:14px;font-weight:700;line-height:1.5}.episode .meta{font-size:12px;color:var(--soft);margin-top:5px}.epbtn{border:1px solid #526167;background:transparent;color:#fff;border-radius:50%;width:38px;height:38px;flex-shrink:0;font-size:14px}.epbtn:hover{color:#111;background:var(--mint)}.error{color:#ffb9a8;line-height:1.6}.footer{position:fixed;bottom:0;left:0;right:0;z-index:10;background:#182228f5;backdrop-filter:blur(20px);border-top:1px solid #2e4148;padding:14px max(20px,calc((100vw - 1200px)/2))}.now{display:flex;align-items:center;gap:10px;font-size:12px;margin-bottom:7px;color:var(--soft)}.now b{color:#fff;font-size:13px;white-space:nowrap;text-overflow:ellipsis;overflow:hidden;max-width:85vw}audio{width:100%;height:35px;accent-color:var(--mint)}.footer a{color:var(--mint)}@media(max-width:850px){.grid{grid-template-columns:repeat(3,minmax(0,1fr))}.shell{padding:24px 19px}.top{margin-bottom:37px}.hero{align-items:start;flex-direction:column}.hero h1{letter-spacing:-2px}.sectionhead{margin-top:40px}.focus-cover{height:105px;width:105px}.focus{padding:15px;gap:16px}}@media(max-width:500px){.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 13px}.focus-cover{height:95px;width:95px}.focus h3{font-size:21px}.tile .name{font-size:13px}.art{border-radius:11px}.faux{font-size:37px}.hero h1{font-size:44px}}
</style></head><body><main class="shell"><header class="top"><div class="logo">echo<span>pod.</span></div><div class="topright"><span class="dot"></span>YOUR DAILY LISTEN</div></header><section class="hero"><div><div class="eyebrow">DISCOVER · LISTEN · REPEAT</div><h1>Good morning.<br>Great listening.</h1><p>Discover the world's most talked-about podcasts. Fresh perspectives, brilliant conversations, and stories worth your time.</p></div><button class="pill" onclick="morning()">▶ &nbsp; Start morning listen</button></section><div class="sectionhead"><h2>Global Top 10</h2><span class="subtle">Curated chart snapshot ↗</span></div><div id="grid" class="grid"></div><div class="sectionhead"><h2>Now exploring</h2><span id="loading" class="subtle">Select a podcast</span></div><section class="focus"><img id="focusArt" class="focus-cover" alt="Podcast cover"><div><div class="eyebrow">FEATURED PODCAST</div><h3 id="focusName">The Daily</h3><p id="focusDesc">Latest episodes and stories, ready to play.</p><div class="subtle" id="count"></div></div></section><div class="sectionhead" style="margin-top:36px"><h2>Latest episodes</h2><span class="subtle">PLAY ANY EPISODE</span></div><div id="episodes"></div><p class="subtle" style="margin-top:30px">Podcast artwork is provided by publishers and directory listings. <a style="color:var(--mint)" href="/api/diagnostics" target="_blank">Connection diagnostics</a></p></main><footer class="footer"><div class="now">♫ NOW PLAYING <b id="playing">Choose an episode to listen</b></div><audio id="audio" controls playsinline preload="none"></audio></footer><script>
const names=__SHOWS__;const types=['Business · Interviews','Conversation · Culture','History','Daily News','Self Improvement','Comedy · Interviews','True Crime','True Crime · News','Conversations','Comedy · Interviews'];let art=names.map(()=>''), links=names.map(()=>''),chosen=3, latest=[], selectionToken=0, allEpisodes=Array(10).fill(null), allPromise=null;
const $=id=>document.getElementById(id);
function draw(){const g=$('grid');g.replaceChildren();names.forEach((name,i)=>{const b=document.createElement('button');b.className='tile'+(i===chosen?' active':'');const w=document.createElement('div');w.className='art-wrap';const cover=document.createElement('img');cover.className='art';cover.alt=name+' podcast cover';cover.loading='lazy';if(art[i])cover.src=art[i];else{cover.style.display='none';const fallback=document.createElement('div');fallback.className='art faux';fallback.textContent=name.slice(0,1);w.appendChild(fallback)}cover.onerror=()=>{cover.style.display='none';if(!w.querySelector('.faux')){const e=document.createElement('div');e.className='art faux';e.textContent=name[0];w.append(e)}};w.append(cover);const no=document.createElement('span');no.className='number';no.textContent='#'+(i+1);w.append(no);const title=document.createElement('div');title.className='name';title.textContent=name;const cat=document.createElement('div');cat.className='cat';cat.textContent=types[i];b.append(w,title,cat);b.onclick=()=>select(i);g.append(b)})}
async function getCovers(){try{let data=await (await fetch('/api/covers')).json();data.forEach((o,i)=>{art[i]=o.art||'';links[i]=o.apple||''});document.querySelectorAll('#grid .tile').forEach((tile,i)=>{if(!art[i])return;const img=tile.querySelector('img.art');if(img&&img.getAttribute('src')!==art[i]){img.src=art[i];img.style.display='block';const fallback=tile.querySelector('.faux');if(fallback)fallback.remove()}});setFocus()}catch(e){console.warn('Artwork service unavailable',e)}}
function setFocus(){if(art[chosen]){if($('focusArt').getAttribute('src')!==art[chosen])$('focusArt').src=art[chosen]}else $('focusArt').removeAttribute('src');$('focusName').textContent=names[chosen];$('focusDesc').textContent=types[chosen]+' · Listen to the latest episodes.'}
async function select(i){const token=++selectionToken;chosen=i;latest=[];document.querySelectorAll('#grid .tile').forEach((tile,j)=>tile.classList.toggle('active',i===j));setFocus();$('loading').textContent='Loading episodes…';$('count').textContent='';if(!allEpisodes[i])$('episodes').replaceChildren();try{const d=allEpisodes[i] || await (async()=>{const r=await fetch('/api/episodes/'+i);return r.json()})();if(token!==selectionToken)return;latest=d.episodes||[];$('episodes').replaceChildren();if(!latest.length){$('loading').textContent='Unavailable';const e=document.createElement('p');e.className='error';e.textContent='Could not load episodes. '+(d.errors||[]).join(' · ');$('episodes').append(e);return}$('loading').textContent='Updated from RSS';$('count').textContent=latest.length+' available episodes';latest.forEach((e,j)=>{const row=document.createElement('div');row.className='episode';const idx=document.createElement('div');idx.className='n';idx.textContent=String(j+1).padStart(2,'0');const info=document.createElement('div');info.className='details';const t=document.createElement('div');t.className='title';t.textContent=e.title;const m=document.createElement('div');m.className='meta';m.textContent=e.date||'Latest episode';info.append(t,m);const play=document.createElement('button');play.className='epbtn';play.textContent='▶';play.setAttribute('aria-label','Play '+e.title);play.onclick=()=>playEpisode(e);row.append(idx,info,play);$('episodes').append(row)})}catch(e){if(token!==selectionToken)return;$('loading').textContent='Connection failed';$('episodes').textContent=e.message}}
function playEpisode(e){$('audio').src=e.audio;$('playing').textContent=e.title;$('audio').play().catch(()=>{})}
async function morning(){await select(3);if(latest[0])playEpisode(latest[0]);$('episodes').scrollIntoView({behavior:'smooth'})}
draw();setFocus();$('loading').textContent='Loading all 10 podcast feeds…';$('episodes').innerHTML='<p class="subtle">Loading all podcasts in parallel. Episodes are cached for one hour.</p>';getCovers();allPromise=fetch('/api/all-episodes').then(r=>{if(!r.ok)throw Error('Feed batch failed');return r.json()}).then(data=>{allEpisodes=data;$('loading').textContent='All podcast feeds checked';return select(chosen)}).catch(err=>{console.warn(err);$('loading').textContent='Some feeds unavailable';return select(chosen)});if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
</script></body></html>""".replace("__SHOWS__",json.dumps(NAMES))
SW=b"self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>self.clients.claim());"
def covers():
    def obtain():
        def one(pair):
            i,name=pair
            art=""; apple=""; publisher=""
            try:
                u=("https://itunes.apple.com/lookup?id=1190981360" if i==9 else "https://itunes.apple.com/search?"+urllib.parse.urlencode({"term":name,"entity":"podcast","limit":12,"country":"us"}))
                results=json.loads(fetch(u)).get("results",[])
                def score(x):
                    n=x.get("collectionName","").lower(); q=name.lower()
                    return (100 if n==q else 50 if q in n else 20 if n in q else 0)+(2 if "podcast" in x.get("kind","") else 0)
                if results:
                    match=max(results,key=score)
                    if i==9 or score(match)>=20:
                        art=match.get("artworkUrl600") or match.get("artworkUrl100") or ""
                        apple=match.get("collectionViewUrl","")
                        publisher=match.get("artistName","")
            except Exception:pass
            return {"name":name,"art":art,"apple":apple,"publisher":publisher}
        with ThreadPoolExecutor(max_workers=10) as pool:
            return list(pool.map(one,enumerate(NAMES)))
    return cache("covers_v3",obtain)

class Handler(BaseHTTPRequestHandler):
    def reply(self,v,typ="application/json",status=200):
        data=v if isinstance(v,bytes) else v.encode() if isinstance(v,str) else json.dumps(v).encode()
        self.send_response(status);self.send_header("Content-Type",typ);self.send_header("Content-Length",str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        p=urllib.parse.urlsplit(self.path).path
        if p in ("/","/index.html"):return self.reply(HTML,"text/html; charset=utf-8")
        if p=="/sw.js":return self.reply(SW,"text/javascript")
        if p=="/manifest.webmanifest":return self.reply({"name":"EchoPod Morning","short_name":"EchoPod","start_url":"/","display":"standalone","background_color":"#07141a","theme_color":"#07141a"})
        if p=="/api/health":return self.reply({"status":"ok"})
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
