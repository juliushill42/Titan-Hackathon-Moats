'use strict';
const $=id=>document.getElementById(id);
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const req=async(path,method='GET',data)=>{
  const r=await fetch(path,{method,headers:{'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});
  const o=await r.json();if(!r.ok)throw new Error(o.error||'Request failed');return o;
};
let lastRun=null;
function busy(v){$('orb').classList.toggle('busy',v);$('orb-label').textContent=v?'AGENTS EXECUTING':'AWAITING DIRECTIVE';$('send').disabled=v;}
function notice(s){$('notice').textContent=s;}
function renderResult(run){lastRun=run;const x=run.result;let html=`<h3>${safe(x.title)}</h3><p>${safe(x.summary)}</p>`;
 if(x.items&&x.items.length)html+=`<ul>${x.items.map(it=>'<li>'+ (typeof it==='string'?safe(it):Object.entries(it).map(([k,v])=>`<strong>${safe(k.toUpperCase())}</strong>${safe(v)}`).join(' &nbsp; '))+'</li>').join('')}</ul>`;
 if(x.draft)html+=`<pre>${safe(x.draft)}</pre><button class="add" id="copy-draft">COPY EMAIL DRAFT</button>`;
 if(x.overflow&&x.overflow.length)html+=`<p>Overflow: ${safe(x.overflow.join(', '))}</p>`;
 html+=`<p class="mini">EXECUTION CHAIN</p><div class="agent-row">${run.agents.map(a=>`<span class="agent-chip" title="${safe(a.action)}">${safe(a.name)}</span>`).join('')}</div>`;
 html+=`<a class="receipt-link" href="/api/receipt/${encodeURIComponent(run.receipt_id)}" target="_blank" rel="noopener">↓ VIEW VERIFIABLE JSON RECEIPT #${safe(run.receipt_id)}</a>`;
 $('result').innerHTML=html;
 if(x.draft)$('copy-draft').onclick=async()=>{try{await navigator.clipboard.writeText(x.draft);notice('Email draft copied. Nothing was sent.')}catch(e){notice('Clipboard unavailable; select the draft text to copy.')}};
}
async function refresh(){try{const s=await req('/api/state');$('open-tasks').textContent=s.stats.open_tasks;$('blockers').textContent=s.stats.blockers;$('runs').textContent=s.stats.runs;
 $('task-list').innerHTML=s.tasks.map(t=>`<div class="task ${t.status==='done'?'done':''}"><i class="dot-prio ${safe(t.priority)}"></i><span class="task-name">${safe(t.title)} ${t.blocker?'<span class="gold">⚑</span>':''}</span><button data-task="${safe(t.id)}" data-status="${t.status==='done'?'open':'done'}">${t.status==='done'?'REOPEN':'DONE'}</button></div>`).join('')||'<p class="empty">No tasks in this workspace.</p>';
 $('ledger').innerHTML=s.receipts.slice(0,8).map(r=>`<div class="ledger-card"><strong>${safe(r.outcome.title)}</strong><span>${safe(r.intent)} · ${safe(r.created_at)}</span><a href="/api/receipt/${encodeURIComponent(r.id)}" target="_blank" rel="noopener">OPEN RECEIPT ↗</a></div>`).join('')||'<p class="empty">Execute a command to generate the first receipt.</p>';
 $('ledger-count').textContent=`${s.stats.runs} EXECUTIONS RECORDED`;
 for(const b of document.querySelectorAll('[data-task]'))b.onclick=async()=>{try{await req('/api/tasks/'+b.dataset.task,'POST',{status:b.dataset.status});await refresh();notice('Task state updated in SQLite.')}catch(e){notice(e.message)}};
 }catch(e){notice('Local service unavailable: '+e.message)}}
$('command-form').addEventListener('submit',async ev=>{ev.preventDefault();notice('');busy(true);try{const run=await req('/api/command','POST',{command:$('command').value});renderResult(run);await refresh();$('result').scrollIntoView({block:'nearest',behavior:'smooth'});}catch(e){notice(e.message)}finally{busy(false)}});
for(const b of document.querySelectorAll('[data-command]'))b.onclick=()=>$('command').value=b.dataset.command;
$('task-form').addEventListener('submit',async ev=>{ev.preventDefault();try{await req('/api/tasks','POST',{title:$('task-title').value,priority:$('task-priority').value,minutes:Number($('task-minutes').value),project:$('task-project').value,blocker:$('task-blocker').checked});$('task-title').value='';$('task-blocker').checked=false;notice('Task stored locally. Agents will include it in the next run.');await refresh();}catch(e){notice(e.message)}});
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SR){const recognition=new SR();recognition.lang='en-US';recognition.interimResults=false;recognition.maxAlternatives=1;
 recognition.onresult=e=>{$('command').value=e.results[0][0].transcript;notice('Voice command captured. Press EXECUTE to run it.')};
 recognition.onend=()=>$('mic').classList.remove('active');recognition.onerror=e=>notice('Microphone: '+e.error);
 $('mic').onclick=()=>{recognition.start();$('mic').classList.add('active')};
}else{$('mic').onclick=()=>notice('Speech capture unavailable in this browser. Type your directive instead.')}
refresh();setInterval(refresh,5000);

// PUBLIC MISSION FABRIC — only bounded local actions and tool contracts.
let missionId=null, missionPolling=false;
async function renderMission(id){
 if(!id)return;const data=await req('/api/missions/'+id);const m=data.mission;
 $('mission-status').textContent=m.status.toUpperCase();
 const agents=data.steps||[];
 $('mission-stats').textContent=agents.filter(x=>x.status==='running').length+' active workers · '+data.artifacts.length+' generated artifacts · '+data.events.length+' audit events';
 $('mission-agent-board').innerHTML=agents.map((a,i)=>`<div class="mission-agent ${safe(a.status)}"><div class="mini">AGENT ${String(i+1).padStart(2,'0')} <span class="agent-status">${safe(a.status).toUpperCase()}</span></div><strong>${safe(a.agent)}</strong><p>${safe((a.result&&a.result.summary)||'Executing scoped local capability')}</p></div>`).join('')||'<p>Coordinating agents…</p>';
 const proof=data.proof;
 $('mission-evidence').innerHTML='<div class="evidence-title">OUTPUT ARTIFACTS / PROVENANCE</div>'+data.artifacts.map(a=>`<a href="${safe(a.url)}" target="_blank" rel="noopener" class="evidence-file">↗ ${safe(a.name)} <small>SHA256 ${safe(a.sha256.slice(0,20))}…</small></a>`).join('')+
 (proof?`<div class="proof-status"><b>${proof.verified?'INTEGRITY VERIFIED':'INTEGRITY FAILED'}</b><span>${safe(proof.event_count)} chained events · ${safe(proof.steps_passed)} verified steps · ${safe(proof.artifacts)} checked artifacts</span><a target="_blank" rel="noopener" href="/api/missions/${encodeURIComponent(id)}/verify">VIEW CRYPTOGRAPHIC EVIDENCE ↗</a></div>`:'');
 return m.status;
}
$('mission-form').addEventListener('submit',async e=>{
 e.preventDefault();if(missionPolling)return;
 const goal=$('mission-goal').value;const allow_local_writes=$('mission-writes').checked;
 $('mission-launch').disabled=true;$('mission-notice').textContent='Delegating objective to autonomous specialist workers…';
 try{const result=await req('/api/missions','POST',{goal,allow_local_writes});missionId=result.id;missionPolling=true;
   for(let i=0;i<80;i++){const s=await renderMission(missionId);if(['completed','failed','cancelled'].includes(s)){missionPolling=false;break;}await new Promise(r=>setTimeout(r,250));}
   const s=await renderMission(missionId);$('mission-notice').textContent=s==='completed'?'Mission completed. Artifact integrity and audit chain available below.':'Mission status: '+s+'. Review the agent telemetry.';
   await refresh();
 }catch(e){$('mission-notice').textContent=e.message;}finally{missionPolling=false;$('mission-launch').disabled=false;}
});
(async()=>{try{const result=await req('/api/missions');if(result.missions.length){missionId=result.missions[0].id;await renderMission(missionId)}}catch(e){/* optional mission API */}})();