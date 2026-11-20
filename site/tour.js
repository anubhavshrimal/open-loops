// The engine of the Open Loops guided tour: one story, an animated bird's-eye view between timestamps,
// then close-ups. All Tasks, PRs, people and numbers are invented.

/* =================== setting =================== */
const K={PR:'PR',pr:n=>'#'+n,check:'CI Check',tracker:'GitHub',host:'Claude Code',hostCmd:'claude -p orchestrator.md',notifier:'Slack',bot:'Open Loops',chan:'open-loops',ws:'acme',
  cols:['Backlog','Ready','Working','Blocked','In Review','Done'],repoA:'acme/api',
  ex:{slug:'tinylm-bpb',title:'Lower val_bpb of a tiny char model',repo:'acme/tinylm',metric:'val_bpb',better:'lower',fmt:v=>v.toFixed(3),
   hyp:'Small training changes cut val_bpb on Tiny Shakespeare by 5% in 6 h of GPU time.',
   rows:[['baseline',1.612,1],['cosine LR + warmup',1.571,1],['width 256 → 384',1.549,1],['dropout 0.1 → 0.2',1.556,0],['rotary position embeddings',1.521,1],['batch 64 → 128',1.528,0],['tie input and output weights',1.509,1]],
   next:['Try a 2× longer context at the same compute.','Retune the learning rate after the width change.'],decide:['Merge the 4 kept changes as one PR, or split them?','Is +12% step time for rotary embeddings acceptable?']}};

/* =================== story =================== */
const ST=['Backlog','Ready','Working','Blocked','In Review','Done'];
function buildStory(K){const X=K.ex.slug,E=K.ex,pr=K.pr;const ref=n=>'PR '+pr(n);K.ref=ref;
 const f=t=>t.replace(/\{PR\}/g,K.PR).replace(/\{check\}/g,K.check).replace(/\{host\}/g,K.host).replace(/\{tracker\}/g,K.tracker).replace(/\{notifier\}/g,K.notifier).replace(/\{metric\}/g,E.metric);
 const tasks={'add-rate-limit':{n:11,title:'Add a rate limit per API key',kind:'Build',state:'Backlog',repo:K.repoA,c:[]},
  'retry-budget':{n:12,title:'Retry budget for clients',kind:'Build',state:'Backlog',dep:11,repo:K.repoA,c:[]},
  'fix-flaky-export':{n:13,title:'Fix the flaky export test',kind:'Build',state:'Backlog',repo:K.repoA,c:[]}};
 tasks[X]={n:14,title:E.title,kind:'Exploration',state:'Backlog',repo:E.repo,c:[]};
 const init=()=>({tasks:JSON.parse(JSON.stringify(tasks)),panes:{},host:[],notes:[],prs:{},rows:[],cycles:0,skipped:0});
 const pn=(s,k,l,alive=true)=>{(s.panes[k]=s.panes[k]||{lines:[]}).lines.push(l);s.panes[k].alive=alive};
 const mv=(s,k,st)=>{s.tasks[k].state=st};
 const nt=(s,t,ev,m)=>s.notes.push({t,ev,m});
 const cyc=(s,t,...l)=>{s.cycles++;s.host.push(`<span class="o">●</span> <span class="w">Cycle ${t}</span> <span class="d">· new session</span>`,...l.map(x=>'  <span class="d">└</span> '+x))};
 const skip=(s,t,n)=>{s.skipped+=n;s.host.push(`<span class="d">${t} change check: no change → no Cycle${n>1?' (×'+n+')':''}</span>`)};
 const row=(s,i)=>{const r=E.rows[i];s.rows.push({n:i,idea:r[0],v:r[1],keep:!!r[2]})};
 const kept=E.rows.filter(x=>x[2]).length-1,best=E.rows.filter(x=>x[2]).slice(-1)[0][1];
 const P=(...ph)=>ph.map((_,i)=>({p:i}));
 const S=[
 {t:'2:00 PM',who:'you',head:'You hand off four Tasks.',
  sum:'You write a Spec for each Task and move the Tasks to Ready. Nothing starts until you do.',
  ph:[s=>{for(const k in s.tasks)mv(s,k,'Ready');s.tasks['retry-budget'].gated=true}],acts:[{w:700},{p:0}],
  b:[[['card:'+X,'An Exploration Spec is an auto-research Task: the Worker hill-climbs one metric within a time budget.'],
      ['card:retry-budget','A Task that depends on another one does not start until that Task is merged and Done.']]]},
 {t:'2:30 PM',who:'cycle',head:'A Cycle spawns Workers.',
  sum:f('{host} starts a Cycle on a cron schedule. It spawns a Worker for each Ready Task and notifies you in {notifier}.'),
  ph:[s=>{cyc(s,'2:30 PM','read Tracker: 4 Ready',`<span class="g">spawn</span> ol-add-rate-limit`,`<span class="g">spawn</span> ol-${X} <span class="d">(Exploration Worker)</span>`,`<span class="g">spawn</span> ol-fix-flaky-export`,`<span class="y">gated</span> retry-budget ← #11 is not Done`);
     ['add-rate-limit',X,'fix-flaky-export'].forEach(k=>{mv(s,k,'Working');pn(s,k,`<span class="d">worktree .openloops/worktrees/${k}</span>`)})},
   s=>['add-rate-limit',X,'fix-flaky-export'].forEach(k=>nt(s,'2:30 PM','spawned',`🚀 Picked up: <b>${s.tasks[k].title}</b>`)),
   s=>{pn(s,'add-rate-limit','<span class="o">●</span> Read(spec.md) · Write(bucket.ts)');pn(s,'fix-flaky-export','<span class="o">●</span> Bash(run test ×20) → <span class="r">3 fail</span>');pn(s,X,'<span class="o">●</span> measure baseline');row(s,0)}],
  b:[[['host','Each Cycle is a new agent session. A state file is its only memory.']],
     [['runtime','Each Worker is its own coding agent in its own Workspace, a git worktree. It builds, tests and reviews its work until the Spec is met.']]]},
 {t:'3:00–4:00 PM',who:'worker',head:'Quiet Cycles, and one Blocked Task.',
  sum:'If nothing changed, the Change check starts no Cycle and spends no tokens. A Worker that needs something only you have stops and asks.',
  ph:[s=>{skip(s,'3:00 PM',1);pn(s,'add-rate-limit','<span class="o">●</span> Bash(npm test) → <span class="g">12 new tests pass</span>')},
   s=>{pn(s,'fix-flaky-export','<span class="y">I need a 10k-row sample export. I cannot make one without real data.</span>',false);mv(s,'fix-flaky-export','Blocked');s.tasks['fix-flaky-export'].tag='needs a sample file'},
   s=>{cyc(s,'4:00 PM','<span class="y">blocked</span> #13 → notify Owner once');nt(s,'4:00 PM','blocked','⛔ Blocked: <b>Fix the flaky export test</b> needs a sample export file.')}],
  b:[[['pane:fix-flaky-export','A Worker that cannot go on moves its Task to Blocked. It does not guess.'],['note:last','The Notifier tells you once, with what the Worker needs. It does not repeat.']]]},
 {t:'4:10 PM',who:'worker',head:f('A draft {PR}, with notes.'),
  sum:f('When a Worker meets its Spec, it opens a draft {PR}, moves its Task to In Review and writes implementation notes.'),
  ph:[s=>{pn(s,'add-rate-limit','<span class="o">●</span> Skill(review) → 2 findings fixed');pn(s,'add-rate-limit',`<span class="g">✓ 48 tests pass · draft ${ref(41)}</span>`,false);
     s.prs[41]={title:'Add a token-bucket rate limit per API key',slug:'add-rate-limit',state:'draft',check:'pass',rev:1,c:[],body:'Token bucket per API key, stored in the existing Redis. 48 tests pass. Two open questions are in the implementation notes.'};mv(s,'add-rate-limit','In Review');s.tasks['add-rate-limit'].pr=41},
   s=>{cyc(s,'4:30 PM',`<span class="g">in_review</span> #11 · ${ref(41)}`);nt(s,'4:30 PM','in_review',`👀 Ready for review: <b>Add a rate limit</b> · ${ref(41)}`)}],
  acts:[{p:0},{p:1},{click:'card:add-rate-limit'},{pop:['pr','art'],pr:41,art:'notes'}],ui:{pops:['pr','art'],pr:41,art:'notes'},
  b:[[['pr',f('The Worker opens a draft {PR} with a description for reviewers. Tests and {check} pass before it asks for your Review.')]],
     [['art','Implementation notes hold the decisions, tradeoffs and open questions that the Spec did not settle. You can review the work without watching the Worker.']]]},
 {t:'5:05–6:00 PM',who:'you',head:'Your Review comment brings the Worker back.',
  sum:'A Review comment starts a new Worker in the same worktree. It replies, or changes the code, and pushes a new revision.',
  ph:[s=>{s.prs[41].c.push({who:'you',x:'Keep the IP as the fallback, but key on the API key first. Add a test for a missing key.',st:'trusted',f:'src/ratelimit/bucket.ts:42'})},
   s=>{cyc(s,'5:30 PM','<span class="g">respawn</span> ol-add-rate-limit <span class="d">trigger: comments</span>');mv(s,'add-rate-limit','Working');pn(s,'add-rate-limit','<span class="d">── respawn · same worktree ──</span>');nt(s,'5:30 PM','respawned','🔁 Back on <b>Add a rate limit</b>: 1 Review comment')},
   s=>{s.prs[41].c.push({who:'ol-add-rate-limit',x:'Done: keyed on the API key, with the IP as fallback, and a test for a missing key. Pushed revision 2.',st:'reply'});s.prs[41].rev=2;pn(s,'add-rate-limit','<span class="o">●</span> Edit(bucket.ts) · pushed revision 2',false);mv(s,'add-rate-limit','In Review');nt(s,'6:00 PM','in_review',`👀 Review round done: ${ref(41)}`)}],
  acts:[{click:'card:add-rate-limit'},{pop:['pr'],pr:41},{type:'box:pr',text:'Keep the IP as the fallback, but key on the API key first. Add a test for a missing key.'},{click:'btn:pr'},{p:0,w:900},{p:1,w:1300},{p:2}],ui:{pops:['pr'],pr:41},
  b:[[['pr:c0',f('Review the {PR} as you would for a teammate. A comment from a trusted author starts a Review round.')],['pr:c1','A new Worker in the same worktree replies to each comment, or changes the code and pushes a new revision.']]]},
 {t:'5:45–7:30 PM',who:'cycle',head:'Unblocked, and a failed Check fixed.',
  sum:f('When you clear a blocker, the Task goes back to Ready and its Worker starts again. A failed {check} also brings a Worker back, with no comment needed.'),
  ph:[s=>{s.tasks['fix-flaky-export'].tag='sample attached ✓'},
   s=>{delete s.tasks['fix-flaky-export'].tag;cyc(s,'6:00 PM','<span class="g">unblocked</span> #13 → Ready → spawn');mv(s,'fix-flaky-export','Working');pn(s,'fix-flaky-export','<span class="d">── respawn · unblocked ──</span>');pn(s,'fix-flaky-export','<span class="o">●</span> cause: export sorts by a non-unique key');nt(s,'6:00 PM','unblocked','✅ Unblocked: <b>Fix the flaky export test</b>')},
   s=>{cyc(s,'7:30 PM','<span class="g">respawn</span> ol-add-rate-limit <span class="d">trigger: failed check</span>');s.panes['add-rate-limit'].alive=true;pn(s,'add-rate-limit','<span class="d">── respawn · failed check ──</span>');pn(s,'add-rate-limit','<span class="g">✓ lint fixed · pushed revision 3</span>',false);s.prs[41].rev=3;nt(s,'7:30 PM','respawned',`🔁 Back on <b>Add a rate limit</b>: failed ${K.check}`)}],
  acts:[{click:'card:fix-flaky-export'},{p:0,w:1000},{cursor:0},{p:1,w:1400},{p:2}],b:[]},
 {t:'9:00–10:00 PM',who:'you',head:'A Follow-up on the Task.',
  sum:'A Task comment that starts with ACTION: is a Follow-up. It triggers a new Worker, which does the work, updates the PR and moves the Task back to In Review.'.replace('PR',K.PR),
  ph:[s=>{pn(s,'fix-flaky-export',`<span class="g">✓ 200 of 200 runs pass · draft ${ref(42)}</span>`,false);s.prs[42]={title:'Make the export order stable',slug:'fix-flaky-export',state:'draft',check:'pass',rev:1,c:[]};s.tasks['fix-flaky-export'].pr=42;mv(s,'fix-flaky-export','In Review');
     s.tasks['fix-flaky-export'].c.push({who:'ol-fix-flaky-export',x:`Opened ${ref(42)}: a stable sort key and a regression test. 200 of 200 runs pass.`});nt(s,'9:30 PM','in_review',`👀 Ready for review: <b>Fix the flaky export test</b> · ${ref(42)}`)},
   s=>{s.tasks['fix-flaky-export'].c.push({who:'you',x:'ACTION: also add a test for an empty export.'});s.tasks['fix-flaky-export'].fu=true},
   s=>{cyc(s,'10:00 PM','<span class="g">respawn</span> ol-fix-flaky-export <span class="d">trigger: follow-up</span>');mv(s,'fix-flaky-export','Working');s.panes['fix-flaky-export'].alive=true;pn(s,'fix-flaky-export','<span class="d">── respawn · follow-up ──</span>');nt(s,'10:00 PM','respawned','🔁 Back on <b>Fix the flaky export test</b>: Follow-up')},
   s=>{delete s.tasks['fix-flaky-export'].fu;pn(s,'fix-flaky-export',`<span class="g">✓ empty-export test added · ${ref(42)} updated</span>`,false);s.prs[42].rev=2;mv(s,'fix-flaky-export','In Review')}],
  acts:[{p:0,w:1000},{click:'card:fix-flaky-export'},{pop:['panel']},{type:'box:panel',text:'ACTION: also add a test for an empty export.'},{click:'btn:panel'},{p:1,w:1000},{close:1},{cursor:0},{p:2,w:1400,say:1},{p:3}],b:[]},
 {t:'10:30 PM–3:30 AM',who:'worker',head:'Overnight, the Exploration Worker hill-climbs.',
  sum:f('The Exploration Worker runs auto-research overnight. It hill-climbs one metric: one idea per experiment, keep what improves {metric}, revert the rest.'),
  ph:[s=>{skip(s,'10:30 PM–3:30 AM',11);pn(s,X,'<span class="o">●</span> experiment loop · budget 6 h')},...E.rows.slice(1).map((_,i)=>s=>row(s,i+1))],
  acts:[{p:0,w:600},...E.rows.slice(1).map((_,i)=>({p:i+1,w:650}))],
  b:[[['pane:'+X,'Each experiment is a commit with its result. The branch keeps only what works.']]]},
 {t:'3:40 AM',who:'worker',head:'Findings, ready for a decision.',
  sum:'When the time budget is spent, the Worker writes a findings report: every experiment, the decisions for you, and the ideas it did not try.',
  ph:[s=>{pn(s,X,`<span class="w">budget spent · report.html · draft ${ref(43)}</span>`,false);s.prs[43]={title:E.title,slug:X,state:'draft',check:'pass',rev:1,c:[]};mv(s,X,'In Review');s.tasks[X].pr=43},
   s=>{cyc(s,'4:00 AM',`<span class="g">in_review</span> #14 · ${ref(43)}`);nt(s,'4:00 AM','in_review',`🔬 Findings ready: <b>${E.title}</b> · ${E.rows.length-1} ideas, ${kept} kept · ${E.fmt(E.rows[0][1])} → ${E.fmt(best)}`)}],
  acts:[{p:0},{p:1},{click:'card:'+X},{pop:['art'],art:'report'}],ui:{pops:['art'],art:'report'},b:[]},
 {t:'8:20–8:30 AM',who:'you',head:'You merge. Gated Tasks start.',
  sum:f('You merge the {PR}s; no agent merges. Merged Tasks move to Done, and the Tasks that waited for them start.'),
  ph:[s=>{s.prs[41].state='open'},s=>{s.prs[41].state='merged';s.prs[42].state='merged';skip(s,'4:30–8:00 AM',8)},
   s=>{cyc(s,'8:30 AM','<span class="g">done</span> #11, #13','<span class="g">spawn</span> ol-retry-budget <span class="d">(upstream #11 is Done)</span>');mv(s,'add-rate-limit','Done');mv(s,'fix-flaky-export','Done');delete s.tasks['retry-budget'].gated;mv(s,'retry-budget','Working');pn(s,'retry-budget','<span class="d">worktree .openloops/worktrees/retry-budget</span>');
     nt(s,'8:30 AM','done','🎉 Done: <b>Add a rate limit</b>, <b>Fix the flaky export test</b>');nt(s,'8:30 AM','spawned','🚀 Picked up: <b>Retry budget for clients</b>')}],
  acts:[{click:'card:add-rate-limit'},{pop:['pr'],pr:41},{click:'btn:ready'},{p:0,w:700},{click:'btn:merge'},{p:1,w:1000},{close:1},{cursor:0},{p:2}],b:[]},
 {t:'8:35 AM',who:'you',head:'Your night.',
  sum:'While you were away, Workers built, reviewed, fixed and explored, and left notes for each decision. You wrote Specs and comments, and you merged.',ph:[],b:[]}];
 S.forEach(x=>{x.acts=x.acts||x.ph.map((_,i)=>({p:i}));x.ui=x.ui||{pops:[]}});
 return {S,init}}
function stateAt(story,i,k){const s=story.init();for(let a=0;a<=i;a++){const ph=story.S[a].ph,n=a===i&&k!=null?k:ph.length-1;for(let j=0;j<=n;j++)ph[j](s)}return s}

/* =================== renderers =================== */
const STORY=buildStory(K);
const LC={Build:['#ddf4ff','#0969da'],Exploration:['#fbefff','#8250df'],Gated:['#fff8c5','#9a6700'],Blocked:['#ffebe9','#cf222e'],PR:['#dafbe1','#1a7f37'],FU:['#fff8c5','#9a6700']};
const lab=(t,k)=>{const c=LC[k];return `<span class="lbl" style="background:${c[0]};color:${c[1]};border-color:${c[1]}44">${t}</span>`};
const COLC=['#8c959f','#1a7f37','#bf8700','#cf222e','#8250df','#0969da'];
const tasksIn=(s,st)=>Object.keys(s.tasks).filter(k=>s.tasks[k].state===st).sort((a,b)=>s.tasks[a].n-s.tasks[b].n);
var board=s=>`<div class="gh-top"><span class="oct"></span><b>acme</b>&nbsp;/&nbsp;<b>Open Loops</b><span class="tabs"><span class="on">Board</span><span>Table</span><span>Roadmap</span></span></div>
<div class="board">${ST.map((st,i)=>{const ks=tasksIn(s,st);return `<div class="col gh"><h5><i style="border-color:${COLC[i]}"></i>${K.cols[i]}<span>${ks.length}</span></h5>${ks.map(k=>{const t=s.tasks[k];
 return `<div class="card gh" data-t="card:${k}" data-k="card:${k}"><div class="r"><i class="${t.state==='Done'?'cl':''}"></i>${t.repo} #${t.n}</div><div class="t">${t.title}</div>${lab(t.kind,t.kind)}${t.gated?lab('Gated','Gated'):''}${t.tag?lab(t.tag,'Blocked'):''}${t.fu?lab('💬 ACTION','FU'):''}${t.pr?lab('↳ '+K.pr(t.pr),'PR'):''}</div>`}).join('')}</div>`}).join('')}</div>`;
var hostW=s=>{const N=s.host.length,from=Math.max(0,N-13);let lastSkip=-1;s.host.forEach((l,i)=>{if(l.includes('change check'))lastSkip=i});
 return `<div class="tt"><i></i><i></i><i></i><b>${K.host}</b><span class="tr">cron */30 · ${K.hostCmd}</span></div>
 <div class="cc-box">✻ Claude Code · headless (-p) · Orchestrator prompt</div>
 <div class="lines">${s.host.slice(from).map((l,j)=>`<div data-k="h:${from+j}" ${from+j===lastSkip?'data-t="host:skip"':''}>${l}</div>`).join('')||'<span class="d">waiting for the next Cycle…</span>'}</div>
 <div class="foot">Cycles run ${s.cycles} · skipped by Change check ${s.skipped}</div>`};
var runtimeW=s=>{const ks=Object.keys(s.panes),ex=s.rows.length>1;return `<div class="hd-tabs"><span class="on">herdr-core</span>${ks.map(k=>`<span>ol-${k}</span>`).join('')}</div>
<div class="panes ${ex?'ex':''}">${ks.map(k=>{const p=s.panes[k],isX=k===K.ex.slug,L=p.lines.length,from=Math.max(0,L-(isX?2:3));
 return `<div class="pane ${p.alive?'':'dead'} ${ex?(isX?'big':'mini'):''}" data-t="pane:${k}" data-k="pane:${k}"><div class="ph"><span>ol-${k}</span><span>${p.alive?'● live':'○ exited'}</span></div><div class="pl">${p.lines.slice(from).map((l,j)=>`<div data-k="pl:${k}:${from+j}">${l}</div>`).join('')}</div>
 ${isX&&s.rows.length?`<table class="res">${s.rows.map(r=>`<tr data-k="r:${r.n}" class="${r.keep?'k':'v'}"><td>#${r.n}</td><td>${r.idea}</td><td>${K.ex.fmt(r.v)}</td><td>${r.n===0?'base':r.keep?'keep':'revert'}</td></tr>`).join('')}</table>`:''}</div>`}).join('')||'<div class="lines d">no Workers yet</div>'}</div>`};
var slackW=s=>{const N=s.notes.length,from=Math.max(0,N-9);return `<div class="sl"><div class="sl-side"><div class="ws">${K.ws}</div><div class="c"># general</div><div class="c on"># ${K.chan}</div><div class="c"># team</div></div>
<div class="sl-main"><div class="sl-h"># ${K.chan}</div><div class="sl-msgs">${s.notes.slice(from).map((m,j)=>`<div class="sm" data-k="n:${from+j}" ${from+j===N-1?'data-t="note:last"':''}><div class="a">${K.bot[0]}</div><div><div class="n">${K.bot}<span class="app">APP</span><small>${m.t}</small></div><div class="x"><span class="ev">${m.ev}</span> ${m.m}</div></div></div>`).join('')||'<div class="sm"><div class="x" style="color:#888">No messages yet.</div></div>'}</div>
<div class="sl-in">Message #${K.chan}</div></div></div>`};
const cmts=(p,n)=>p.c.map((c,i)=>`<div class="ghc" style="--av:${c.who==='you'?'#f5a524':'#0f9d8a'}" data-t="pr:c${i}" data-k="c:${n}:${i}"><div class="h"><b>${c.who}</b> commented${c.f?` on <code>${c.f}</code>`:''}</div><div class="b">${c.x}</div></div>`).join('');
var prW=(s,n)=>{const p=s.prs[n];return `<div class="br"><i></i><i></i><i></i><div class="url">github.com/${s.tasks[p.slug].repo}/pull/${n}</div></div><div class="ghpr">
<h3>${p.title} <span>#${n}</span></h3><div class="st"><span class="pill ${p.state}">${p.state==='draft'?'◌ Draft':p.state==='open'?'⮂ Open':'⮂ Merged'}</span><span><b>ol-${p.slug}</b> → <b>main</b> · ${p.rev} commit${p.rev>1?'s':''}</span></div>
${p.body?`<div class="ghc" style="--av:#0f9d8a" data-t="pr:body"><div class="h"><b>ol-${p.slug}</b> opened this pull request</div><div class="b">${p.body}</div></div>`:''}${cmts(p,n)}
<div class="ghchk ok"><div class="ic">✓</div><div><b>All checks have passed</b><div class="sm2">${K.check} · 3 successful checks</div></div>${p.state==='draft'?'<span class="mergebtn dr" data-t="btn:ready">Ready for review</span>':`<span class="mergebtn ${p.state==='merged'?'m':''}" data-t="btn:merge">${p.state==='merged'?'Merged by you':'Merge pull request'}</span>`}</div>${p.state==='draft'?'<div class="sm2" style="margin:4px 0 0 40px">This pull request is still a draft. It cannot be merged until you mark it ready for review.</div>':''}
${p.state==='merged'?'':`<div class="ghbox"><div class="ta" data-t="box:pr">Leave a comment</div><span class="cbtn" data-t="btn:pr">Comment</span></div>`}</div>`};
var panelW=s=>{const k='fix-flaky-export',t=s.tasks[k];return `<div class="pnl-h"><b>${t.title}</b><span>${t.repo} #${t.n}</span></div>
<div class="pnl-b"><div class="pnl-d">Spec: <code>specs/${k}.md</code></div>${t.c.map((c,i)=>`<div class="pnl-c" data-k="tc:${i}"><b>${c.who}</b><div>${c.x}</div></div>`).join('')}
<div class="pnl-box"><div class="ta" data-t="box:panel">Add a comment</div><span class="cbtn" data-t="btn:panel">Comment</span></div></div>`};
var notesW=s=>`<div class="br"><i></i><i></i><i></i><div class="url">file:///…/.openloops/add-rate-limit/implementation-notes.html</div></div><div class="art">
<h2>Implementation notes · add-rate-limit</h2><div class="sub">ol-add-rate-limit · 2:30–4:10 PM · ${K.ref(41)} · 48 tests pass · review skill: 2 findings fixed</div>
<div class="g2"><div><h4>Design decisions</h4><ul><li>Token bucket, not a fixed window: it allows short bursts. The Spec did not say.</li><li>Buckets live in the existing Redis. No new service.</li></ul></div>
<div><h4>Tradeoffs</h4><ul><li>An in-memory bucket was 0.4 ms faster, but it breaks with 2+ instances. Chose Redis.</li></ul></div>
<div><h4>Deviations</h4><ul><li>None.</li></ul></div>
<div class="q"><h4>Open questions</h4><ul><li>Requests with no API key fall back to the client IP. Keep that, or reject them?</li><li>Is 100 requests/min per key right for all plans?</li></ul></div></div>
<div class="resp"><b>Summary at exit.</b> 6 files changed, 1 commit, draft ${K.PR}. Waiting for your answer to the open questions.</div></div>`;
var reportW=s=>{const E=K.ex,r=E.rows,lo=E.better==='lower',vals=r.map(x=>x[1]),mn=Math.min(...vals),mx=Math.max(...vals),W=600,H=150,px=i=>34+i*(W-60)/(r.length-1),py=v=>18+(lo?(v-mn):(mx-v))/(mx-mn||1)*(H-42);
 let best=[],b=r[0][1];r.forEach(x=>{if(x[2])b=x[1];best.push(b)});const kept=r.filter(x=>x[2]).length-1;
 return `<div class="br"><i></i><i></i><i></i><div class="url">file:///…/.openloops/${E.slug}/report.html</div></div><div class="art">
<h2>Findings · ${E.title}</h2><div class="sub">Exploration Worker · 2:30 PM–3:40 AM · hypothesis: ${E.hyp}</div>
<div class="sum"><div>baseline<b>${E.fmt(r[0][1])}</b></div><div>best<b style="color:#0b7b6c">${E.fmt(best[best.length-1])}</b></div><div>ideas tried<b>${r.length-1}</b></div><div>kept<b>${kept}</b></div></div>
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" style="background:#fafafa;border-radius:8px;display:block"><polyline fill="none" stroke="#0f9d8a" stroke-width="2.5" points="${best.map((v,i)=>px(i)+','+py(v)).join(' ')}"/>
${r.map((x,i)=>`<circle cx="${px(i)}" cy="${py(x[1])}" r="5" fill="${x[2]?'#0f9d8a':'#fff'}" stroke="${x[2]?'#0f9d8a':'#9ca3af'}" stroke-width="2"/><text x="${px(i)}" y="${H-6}" font-size="10" text-anchor="middle" fill="#888">#${i}</text>`).join('')}
<text x="8" y="12" font-size="10" fill="#888">${E.metric} · up = better (${E.better} ${E.metric}) · line = best so far</text></svg>
<table style="margin-top:8px"><tr><th>#</th><th>idea</th><th>${E.metric}</th><th></th></tr>${r.map((x,i)=>`<tr><td>${i}</td><td>${x[0]}</td><td>${E.fmt(x[1])}</td><td class="${x[2]?'kept':'rev'}">${i===0?'baseline':x[2]?'kept':'reverted'}</td></tr>`).join('')}</table>
<div class="g2"><div><h4>Decisions for you</h4><ul>${E.decide.map(x=>`<li>${x}</li>`).join('')}</ul></div><div><h4>Not tried yet</h4><ul>${E.next.map(x=>`<li>${x}</li>`).join('')}</ul></div></div></div>`};
const LAY={tracker:[0,0,950,440],notifier:[970,0,430,800],host:[0,460,430,340],runtime:[450,460,500,340],pr:[40,30,640,0],art:[700,30,680,0],artSolo:[250,20,700,0],panel:[520,50,420,380]};
const posS=k=>`left:${LAY[k][0]}px;top:${LAY[k][1]}px;width:${LAY[k][2]}px;`+(LAY[k][3]?`height:${LAY[k][3]}px`:'max-height:770px');
function deskHTML(s,ui){const op=ui.pops||[];
 let h=`<div class="win" style="${posS('tracker')}" data-t="tracker">${board(s)}</div>
 <div class="win term" style="${posS('host')}" data-t="host">${hostW(s)}</div>
 <div class="win term" style="${posS('runtime')}" data-t="runtime">${runtimeW(s)}</div>
 <div class="win" style="${posS('notifier')}" data-t="notifier">${slackW(s)}</div>`;
 if(op.includes('pr')&&s.prs[ui.pr])h+=`<div class="win pop" style="${posS('pr')}" data-t="pr" data-k="pop:pr">${prW(s,ui.pr)}</div>`;
 if(op.includes('art'))h+=`<div class="win pop" style="${posS(op.includes('pr')?'art':'artSolo')}" data-t="art" data-k="pop:art">${ui.art==='notes'?notesW(s):reportW(s)}</div>`;
 if(op.includes('panel'))h+=`<div class="win pop panel" style="${posS('panel')}" data-t="panel" data-k="pop:panel">${panelW(s)}</div>`;
 return h}

/* =================== frame renderer: FLIP moves + enter animations =================== */
const $=id=>document.getElementById(id);
function rectOf(el){let x=0,y=0,e=el;const desk=$('desk');while(e&&e!==desk){x+=e.offsetLeft;y+=e.offsetTop;e=e.offsetParent}return{x,y,w:el.offsetWidth,h:el.offsetHeight}}
let lastKeys=new Set();
function frame(s,ui,animate){const c=$('content'),old={};if(animate)c.querySelectorAll('[data-k^="card:"]').forEach(el=>old[el.dataset.k]=rectOf(el));
 c.innerHTML=deskHTML(s,ui);const keys=new Set();let n=0;
 c.querySelectorAll('[data-k]').forEach(el=>{const k=el.dataset.k;keys.add(k);if(!animate)return;
  if(old[k]){const r=rectOf(el),dx=old[k].x-r.x,dy=old[k].y-r.y;if(dx||dy){el.style.transition='none';el.style.transform=`translate(${dx}px,${dy}px)`;el.classList.add('flying');requestAnimationFrame(()=>requestAnimationFrame(()=>{el.style.transition=`transform ${1/SPEED}s cubic-bezier(.65,0,.35,1)`;el.style.transform=''}));setTimeout(()=>el.classList.remove('flying'),1300/SPEED)}}
  else if(!lastKeys.has(k)){el.classList.add(k.startsWith('pop:')?'pop-in':'enter');el.style.animationDelay=(k.startsWith('pop:')?0:Math.min(n++,8)*110/SPEED)+'ms'}});
 lastKeys=keys}

/* =================== tour engine =================== */
var step=0,beat=0,timer=null,base=1,tok=0,busy=false,SPEED=1;
function setSpeed(x){SPEED=x;document.documentElement.style.setProperty('--sp',x)}
const WHO={you:'You',cycle:'Cycle',worker:'Worker',check:'Check'};
const wait=ms=>new Promise(r=>setTimeout(r,ms/SPEED));
function setT(tx,ty,sc){$('desk').style.transform=`translate(${tx}px,${ty}px) scale(${sc})`;$('desk').dataset.z=sc>base*1.01?'1':''}
function find(tk){return $('content').querySelector(`[data-t="${tk}"]`)}
const vpH=()=>$('vp').clientHeight-(window.TOUR_CTL_H||70);
function overviewT(){const vw=$('vp').clientWidth,top=118;base=Math.min((vw-24)/1400,(vpH()-top)/800);setT((vw-1400*base)/2,top,base)}
function clearFocus(){$('dim').classList.remove('on');$('rings').innerHTML='';$('callouts').innerHTML=''}
function caption(st,s){$('cap').innerHTML=`<span class="clock">${st.t}</span><span class="who ${st.who}">${WHO[st.who]}</span><span class="head">${st.head}</span><span class="cnt">${ST.map((x,i)=>`${x} ${Object.values(s.tasks).filter(t=>t.state===x).length}`).join(' · ')}</span>`}
function showOverview(st){$('callouts').innerHTML=`<div class="co ov"><div class="k">${st.t}</div><div class="tx">${st.sum}</div></div>`;requestAnimationFrame(()=>$('callouts').firstChild.classList.add('on'))}
async function cursorTo(tk,t){const el=find(tk);if(!el)return;const r=rectOf(el),cu=$('cursor');cu.classList.add('on');cu.style.left=(r.x+Math.min(r.w*.6,r.w-12))+'px';cu.style.top=(r.y+Math.min(r.h*.55,r.h-8))+'px';await wait(800);if(t!==tok)return;cu.classList.add('click');await wait(380);cu.classList.remove('click')}
async function typeInto(tk,text,t){const el=find(tk);if(!el)return;el.classList.add('typing');el.textContent='';for(const ch of text){if(t!==tok)return;el.textContent+=ch;await wait(28)}await wait(300)}
// animated entry into step i: zoom out, close popups, play the acts, then the bird's-eye text
async function enter(i){const t=++tok;busy=true;clearFocus();const st=STORY.S[i];
 const wasZoomed=$('desk').dataset.z==='1';overviewT();if(wasZoomed)await wait(1000);if(t!==tok)return;
 let ui={pops:[]},said=false;const prev=i>0?stateAt(STORY,i-1):STORY.init();
 $('content').querySelectorAll('.pop').forEach(p=>p.classList.add('pop-out'));await wait(350);if(t!==tok)return;
 frame(prev,ui,false);caption(st,prev);window.onBeat&&window.onBeat();let k=-1;await wait(400);
 for(const a of st.acts){if(t!==tok)return;
  if(a.p!=null){k=a.p;const s=stateAt(STORY,i,k);frame(s,ui,true);caption(st,s);await wait(a.w||1150)}
  else if(a.w&&a.p==null&&!a.click&&!a.pop&&!a.type)await wait(a.w);
  if(a.click)await cursorTo(a.click,t);
  if(a.pop){ui={pops:a.pop,pr:a.pr,art:a.art};frame(stateAt(STORY,i,k),ui,true);await wait(800)}
  if(a.type)await typeInto(a.type,a.text,t);
  if(a.close){ui={pops:[]};$('content').querySelectorAll('.pop').forEach(p=>p.classList.add('pop-out'));await wait(350);frame(stateAt(STORY,i,k),ui,true)}
  if(a.cursor===0)$('cursor').classList.remove('on');
  if(a.say){$('cursor').classList.remove('on');showOverview(st);said=true;await wait(Math.max(3200,st.sum.length*48));if(t!==tok)return}}
 if(t!==tok)return;$('cursor').classList.remove('on');if(!said)showOverview(st);busy=false;window.onBeat&&window.onBeat()}
function jump(i,b){tok++;busy=false;step=i;beat=b;clearFocus();$('cursor').classList.remove('on');const st=STORY.S[i],s=stateAt(STORY,i);frame(s,st.ui,false);caption(st,s);overviewT();if(b===0){showOverview(st);window.onBeat&&window.onBeat()}else closeUp()}
function closeUp(){const st=STORY.S[step],tg=st.b[beat-1];clearFocus();const els=tg.map(([tk,txt])=>[find(tk),txt]).filter(x=>x[0]);if(!els.length){overviewT();return}
 const pad=els.length>1?6:12,vw=$('vp').clientWidth,vh=vpH(),room=370,rs=els.map(([el])=>{const r=rectOf(el),w=el.closest('.win');if(w&&w!==el){const c=rectOf(w);const x1=Math.max(r.x,c.x),y1=Math.max(r.y,c.y);return{x:x1,y:y1,w:Math.max(20,Math.min(r.x+r.w,c.x+c.w)-x1),h:Math.max(20,Math.min(r.y+r.h,c.y+c.h)-y1),c}}return{...r,c:r}});
 // context box: union of targets, grown to ~560×300 inside their window
 let z={x:Math.min(...rs.map(r=>r.x)),y:Math.min(...rs.map(r=>r.y))};z.w=Math.max(...rs.map(r=>r.x+r.w))-z.x;z.h=Math.max(...rs.map(r=>r.y+r.h))-z.y;
 if(rs.length===1){const c=rs[0].c,mw=Math.min(c.w,560),mh=Math.min(c.h,300);if(z.w<mw){z.x=Math.min(Math.max(c.x,z.x+z.w/2-mw/2),c.x+c.w-mw);z.w=mw}if(z.h<mh){z.y=Math.min(Math.max(c.y,z.y+z.h/2-mh/2),c.y+c.h-mh);z.h=mh}}
 let sc=Math.min((vw-room-60)/(z.w+2*pad),(vh-40)/(z.h+2*pad),base*2);sc=Math.max(sc,base*1.05);
 const tx=(vw-room)/2-(z.x+z.w/2)*sc,ty=vh/2-(z.y+z.h/2)*sc;setT(tx,ty,sc);
 // dim everything except the targets (one overlay with holes)
 const holes=rs.map(r=>`M${r.x-pad} ${r.y-pad}h${r.w+2*pad}v${r.h+2*pad}h${-(r.w+2*pad)}Z`).join(' ');
 $('dim').style.clipPath=`path(evenodd,'M-3000 -3000H5000V5000H-3000Z ${holes}')`;$('dim').classList.add('on');
 $('rings').innerHTML=rs.map(r=>`<div class="ring" style="left:${r.x-pad}px;top:${r.y-pad}px;width:${r.w+2*pad}px;height:${r.h+2*pad}px"></div>`).join('');
 const t=tok;setTimeout(()=>{if(t!==tok)return;const placed=[];$('callouts').innerHTML='';
  rs.forEach((r,i)=>{const sx=tx+(r.x-pad)*sc,sy=ty+(r.y-pad)*sc,sw=(r.w+2*pad)*sc;let left=sx+sw+22;if(left+340>vw)left=Math.max(12,sx-362);let top=Math.min(Math.max(12,sy),vh-120);
   placed.forEach(p=>{if(Math.abs(p.left-left)<340&&top<p.top+p.h+10&&top+90>p.top)top=p.top+p.h+12});
   const d=document.createElement('div');d.className='co zm';d.style.left=left+'px';d.style.top=top+'px';d.innerHTML=`<div class="tx">${els[i][1]}</div>`;$('callouts').appendChild(d);placed.push({left,top,h:d.offsetHeight});requestAnimationFrame(()=>d.classList.add('on'))})},950/SPEED);
 window.onBeat&&window.onBeat()}
function fwd(){if(busy){jump(step,0);return}if(beat<STORY.S[step].b.length){beat++;closeUp()}else if(step<STORY.S.length-1){step++;beat=0;enter(step)}}
function back(){if(beat>0){beat--;if(beat===0){clearFocus();overviewT();showOverview(STORY.S[step]);window.onBeat&&window.onBeat()}else closeUp()}else if(step>0)jump(step-1,STORY.S[step-1].b.length)}
function atEnd(){return step===STORY.S.length-1&&beat===STORY.S[step].b.length&&!busy}
function readMs(){const st=STORY.S[step];const txt=beat===0?st.sum:st.b[beat-1].map(x=>x[1]).join(' ');return (Math.max(3200,txt.length*48)+(beat===0?0:900))/SPEED}
function stopPlay(){clearTimeout(timer);timer=null;window.onPlay&&window.onPlay(false)}
function play(){if(timer){stopPlay();return}window.onPlay&&window.onPlay(true);const tick=async()=>{if(atEnd()){stopPlay();return}if(busy){timer=setTimeout(tick,300);return}fwd();timer=setTimeout(async function w(){if(busy){timer=setTimeout(w,300);return}timer=setTimeout(tick,readMs())},300)};
 timer=setTimeout(tick,busy?300:readMs())}
