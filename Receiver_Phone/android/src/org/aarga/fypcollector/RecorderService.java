package org.aarga.fypcollector;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.hardware.*;
import android.media.*;
import android.os.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

public class RecorderService extends Service {
 public static volatile RecorderService instance;
 HandlerThread sensorThread;Handler sensorHandler;
 volatile Recorder recorder;volatile Wire.Clock clock;
 volatile String lastError="",connection="Connecting",currentPrompt="Waiting for laptop";
 volatile boolean alive=true;String deviceId;Thread worker;PowerManager.WakeLock wake;
 final Object recordingLock=new Object();
 public boolean recording(){return recorder!=null&&recorder.open;}
 public String summary(){
  Recorder r=recorder;
  return connection+"\n"+(r==null?currentPrompt:r.sid+"\n"+currentPrompt+"\nAcceleration: "+r.accCount+" · Gyroscope: "+r.gyroCount)+
   (clock==null?"\nWaiting for clock check":"\nClock round trip: "+String.format(Locale.US,"%.1f",clock.rtt/1e6)+" ms")+(lastError.isEmpty()?"":"\n"+lastError);
 }
 @Override public void onCreate(){
  super.onCreate();instance=this;
  SharedPreferences prefs=getSharedPreferences("identity",0);deviceId=prefs.getString("id",null);
  if(deviceId==null){deviceId=UUID.randomUUID().toString();prefs.edit().putString("id",deviceId).commit();}
  sensorThread=new HandlerThread("FYP-sensors");sensorThread.start();sensorHandler=new Handler(sensorThread.getLooper());
  NotificationManager nm=(NotificationManager)getSystemService(NOTIFICATION_SERVICE);nm.createNotificationChannel(new NotificationChannel("recording","Research recorder",NotificationManager.IMPORTANCE_LOW));
  Notification n=notification("Ready to connect");
  if(Build.VERSION.SDK_INT>=34)startForeground(67,n,ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);else startForeground(67,n);
  wake=((PowerManager)getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"FYP:Collection");wake.setReferenceCounted(false);
 }
 @Override public int onStartCommand(Intent intent,int flags,int id){
  String action=intent==null?"CONNECT":intent.getAction();
  if("STOP".equals(action)){sensorHandler.post(()->finishOnHandler("stopped"));return START_STICKY;}
  if("DISCONNECT".equals(action)){if(!recording())stopSelf();return START_NOT_STICKY;}
  if(worker==null||!worker.isAlive()){
   worker=new Thread(this::loop,"FYP-connection");worker.start();
  }
  return START_STICKY;
 }
 private Notification notification(String t){
  PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE);
  PendingIntent stop=PendingIntent.getService(this,1,new Intent(this,RecorderService.class).setAction("STOP"),PendingIntent.FLAG_IMMUTABLE);
  return new Notification.Builder(this,"recording").setContentTitle("FYP Phone Collector").setContentText(t).setSmallIcon(android.R.drawable.ic_menu_save).setOngoing(true).setContentIntent(open).addAction(new Notification.Action.Builder(null,"Stop and save",stop).build()).build();
 }
 void notifyText(String t){((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).notify(67,notification(t));}
 void beep(){try{ToneGenerator tone=new ToneGenerator(AudioManager.STREAM_MUSIC,65);tone.startTone(ToneGenerator.TONE_PROP_BEEP,120);sensorHandler.postDelayed(tone::release,300);}catch(Exception ignored){}}
 private Wire wire(){SharedPreferences p=getSharedPreferences("connection",0);return new Wire(p.getString("url","http://127.0.0.1:8765"),p.getString("token",""));}
 private JSONObject info()throws Exception{
  SensorManager sm=(SensorManager)getSystemService(SENSOR_SERVICE);Wire.Clock c=clock;Recorder r=recorder;
  return new JSONObject().put("device_id",deviceId).put("app_version","1.1").put("screen_visible",MainActivity.visible).put("model",Build.MANUFACTURER+" "+Build.MODEL)
   .put("accelerometer",sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)!=null).put("gyroscope",sm.getDefaultSensor(Sensor.TYPE_GYROSCOPE)!=null)
   .put("active_session",r==null?"":r.sid).put("clock_controller_id",c==null?"":c.controller)
   .put("clock_age_ms",c==null?1e9:(SystemClock.elapsedRealtimeNanos()-c.sampled)/1e6)
   .put("clock_rtt_ms",c==null?1e9:c.rtt/1e6).put("acceleration_rows",r==null?0:r.accCount).put("gyroscope_rows",r==null?0:r.gyroCount)
   .put("prompt",currentPrompt).put("error",lastError);
 }
 private void loop(){
  try{Recorder.recover(new File(getFilesDir(),"sessions"));}catch(Exception e){lastError="Recovery needs review: "+e.getMessage();}
  long syncAt=0,beatAt=0,uploadAt=0;
  while(alive){
   try{
    Wire w=wire();long now=SystemClock.elapsedRealtime();
    if(clock==null||now-syncAt>10000){
     Wire.Clock c=w.measure();clock=c;syncAt=now;
     sensorHandler.post(()->{try{if(recorder!=null)recorder.clock(c);}catch(Exception e){lastError=e.getMessage();}});
    }
    if(now-beatAt>1000){w.request("/api/heartbeat",info());beatAt=now;connection="Connected to laptop";}
    JSONObject result=w.request("/api/command?device="+deviceId,null);
    if(!result.isNull("command"))execute(w,result.getJSONObject("command"));
    if(!recording()&&now-uploadAt>8000){uploadAt=now;uploadPending(w,null);}
    Thread.sleep(250);
   }catch(InterruptedException e){break;}
   catch(Exception e){connection="Connection interrupted — local files retained";lastError=e.getMessage()==null?e.toString():e.getMessage();try{Thread.sleep(1500);}catch(InterruptedException x){break;}}
  }
 }
 private JSONObject onSensorThread(Callable<JSONObject> call)throws Exception{
  FutureTask<JSONObject> task=new FutureTask<>(call);sensorHandler.post(task);return task.get(45,TimeUnit.SECONDS);
 }
 private void execute(Wire w,JSONObject cmd)throws Exception{
  String cid=cmd.getString("id"),kind=cmd.getString("kind"),sid=cmd.getString("session_id");
  SharedPreferences prefs=getSharedPreferences("commands",0);String prior=prefs.getString(cid,null);JSONObject ack;
  if(prior!=null)ack=new JSONObject(prior);
  else{
   ack=new JSONObject().put("id",cid).put("device_id",deviceId);
   try{
    JSONObject result;
    if("START".equals(kind)){
     JSONObject plan=cmd.getJSONObject("payload");
     result=onSensorThread(()->{
      if(recording()){if(recorder.sid.equals(sid))return new JSONObject().put("already_running",true);throw new IOException("Phone already recording a different session");}
      File existing=new File(new File(getFilesDir(),"sessions"),sid);
      if(existing.exists())return new JSONObject().put("already_exists",true);
      Wire.Clock c=clock;if(c==null||SystemClock.elapsedRealtimeNanos()-c.sampled>15_000_000_000L||c.rtt>200_000_000L)throw new IOException("Clock check is stale or too slow");
      if(c.host(SystemClock.elapsedRealtimeNanos())>plan.getLong("start_ns"))throw new IOException("Start arrived too late. Create a fresh session.");
      if(getFilesDir().getUsableSpace()<200_000_000L)throw new IOException("Less than 200 MB free on phone");
      long remain=(plan.getLong("end_ns")-c.host(SystemClock.elapsedRealtimeNanos()))/1_000_000L;
      if(remain<=0||remain>3*60*60*1000L)throw new IOException("Invalid recording duration");
      wake.acquire(remain+5*60*1000L);
      try{recorder=new Recorder(this,plan,c);}catch(Exception ex){if(wake.isHeld())wake.release();throw ex;}
      currentPrompt="Recording · waiting for first prompt";lastError="";
      return new JSONObject().put("session_id",sid).put("started_phone_elapsed_ns",SystemClock.elapsedRealtimeNanos());
     });
    }else if("STOP".equals(kind)){
     result=onSensorThread(()->{
      if(recording()&&!recorder.sid.equals(sid))throw new IOException("Stop belongs to a different session");
      boolean absent=!recording();finishOnHandler("stopped");return new JSONObject().put("not_started",absent&&!new File(new File(getFilesDir(),"sessions"),sid).exists());
     });
    }else if("UPLOAD".equals(kind)){
     if(recording()&&recorder.sid.equals(sid))throw new IOException("Recording is still running");
     uploadPending(w,sid);result=new JSONObject().put("transfer_checked",true);
    }else throw new IOException("Unsupported command");
    ack.put("ok",true).put("result",result);
   }catch(Exception e){ack.put("ok",false).put("error",e.getCause()==null?e.toString():e.getCause().toString());lastError=ack.optString("error");}
   // Persist before sending ACK: a lost response cannot replay a recording command.
   SharedPreferences.Editor edit=prefs.edit();if(prefs.getAll().size()>250)edit.clear();edit.putString(cid,ack.toString()).commit();
  }
  w.request("/api/ack",ack);
 }
 void finishOnHandler(String status){
  Recorder r=recorder;if(r==null)return;
  try{r.finish(status);currentPrompt="Saved locally · transfer will retry automatically";notifyText(currentPrompt);}
  catch(Exception e){lastError="Local recovery needed: "+e.toString();currentPrompt="Partial recording retained on phone";}
  finally{recorder=null;if(wake!=null&&wake.isHeld())wake.release();}
 }
 private void uploadPending(Wire w,String only)throws Exception{
  File root=new File(getFilesDir(),"sessions");File[] dirs=root.listFiles();if(dirs==null)return;
  Arrays.sort(dirs,(a,b)->a.getName().compareTo(b.getName()));boolean found=false;
  for(File dir:dirs){
   if(!dir.isDirectory()||only!=null&&!dir.getName().equals(only))continue;
   File zip=new File(dir,"recording.zip"),receipt=new File(dir,"laptop_receipt.json");if(!zip.isFile())continue;found=true;
   if(receipt.exists())continue;
   connection="Transferring "+dir.getName();JSONObject ack=w.upload(zip,dir.getName());Recorder.atomic(receipt,ack);lastError="";connection="Transfer verified · original retained";
  }
  if(only!=null&&!found)throw new IOException("No local archive for this session yet");
 }
 @Override public void onDestroy(){
  alive=false;if(worker!=null)worker.interrupt();
  try{onSensorThread(()->{finishOnHandler("interrupted");return new JSONObject();});}catch(Exception ignored){}
  sensorThread.quitSafely();if(wake!=null&&wake.isHeld())wake.release();instance=null;super.onDestroy();
 }
 @Override public IBinder onBind(Intent i){return null;}
}
