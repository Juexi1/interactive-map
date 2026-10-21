import os, json, re, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

NAMES=["The Diary of a CEO","The Joe Rogan Experience","The Rest Is History","The Daily","The Mel Robbins Podcast","Good Hang with Amy Poehler","Crime Junkie","Dateline NBC","The Shawn Ryan Show","This Past Weekend with Theo Von"]
FEEDS={0:"https://rss2.flightcast.com/xmsftuzjjykcmqwolaqn6mdn",2:"https://feeds.megaphone.fm/GLT4787413333",3:"https://feeds.simplecast.com/Sl5CSM3S",4:"https://feeds.simplecast.com/UCwaTX1J",6:"https://feeds.simplecast.com/qm_9xx0g"}
CACHE={}
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 EchoPod/1.0","Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=14) as res:return res.read(8000000)
def cache(k,fn):
    old=CACHE.get(k)
    if old and time.time()-old[0]<900:return old[1]
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
HTML=r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#07141a"><title>EchoPod — Morning Podcasts</title><link rel="manifest" href="/manifest.webmanifest"><style>
:root{font-family:system-ui,-apple-system,sans-serif;background:#07141a;color:#eef8f5}*{box-sizing:border-box}body{margin:0;padding:24px 16px 130px}main{max-width:850px;margin:auto}.muted{color:#95aaa9}.brand{font-size:34px;font-weight:850;letter-spacing:-1px}.green{color:#6fe8be}.card{background:#11252b;border:1px solid #234046;border-radius:17px;padding:15px;margin:10px 0;cursor:pointer;display:flex;gap:16px;align-items:center}.card:hover,.selected{border-color:#6fe8be}.rank{color:#6fe8be;font-weight:800;font-size:20px;min-width:28px}.cover{width:58px;height:58px;background:#25444b;border-radius:12px;object-fit:cover}.title{font-size:17px;font-weight:750}.desc{font-size:12px;color:#9eb5b3;margin-top:5px}button{cursor:pointer;border:0;background:#6fe8be;color:#09201b;border-radius:13px;padding:10px 16px;font-weight:750}h2{margin-top:30px}.episode{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 0;border-bottom:1px solid #2b4549}.episode button{flex-shrink:0}.bar{position:fixed;bottom:0;left:0;width:100%;background:#0c2228;border-top:1px solid #365357;padding:14px}.inner{max-width:850px;margin:auto}audio{width:100%;margin-top:8px}.error{color:#ffb5a2;white-space:pre-wrap}.spacer{height:15px}a{color:#6fe8be}</style></head><body><main><div class="brand">Echo<span class="green">Pod</span> 🎧</div><p class="muted">Your morning listening room · Worldwide Top 10</p><button onclick="pickDaily()">▶ Play The Daily</button><h2>Global chart</h2><div id="shows"></div><h2 id="selectedTitle">Choose a podcast</h2><div id="status" class="muted">Select a show to load recent episodes.</div><div id="episodes"></div><p class="muted">Chart order is a snapshot, not a live ranking. Streams depend on the publisher and your network.</p><p><a href="/api/diagnostics" target="_blank">Check server connectivity</a></p></main><div class="bar"><div class="inner"><span id="playing" class="muted">Nothing playing</span><audio id="audio" controls playsinline preload="none"></audio></div></div><script>
const names=__SHOWS__;let current=3;
const shows=document.getElementById('shows'),status=document.getElementById('status'),ep=document.getElementById('episodes');
names.forEach((name,i)=>{const item=document.createElement('div');item.className='card';item.innerHTML='<span class="rank">'+String(i+1).padStart(2,'0')+'</span><div class="cover" style="display:grid;place-items:center;font-size:24px">🎙️</div><div><div class="title"></div><div class="desc">Podcast · English</div></div>';item.querySelector('.title').textContent=name;item.onclick=()=>select(i);shows.appendChild(item)});
async function select(i){current=i;document.querySelectorAll('.card').forEach((c,j)=>c.classList.toggle('selected',i===j));document.getElementById('selectedTitle').textContent=names[i];status.textContent='Loading episodes from the server…';ep.replaceChildren();try{const r=await fetch('/api/episodes/'+i);const d=await r.json();if(!d.episodes?.length){status.className='error';status.textContent='Episodes unavailable. '+(d.errors||[]).join(' | ');return}status.className='muted';status.textContent=d.episodes.length+' episodes available';d.episodes.forEach(e=>{const row=document.createElement('div');row.className='episode';const detail=document.createElement('div');const head=document.createElement('div');head.className='title';head.textContent=e.title;const sub=document.createElement('div');sub.className='desc';sub.textContent=(e.date||'').slice(0,25);detail.append(head,sub);const b=document.createElement('button');b.textContent='▶ Play';b.onclick=()=>play(e);row.append(detail,b);ep.append(row)})}catch(err){status.className='error';status.textContent=err.message}}
function play(e){document.getElementById('audio').src=e.audio;document.getElementById('playing').textContent=e.title;document.getElementById('audio').play().catch(()=>{})}
async function pickDaily(){await select(3);const btn=ep.querySelector('button');if(btn)btn.click()}
select(3);
if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
</script></body></html>""".replace("__SHOWS__",json.dumps(NAMES))
SW=b"self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('activate',e=>self.clients.claim());"
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
