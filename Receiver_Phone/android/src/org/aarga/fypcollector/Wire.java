package org.aarga.fypcollector;
import android.os.SystemClock;
import org.json.*;
import java.net.*;
import java.io.*;
import java.security.*;

final class Wire {
 final String url,token;
 Wire(String url,String token){this.url=url;this.token=token;}
 HttpURLConnection open(String path)throws Exception{
  HttpURLConnection c=(HttpURLConnection)new URL(url+path).openConnection();c.setConnectTimeout(4000);c.setReadTimeout(8000);c.setRequestProperty("X-Token",token);c.setUseCaches(false);return c;
 }
 JSONObject request(String path,JSONObject data)throws Exception{
  HttpURLConnection c=open(path);
  try{
   if(data!=null){byte[] bytes=data.toString().getBytes("UTF-8");c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");c.setFixedLengthStreamingMode(bytes.length);try(OutputStream o=c.getOutputStream()){o.write(bytes);}}
   return response(c);
  }finally{c.disconnect();}
 }
 JSONObject response(HttpURLConnection c)throws Exception{
  int code=c.getResponseCode();InputStream stream=code<400?c.getInputStream():c.getErrorStream();ByteArrayOutputStream out=new ByteArrayOutputStream();
  if(stream!=null)try(InputStream in=stream){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){out.write(b,0,n);if(out.size()>1_000_000)throw new IOException("Response too large");}}
  JSONObject d=new JSONObject(out.toString("UTF-8"));if(code>=400)throw new IOException(d.optString("error","Laptop request failed"));return d;
 }
 JSONObject upload(File file,String sid)throws Exception{
  HttpURLConnection c=open("/api/upload");c.setReadTimeout(120000);c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("Content-Type","application/zip");c.setRequestProperty("X-Session-ID",sid);String hash=sha(file);c.setRequestProperty("X-SHA256",hash);c.setFixedLengthStreamingMode(file.length());
  try{
   try(InputStream in=new FileInputStream(file);OutputStream out=c.getOutputStream()){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}
   JSONObject receipt=response(c);if(!receipt.optBoolean("ok")||!hash.equals(receipt.optString("sha256")))throw new IOException("Laptop receipt checksum mismatch; local copy kept");return receipt;
  }finally{c.disconnect();}
 }
 static String sha(File f)throws Exception{
  MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)d.update(b,0,n);}
  StringBuilder s=new StringBuilder();for(byte b:d.digest())s.append(String.format(java.util.Locale.US,"%02x",b&255));return s.toString();
 }
 static final class Clock {
  final long offset,rtt,sampled;final String controller,id;final JSONObject evidence;
  Clock(long offset,long rtt,long sampled,String controller,JSONObject evidence){this.offset=offset;this.rtt=rtt;this.sampled=sampled;this.controller=controller;this.evidence=evidence;this.id=java.util.UUID.randomUUID().toString();}
  long host(long phone){return phone+offset;}
 }
 Clock measure()throws Exception{
  Clock best=null;
  for(int i=0;i<7;i++){
   long t1=SystemClock.elapsedRealtimeNanos();JSONObject d=request("/api/clock",null);long t4=SystemClock.elapsedRealtimeNanos();long t2=d.getLong("receive_ns"),t3=d.getLong("send_ns");
   long rtt=Math.max(0,(t4-t1)-(t3-t2));long offset=((t2-t1)+(t3-t4))/2;
   JSONObject evidence=new JSONObject().put("phone_send_ns",t1).put("host_receive_ns",t2).put("host_send_ns",t3).put("phone_receive_ns",t4);
   Clock c=new Clock(offset,rtt,t4,d.getString("controller_id"),evidence);if(best==null||rtt<best.rtt)best=c;
  }
  return best;
 }
}
