'use strict';
const assert=require('node:assert/strict');
const {frame,CueSound}=require('../web/cues.js');
const ns=s=>s*1e9;
const phases=[
 {index:0,kind:'ready',label:'WATER',state:'',trial:1,start_ns:ns(0),end_ns:ns(2)},
 {index:1,kind:'perform',label:'WATER',state:'sign',trial:1,start_ns:ns(2),end_ns:ns(6)},
 {index:2,kind:'ready',label:'drink',state:'',trial:2,start_ns:ns(6),end_ns:ns(8)},
 {index:3,kind:'perform',label:'drink',state:'activity',trial:2,start_ns:ns(8),end_ns:ns(12)}
];
const active={id:'P00_test',status:'recording',plan:{mode:'meal',start_ns:0,end_ns:ns(12),phases}};
function context(){
 const ctx={currentTime:0,state:'suspended',destination:{},oscillators:[],async resume(){this.state='running';},createGain(){return {gain:{setValueAtTime(){},linearRampToValueAtTime(){}},connect(){}};},createOscillator(){
  const o={frequency:{setValueAtTime(){}},connect(){},starts:[],stops:[],start(t){this.starts.push(t);},stop(t){this.stops.push(t);}};
  this.oscillators.push(o);return o;
 }};return ctx;
}
async function tests(){
 assert.equal(frame(active,ns(1),true).state,'buffer');
 assert.match(frame(active,ns(1),true).heading,/GET READY/);
 assert.equal(frame(active,ns(2),true).state,'event');
 assert.match(frame(active,ns(3),true).heading,/MIXED.*SIGN/);
 assert.equal(frame(active,ns(6),true).state,'buffer');
 assert.match(frame(active,ns(9),true).heading,/MIXED.*ACTIVITY/);
 assert.equal(frame({...active,status:'stopping'},ns(3),true).state,'buffer');
 const ctx=context(),sound=new CueSound(()=>ctx);await sound.enable();
 sound.tick(active,ns(1.5));assert.equal(ctx.oscillators.length,1,'GO is one beep');
 sound.tick(active,ns(1.6));assert.equal(ctx.oscillators.length,1,'refresh does not duplicate GO');
 ctx.currentTime=4;sound.tick(active,ns(5.5));assert.equal(ctx.oscillators.length,3,'STOP adds two beeps');
 assert.ok(Math.abs(ctx.oscillators[2].starts[0]-ctx.oscillators[1].starts[0]-.28)<1e-8);
 ctx.currentTime=4.55;sound.tick(null,ns(6.05));
 assert.equal(ctx.oscillators[2].stops.length,1,'natural completion preserves the second STOP beep');
 const late=context(),resume=new CueSound(()=>late);await resume.enable();
 resume.tick(active,ns(4));assert.equal(late.oscillators.length,0,'no stale GO after reload/resume');
 resume.tick(active,ns(5.5));assert.equal(late.oscillators.length,2,'upcoming STOP still plays');
 const early=context(),stop=new CueSound(()=>early);await stop.enable();
 stop.tick(active,ns(1.5));early.currentTime=1.5;stop.stopNow(active,ns(3));
 assert.equal(early.oscillators.length,3,'manual event stop emits two beeps');
 stop.tick({...active,status:'stopping'},ns(3.1));assert.equal(early.oscillators.length,3);
 const quiet=context(),disabled=new CueSound(()=>quiet);
 disabled.tick(active,ns(1.5));assert.equal(quiet.oscillators.length,0,'audio is not played before user enable');
 console.log('Cue tests passed: red/green, mixed events, one/two beeps, duplicate prevention, late resume, stop tails, manual stop.');
}
tests().catch(e=>{console.error(e);process.exitCode=1;});
