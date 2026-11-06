// Run on an open Instagram profile page (logged-in Chrome) via the Claude in Chrome javascript tool.
// Body of an async function: returns a JSON string with public stats of the last 12 posts.
await new Promise(r => setTimeout(r, 2500));
const og = document.querySelector('meta[property="og:description"]')?.content || '';
const P = {
  "Enrolment": /enrol|apply|application|open (day|evening|morning)|admission|taster|places available|registration|promotion|offer|join us|prospectus/i,
  "Sport": /match|final|cup|rugby|hurling|football|camogie|basketball|athletic|hockey|sport|golf|team|blitz|league/i,
  "Achievement": /congratulat|award|winner|achiev|result|scholarship|medal|proud|success|well done/i,
  "Faith & values": /chapel|prayer|pray|god|faith|christ|bible|church|blessing|advent|scripture|worship/i,
  "Seasonal": /christmas|halloween|easter|santa|festive|patrick|valentine|mother.?s day|new year/i,
  "Events": /concert|show|musical|trip|visit|event|day out|celebrat|graduation|ceremony|week|tickets|fun/i,
  "Staff": /teacher|staff|principal|meet (our|the)|welcome (to )?(our )?new/i,
  "Community": /charity|fundrais|donat|community|volunteer|support/i
};
const num = x => { if (!x) return 0; x = x.replace(/,/g, ''); return x.endsWith('K') ? Math.round(parseFloat(x) * 1000) : x.endsWith('M') ? Math.round(parseFloat(x) * 1e6) : parseInt(x) || 0; };
const owner = location.pathname.split('/').filter(Boolean)[0];
const links = [...new Set([...document.querySelectorAll('main a[href*="/p/"],main a[href*="/reel/"]')].map(a => a.getAttribute('href')))]
  .filter(l => l.startsWith('/' + owner + '/') || /^\/(p|reel)\//.test(l)).slice(0, 12);  // skip collab posts from other accounts
const it = [];
for (const l of links) {
  const h = await (await fetch(l)).text();
  const m = h.match(/property="og:description"[^>]*content="([^"]+)"/) || h.match(/content="([^"]+)"[^>]*property="og:description"/);
  const s = (m ? m[1] : '').replace(/&quot;/g, '"').replace(/&#0?39;/g, "'").replace(/&amp;/g, '&');
  const lk = s.match(/^([\d,.KM]+) likes?/); const cm = s.match(/([\d,.KM]+) comments?/); const dt = s.match(/ on ([A-Z][a-z]+ \d{1,2}, \d{4})/);
  const cap = (s.split(': "')[1] || ''); if (!lk) continue;
  it.push({ t: l.includes('/reel/') ? 'Reel' : 'Post', l: num(lk[1]), c: num(cm && cm[1]), d: dt ? Date.parse(dt[1]) : null,
            p: Object.keys(P).find(k => P[k].test(cap)) || 'Student life', code: l.split('/').filter(Boolean).pop() });
}
const v = it.filter(x => x.l > 0);
const avg = a => a.length ? Math.round(a.reduce((s, x) => s + x.l + x.c, 0) / a.length) : 0;
const ds = it.map(x => x.d).filter(Boolean); const span = ds.length > 1 ? (Math.max(...ds) - Math.min(...ds)) / 86400000 : null;
const pc = {}; it.forEach(x => pc[x.p] = (pc[x.p] || 0) + 1);
const top = [...v].sort((a, b) => b.l + b.c - a.l - a.c).slice(0, 2).map(x => [x.code, x.t, x.p, x.l + x.c]);
return JSON.stringify({ og: og.split(' - ')[0], n: it.length, reels: it.filter(x => x.t == 'Reel').length, avgEng: avg(v),
  avgReel: avg(v.filter(x => x.t == 'Reel')), avgPost: avg(v.filter(x => x.t == 'Post')),
  perWeek: span ? +(it.length / (span / 7)).toFixed(1) : null, last: ds.length ? new Date(Math.max(...ds)).toISOString().slice(0, 10) : null,
  pil: pc, pilEng: Object.fromEntries(Object.keys(pc).map(k => [k, avg(v.filter(x => x.p == k))])), top });
