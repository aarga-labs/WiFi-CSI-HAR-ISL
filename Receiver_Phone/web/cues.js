(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.FypCues=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const EVENT_KINDS=new Set(['perform','baseline','ordinary','sync']);
  const pretty=label=>String(label||'').replaceAll('_',' ').toUpperCase();
  function frame(active,now,connected){
    if(!active)return {state:'buffer',heading:'WAIT — NOT RECORDING',label:connected?'START YOUR NAMED COMMAND':'CONNECT THE PHONE',seconds:'—',progress:'Red = preparation / rest · Green = event · 1 beep = start · 2 beeps = stop'};
    if(active.status==='queued')return {state:'buffer',heading:'WAITING FOR PHONE',label:'GET READY',seconds:'—',progress:'Recording starts after the phone confirms.'};
    if(active.status==='stopping')return {state:'buffer',heading:'STOP — SAVING',label:'STAY STILL',seconds:'—',progress:'Keeping the partial recording and transferring it.'};
    const plan=active.plan,p=plan.phases.find(x=>now>=x.start_ns&&now<x.end_ns);
    if(!p)return now<plan.start_ns?
      {state:'buffer',heading:'BUFFER — GET READY',label:pretty(plan.phases[0]?.label||plan.block_title||'GET READY'),seconds:Math.max(0,Math.ceil((plan.start_ns-now)/1e9)),progress:'Wait for green and one beep.'}:
      {state:'buffer',heading:'STOP — SAVING',label:'RECORDING FINISHED',seconds:'—',progress:'Wait for the files to transfer.'};
    const seconds=Math.max(0,Math.ceil((p.end_ns-now)/1e9));
    const next=plan.phases.find(x=>x.index>p.index&&EVENT_KINDS.has(x.kind));
    const total=plan.phases.filter(x=>EVENT_KINDS.has(x.kind)).length;
    const progress=`${plan.pid||''} · ${p.posture||plan.posture||''}${p.trial?' · Trial '+p.trial+' of '+total:''}${p.script_id?' · '+p.script_id+' / run '+p.run:''}`;
    if(EVENT_KINDS.has(p.kind)){
      let category=p.kind==='sync'?'TIMING CHECK':p.kind==='baseline'?'STAY STILL':p.state==='sign'?'SIGN':'ACTIVITY';
      if(['mixed','meal','tv','cleaning'].includes(plan.mode)&&p.kind==='perform')category='MIXED · '+category;
      return {state:'event',heading:'GO — '+category,label:pretty(p.label),seconds,progress,phase:p};
    }
    return {state:'buffer',heading:p.kind==='rest'?'STOP — REST':'BUFFER — GET READY',
      label:p.kind==='rest'?'STAY STILL':pretty(p.label),seconds,
      progress:progress+(next?' · Next: '+pretty(next.label):''),phase:p};
  }
  class CueSound {
    constructor(makeContext){
      this.makeContext=makeContext||(()=>new (window.AudioContext||window.webkitAudioContext)());
      this.context=null;this.enabled=false;this.session=null;this.seen=new Set();this.nodes=[];
    }
    async enable(){
      if(!this.context)this.context=this.makeContext();
      await this.context.resume();
      if(this.context.state!=='running')throw Error('Sound is blocked. Click Enable / test sound, then try again.');
      this.enabled=true;
    }
    tone(count,when){
      if(!this.enabled||!this.context||this.context.state!=='running')return;
      const ctx=this.context,start=Math.max(ctx.currentTime+.015,when);
      this.nodes=this.nodes.filter(x=>x.end>ctx.currentTime);
      for(let i=0;i<count;i++){
        const at=start+i*.28,osc=ctx.createOscillator(),gain=ctx.createGain();
        osc.type='sine';osc.frequency.setValueAtTime(count===1?1000:650,at);
        gain.gain.setValueAtTime(0,at);gain.gain.linearRampToValueAtTime(.24,at+.012);
        gain.gain.setValueAtTime(.24,at+.115);gain.gain.linearRampToValueAtTime(0,at+.14);
        osc.connect(gain);gain.connect(ctx.destination);osc.start(at);osc.stop(at+.16);
        this.nodes.push({osc,end:at+.16,count,cueAt:start});
      }
    }
    cancel(keepStopTail=false){
      const kept=[];
      for(const x of this.nodes){
        if(keepStopTail&&x.count===2&&x.cueAt<=(this.context?.currentTime||0)+.02&&x.end>(this.context?.currentTime||0)){kept.push(x);continue;}
        try{x.osc.stop();}catch{}
      }
      this.nodes=kept;
    }
    mute(){this.enabled=false;this.cancel();}
    test(){if(this.enabled){this.tone(1,this.context.currentTime+.08);this.tone(2,this.context.currentTime+.8);}}
    tick(active,now){
      const sid=active?.id||null;
      if(sid!==this.session){this.cancel(true);this.session=sid;this.seen.clear();}
      if(!active||active.status!=='recording'||!this.enabled||this.context.state!=='running')return;
      for(const p of active.plan.phases){
        if(!EVENT_KINDS.has(p.kind))continue;
        for(const [edge,target,count] of [['start',p.start_ns,1],['stop',p.end_ns,2]]){
          const key=p.index+':'+edge;if(this.seen.has(key))continue;
          const seconds=(target-now)/1e9;
          // Never play a stale GO after a reload/background delay. Schedule ahead.
          if(seconds<0){this.seen.add(key);continue;}
          if(seconds<=.8){this.tone(count,this.context.currentTime+seconds);this.seen.add(key);}
        }
      }
    }
    stopNow(active,now){
      this.cancel();
      if(!active)return;
      const p=active.plan.phases.find(x=>now>=x.start_ns&&now<x.end_ns);
      if(p&&EVENT_KINDS.has(p.kind)&&this.enabled){this.tone(2,this.context.currentTime+.02);this.seen.add(p.index+':stop');}
    }
  }
  return {EVENT_KINDS,frame,CueSound};
});
