package org.aarga.fypcollector;

import android.hardware.*;
import android.os.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.zip.*;

final class Recorder implements SensorEventListener {
 final RecorderService owner;final JSONObject plan;final File folder;final String sid;
 final SensorManager sensors;final Wire.Clock initialClock;
 final HashMap<String,FileOutputStream> streams=new HashMap<>();
 final HashMap<String,BufferedWriter> writers=new HashMap<>();
 final long deviceEpochOffset=System.currentTimeMillis()*1_000_000L-SystemClock.elapsedRealtimeNanos();
 volatile long accCount=0,gyroCount=0;
 boolean open=true;int phase=-1;long phaseActualStart=0,lastFlush=0,lastSync=0;
 String failure="";JSONObject metadata;
 final ArrayList<Runnable> scheduledTasks=new ArrayList<>();
 long lastAcc=0,lastGyro=0;
 static final long MAX_SENSOR_GAP_NS=100_000_000L,MAX_CUE_LATENESS_NS=200_000_000L;
 Recorder(RecorderService owner,JSONObject plan,Wire.Clock clock)throws Exception{
  this.owner=owner;this.plan=plan;this.initialClock=clock;this.sid=plan.getString("session_id");
  if(!sid.matches("[A-Za-z0-9_-]{1,100}"))throw new IOException("Invalid session ID");
  folder=new File(new File(owner.getFilesDir(),"sessions"),sid);
  if(folder.exists())throw new IOException("Recording already exists; refusing to overwrite");
  if(!folder.mkdirs())throw new IOException("Cannot create recording folder");
  sensors=(SensorManager)owner.getSystemService(android.content.Context.SENSOR_SERVICE);
  Sensor acc=sensors.getDefaultSensor(Sensor.TYPE_ACCELEROMETER),gyro=sensors.getDefaultSensor(Sensor.TYPE_GYROSCOPE);
  if(acc==null||gyro==null)throw new IOException("Both motion sensors are required");
  create("accelerometer.csv","sensor_elapsed_ns,received_elapsed_ns,device_time_est_ns,controller_time_est_ns,clock_sample_id,x,y,z,accuracy\n");
  create("gyroscope.csv","sensor_elapsed_ns,received_elapsed_ns,device_time_est_ns,controller_time_est_ns,clock_sample_id,x,y,z,accuracy\n");
  create("labels.csv","phase_index,trial,kind,label,state,scheduled_start_controller_ns,scheduled_end_controller_ns,actual_start_phone_ns,actual_end_phone_ns,start_controller_est_ns,end_controller_est_ns,phase_complete,source\n");
  create("clock_sync.csv","sample_id,controller_id,phone_sample_ns,offset_ns,rtt_ns,phone_send_ns,host_receive_ns,host_send_ns,phone_receive_ns\n");
  metadata=new JSONObject().put("session_id",sid).put("pid",plan.getString("pid")).put("device_id",owner.deviceId)
   .put("status","recording").put("plan",plan).put("phone_model",Build.MANUFACTURER+" "+Build.MODEL)
   .put("android_api",Build.VERSION.SDK_INT).put("app_version","1.1").put("requested_hz",50)
   .put("timing_guard","Stop and retain partial data on sensor gaps >100ms or cue delay >200ms")
   .put("acceleration_units","m/s^2, gravity included").put("gyroscope_units","rad/s")
   .put("axes","Android device axes; phone mounting must remain consistent")
   .put("started_phone_elapsed_ns",SystemClock.elapsedRealtimeNanos()).put("device_epoch_offset_ns",deviceEpochOffset)
   .put("clock_method","Seven HTTP round trips; minimum RTT mapping, repeated periodically. Network asymmetry and sensor latency are not calibrated.")
   .put("label_provenance","Scheduled prompt intervals; not independently verified movement boundaries. READY/REST/SYNC are not supervised idle.")
   .put("accelerometer",sensorInfo(acc)).put("gyroscope",sensorInfo(gyro));
  atomic(new File(folder,"metadata.json"),metadata);
  clock(clock);
  boolean a=sensors.registerListener(this,acc,20000,0,owner.sensorHandler);
  boolean g=sensors.registerListener(this,gyro,20000,0,owner.sensorHandler);
  if(!a||!g){finish("sensor_error");throw new IOException("Could not start both motion sensors");}
  owner.sensorHandler.postDelayed(flusher,1000);
  JSONArray phases=plan.getJSONArray("phases");
  for(int i=0;i<phases.length();i++){
   final int ix=i;long due=phases.getJSONObject(i).getLong("start_ns")-clock.offset;
   Runnable task=()->{if(!open)return;if(SystemClock.elapsedRealtimeNanos()-due>MAX_CUE_LATENESS_NS){fail("Cue timing exceeded 200ms; recording stopped to prevent mislabeled data");return;}advance(ix);};
   scheduledTasks.add(task);owner.sensorHandler.postDelayed(task,Math.max(0,(due-SystemClock.elapsedRealtimeNanos())/1_000_000L));
  }
  long end=plan.getLong("end_ns")-clock.offset;
  Runnable finishTask=()->{if(!open)return;if(SystemClock.elapsedRealtimeNanos()-end>MAX_CUE_LATENESS_NS){fail("Final cue timing exceeded 200ms");return;}owner.finishOnHandler("complete");};
  scheduledTasks.add(finishTask);owner.sensorHandler.postDelayed(finishTask,Math.max(0,(end-SystemClock.elapsedRealtimeNanos())/1_000_000L));
 }
 private JSONObject sensorInfo(Sensor s)throws Exception{
  return new JSONObject().put("name",s.getName()).put("vendor",s.getVendor()).put("version",s.getVersion())
   .put("min_delay_us",s.getMinDelay()).put("resolution",s.getResolution()).put("max_range",s.getMaximumRange());
 }
 private void create(String name,String header)throws Exception{
  FileOutputStream f=new FileOutputStream(new File(folder,name));streams.put(name,f);
  BufferedWriter w=new BufferedWriter(new OutputStreamWriter(f,"UTF-8"),32768);writers.put(name,w);w.write(header);w.flush();f.getFD().sync();
 }
 static String cell(String s){return "\""+s.replace("\"","\"\"").replace('\n',' ').replace('\r',' ')+"\"";}
 public void onAccuracyChanged(Sensor sensor,int accuracy){}
 public void onSensorChanged(SensorEvent e){
  if(!open)return;
  try{
   String name=e.sensor.getType()==Sensor.TYPE_ACCELEROMETER?"accelerometer.csv":"gyroscope.csv";
   Wire.Clock c=owner.clock;long estimate=c==null?0:c.host(e.timestamp);String cid=c==null?"":c.id;
   writers.get(name).write(e.timestamp+","+SystemClock.elapsedRealtimeNanos()+","+(e.timestamp+deviceEpochOffset)+","+estimate+","+cid+","+Float.toString(e.values[0])+","+Float.toString(e.values[1])+","+Float.toString(e.values[2])+","+e.accuracy+"\n");
   if(name.startsWith("acc"))accCount++;else gyroCount++;
   long previous=name.startsWith("acc")?lastAcc:lastGyro;
   if(name.startsWith("acc"))lastAcc=e.timestamp;else lastGyro=e.timestamp;
   if(previous!=0&&e.timestamp-previous>MAX_SENSOR_GAP_NS)fail(name+" gap exceeded 100ms; stopped and retained partial data");
  }catch(Exception ex){failure=ex.toString();owner.lastError="Sensor write failed; preserving partial recording";owner.finishOnHandler("sensor_error");}
 }
 private final Runnable flusher=new Runnable(){public void run(){
  if(!open)return;
  long now=SystemClock.elapsedRealtimeNanos();
  if((lastAcc!=0&&now-lastAcc>1_000_000_000L)||(lastGyro!=0&&now-lastGyro>1_000_000_000L)){fail("Motion sensor delivery stopped for over 1 second");return;}
  try{flush(SystemClock.elapsedRealtime()-lastSync>=5000);}catch(Exception e){failure=e.toString();owner.finishOnHandler("sensor_error");return;}
  owner.sensorHandler.postDelayed(this,1000);
 }};
 private void fail(String message){failure=message;owner.lastError=message;owner.finishOnHandler("sensor_error");}
 private void flush(boolean sync)throws Exception{
  for(BufferedWriter w:writers.values())w.flush();
  if(sync){for(FileOutputStream f:streams.values())f.getFD().sync();lastSync=SystemClock.elapsedRealtime();}
 }
 void clock(Wire.Clock c)throws Exception{
  if(!open)return;JSONObject e=c.evidence;
  writers.get("clock_sync.csv").write(c.id+","+c.controller+","+c.sampled+","+c.offset+","+c.rtt+","+e.getLong("phone_send_ns")+","+e.getLong("host_receive_ns")+","+e.getLong("host_send_ns")+","+e.getLong("phone_receive_ns")+"\n");
  writers.get("clock_sync.csv").flush();
 }
 private void endPhase(long end,boolean complete)throws Exception{
  if(phase<0)return;JSONObject p=plan.getJSONArray("phases").getJSONObject(phase);
  writers.get("labels.csv").write(phase+","+p.getInt("trial")+","+p.getString("kind")+","+cell(p.getString("label"))+","+p.getString("state")+","+p.getLong("start_ns")+","+p.getLong("end_ns")+","+phaseActualStart+","+end+","+initialClock.host(phaseActualStart)+","+initialClock.host(end)+","+complete+",scheduled_cue\n");writers.get("labels.csv").flush();
 }
 private void advance(int index){
  if(!open)return;
  try{
   long t=SystemClock.elapsedRealtimeNanos();endPhase(t,true);phase=index;phaseActualStart=t;
   JSONObject p=plan.getJSONArray("phases").getJSONObject(index);owner.currentPrompt=p.getString("kind").toUpperCase()+": "+p.getString("label");
   owner.notifyText(owner.currentPrompt);
   if(p.getString("kind").equals("perform"))owner.beep();
  }catch(Exception e){failure=e.toString();owner.finishOnHandler("sensor_error");}
 }
 void finish(String status)throws Exception{
  if(!open)return;open=false;sensors.unregisterListener(this);owner.sensorHandler.removeCallbacks(flusher);
  for(Runnable task:scheduledTasks)owner.sensorHandler.removeCallbacks(task);scheduledTasks.clear();
  long end=SystemClock.elapsedRealtimeNanos();
  Exception issue=null;
  try{endPhase(end,"complete".equals(status));flush(true);}catch(Exception e){issue=e;status="sensor_error";}
  for(BufferedWriter w:writers.values())try{w.close();}catch(Exception e){issue=e;}
  metadata.put("status",status).put("ended_phone_elapsed_ns",end).put("acceleration_rows",accCount).put("gyroscope_rows",gyroCount)
   .put("error",failure+(issue==null?"":" "+issue)).put("raw_retention","Never automatically deleted after transfer");
  atomic(new File(folder,"metadata.json"),metadata);archive(folder);
 }
 static void atomic(File file,JSONObject d)throws Exception{
  File temp=new File(file.getParentFile(),file.getName()+".tmp");
  try(FileOutputStream out=new FileOutputStream(temp)){out.write(d.toString(2).getBytes("UTF-8"));out.flush();out.getFD().sync();}
  if(!temp.renameTo(file))throw new IOException("Could not save "+file.getName());
 }
 static JSONObject read(File f)throws Exception{
  ByteArrayOutputStream o=new ByteArrayOutputStream();try(InputStream in=new FileInputStream(f)){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)o.write(b,0,n);}return new JSONObject(o.toString("UTF-8"));
 }
 static void archive(File dir)throws Exception{
  File zip=new File(dir,"recording.zip");if(zip.exists())return;
  String[] names={"accelerometer.csv","gyroscope.csv","labels.csv","clock_sync.csv","metadata.json"};
  JSONObject manifest=new JSONObject();
  for(String name:names){File f=new File(dir,name);if(!f.isFile())throw new IOException("Missing local file "+name);manifest.put(name,new JSONObject().put("bytes",f.length()).put("sha256",Wire.sha(f)));}
  atomic(new File(dir,"manifest.json"),manifest);
  File temp=new File(dir,"recording.zip.part");
  try(FileOutputStream fout=new FileOutputStream(temp)){
   ZipOutputStream out=new ZipOutputStream(new BufferedOutputStream(fout));
   for(String name:new String[]{"accelerometer.csv","gyroscope.csv","labels.csv","clock_sync.csv","metadata.json","manifest.json"}){
    out.putNextEntry(new ZipEntry(name));try(InputStream in=new FileInputStream(new File(dir,name))){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}out.closeEntry();
   }
   out.finish();out.flush();fout.getFD().sync();out.close();
  }
  if(!temp.renameTo(zip))throw new IOException("Could not finalize local archive");
 }
 static void recover(File root)throws Exception{
  File[] dirs=root.listFiles();if(dirs==null)return;
  for(File dir:dirs){
   File meta=new File(dir,"metadata.json");if(!dir.isDirectory()||!meta.isFile()||new File(dir,"recording.zip").isFile())continue;
   JSONObject d=read(meta);
   if("recording".equals(d.optString("status"))){d.put("status","interrupted").put("recovery_note","Process stopped. Persisted rows retained; the unfinished cue interval is not fabricated.");atomic(meta,d);}
   archive(dir);
  }
 }
}
