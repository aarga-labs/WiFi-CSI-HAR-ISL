'use strict';
const $=id=>document.getElementById(id);
const fragment=new URLSearchParams(location.hash.slice(1));
let token=fragment.get('token')||localStorage.getItem('fyp_pairing')||'';
if(fragment.has('token')){localStorage.setItem('fyp_pairing',token);history.replaceState(null,'',location.pathname);}
$('key').value=token;$('address').value=location.origin;
let snapshot=null,active=null,clock=null,busy=false;
const sound=new FypCues.CueSound();
function error(msg){$('error').textContent=msg;$('error').hidden=!msg;}
async function api(path,data){
 const r=await fetch(path,{method:data?'POST':'GET',headers:{'X-Token':token,...(data?{'Content-Type':'application/json'}:{})},body:data?JSON.stringify(data):undefined});
 const d=await r.json();if(!r.ok)throw Error(d.error||'Request failed');return d;
}
function render(s){
 snapshot=s;clock={ns:s.now_ns,at:performance.now()};
 const d=s.devices[0],connected=d&&d.seen_s_ago<8;
 $('connection').textContent=connected?'Phone connected':'Waiting for phone';$('connection').className='badge '+(connected?'good':'bad');
 $('phoneinfo').textContent=d?`${d.model||'Android phone'} · acceleration ${d.accelerometer?'available':'MISSING'} · gyroscope ${d.gyroscope?'available':'MISSING'} · last seen ${d.seen_s_ago}s ago · clock round trip ${Number(d.clock_rtt_ms||0).toFixed(1)} ms`:'Open and connect the phone app.';
 active=s.sessions.find(x=>['queued','recording','stopping'].includes(x.status))||null;
 $('stop').disabled=!active||busy;$('flag').disabled=!active;
 const out=$('recordings');out.replaceChildren();
 for(const rec of s.sessions){
  const row=document.createElement('div');row.className='record';const text=document.createElement('div');
  const title=document.createElement('strong');title.textContent=rec.id;
  const info=document.createElement('p');info.className='muted';info.textContent=rec.status.replaceAll('_',' ')+' · '+rec.plan.arm+' forearm';
  text.append(title,info);const retry=document.createElement('button');retry.textContent='Retry transfer';
  retry.onclick=()=>run(()=>api('/api/retry',{session_id:rec.id}));row.append(text,retry);out.append(row);
 }
 if(!s.sessions.length)out.textContent='No recordings yet.';
 $('system').textContent=`Local storage: ${(s.disk_free_bytes/1e9).toFixed(1)} GB free · Laptop clock change: ${s.wall_clock_difference_ms.toFixed(1)} ms`;
 const failure=s.commands.find(c=>c.state==='error');
 if(failure){try{error(JSON.parse(failure.result).error||'Phone reported a command error.');}catch{}}
 tick();
}
function current(){
 if(!active||!clock)return null;
 const now=clock.ns+(performance.now()-clock.at)*1e6;
 return {now,phase:active.plan.phases.find(p=>now>=p.start_ns&&now<p.end_ns)};
}
function tick(){
 const now=clock?clock.ns+(performance.now()-clock.at)*1e6:0;
 const f=FypCues.frame(active,now,snapshot?.devices[0]?.seen_s_ago<8);
 $('sessionname').textContent=active?`${active.plan.pid} · ${active.plan.session} · ${active.plan.block_title||active.plan.mode}`:'No active session';
 $('runinfo').textContent=active?`${active.plan.pid} / ${active.plan.session}: ${active.plan.block_title||active.plan.mode}`:'Waiting for a named run.';
 $('cuepanel').dataset.state=f.state;$('phase').textContent=f.heading;
 $('cue').textContent=f.label;$('countdown').textContent=f.seconds;$('progress').textContent=f.progress;
 sound.tick(active,now);
}
async function run(fn){if(busy)return;busy=true;error('');try{await fn();await refresh();}catch(e){error(e.message);}finally{busy=false;}}
async function refresh(){try{render(await api('/api/state'));}catch(e){error(e.message);$('connection').textContent='Controller not available';}}
$('showkey').onclick=()=>{$('key').type=$('key').type==='password'?'text':'password';};
$('soundtest').onclick=()=>run(async()=>{
 await sound.enable();
 if(!active)sound.test();
 $('soundstatus').textContent=active?'Laptop sound enabled for upcoming event boundaries.':'Sound enabled · 1 beep = GO · 2 beeps = STOP';
});
$('fullscreen').onclick=async()=>{
 try{if(document.fullscreenElement)await document.exitFullscreen();else await $('cuepanel').requestFullscreen();}
 catch(e){error('Full screen was unavailable. The coloured prompt still works in this window.');}
};
$('stop').onclick=()=>run(async()=>{
 const stopped=active;await api('/api/stop',{session_id:stopped.id});
 sound.stopNow(stopped,clock.ns+(performance.now()-clock.at)*1e6);
});
$('flag').onclick=()=>run(async()=>{await api('/api/flag',{session_id:active.id,trial:current()?.phase?.trial||null,note:$('flagNote').value||'Operator marked this interval for review'});$('flagNote').value='';});
setInterval(refresh,1000);setInterval(tick,50);refresh();
