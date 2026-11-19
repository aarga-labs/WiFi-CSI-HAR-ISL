package org.aarga.fypcollector;

import android.app.*;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.provider.Settings;
import android.text.InputType;
import android.view.*;
import android.widget.*;
import java.io.File;
import java.util.*;

public class MainActivity extends Activity {
    public static volatile boolean visible=false;
    private TextView status;
    private EditText address,key;
    private final Handler ui=new Handler();
    private final Runnable refresh=new Runnable(){public void run(){
        RecorderService s=RecorderService.instance;
        status.setText(s==null?"Not connected. Enter the laptop address and key, then connect.":s.summary());
        ui.postDelayed(this,1000);
    }};
    private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density);}
    private TextView text(String t,int size){TextView v=new TextView(this);v.setText(t);v.setTextSize(size);v.setTextColor(Color.rgb(30,38,49));v.setPadding(0,dp(8),0,dp(8));return v;}
    private Button button(String t,LinearLayout l){Button b=new Button(this);b.setText(t);l.addView(b,new LinearLayout.LayoutParams(-1,dp(58)));return b;}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        ScrollView scroll=new ScrollView(this);LinearLayout l=new LinearLayout(this);l.setOrientation(1);l.setPadding(dp(24),dp(24),dp(24),dp(24));scroll.addView(l);setContentView(scroll);
        l.addView(text("GROUP 067 · PHONE RECORDER",12));l.addView(text("FYP Phone Collector",28));
        l.addView(text("Version 1.1 · Keep this app visible while recording. This page keeps the screen awake. The laptop controls recording. Your original files stay on this phone.",16));
        l.addView(text("Laptop address",14));address=new EditText(this);address.setSingleLine(true);address.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_URI);address.setText(getPreferences().getString("url","http://127.0.0.1:8765"));l.addView(address);
        l.addView(text("Pairing key from laptop",14));key=new EditText(this);key.setSingleLine(true);key.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);key.setText(getPreferences().getString("token",""));l.addView(key);
        button("Connect / Ready",l).setOnClickListener(v->{
            try {
                String url=address.getText().toString().trim().replaceAll("/+$","");
                Uri u=Uri.parse(url);String host=u.getHost();
                boolean local=host!=null&&(host.equals("localhost")||host.equals("127.0.0.1")||host.startsWith("192.168.")||host.startsWith("10.")||host.matches("172\\.(1[6-9]|2[0-9]|3[01])\\..+"));
                if(!"http".equals(u.getScheme())||!local||u.getUserInfo()!=null||!(u.getPath()==null||u.getPath().isEmpty()))throw new Exception("Use a local laptop address, such as http://127.0.0.1:8765 over USB or http://192.168.x.x:8765 over trusted Wi-Fi.");
                String token=key.getText().toString().trim();if(token.length()<20)throw new Exception("Copy the full pairing key from your laptop.");
                if(RecorderService.instance!=null&&RecorderService.instance.recording())throw new Exception("Finish the current recording before changing the connection.");
                getPreferences().edit().putString("url",url).putString("token",token).apply();
                getSharedPreferences("connection",0).edit().putString("url",url).putString("token",token).commit();
                if(Build.VERSION.SDK_INT>=33&&checkSelfPermission("android.permission.POST_NOTIFICATIONS")!=PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},12);
                startForegroundService(new Intent(this,RecorderService.class).setAction("CONNECT"));
            }catch(Exception e){new AlertDialog.Builder(this).setMessage(e.getMessage()).setPositiveButton("OK",null).show();}
        });
        status=text("",16);status.setPadding(dp(12),dp(16),dp(12),dp(16));status.setBackgroundColor(Color.rgb(244,239,240));l.addView(status);
        button("Stop recording and keep files",l).setOnClickListener(v->{if(RecorderService.instance!=null)startService(new Intent(this,RecorderService.class).setAction("STOP"));});
        button("Share a local backup",l).setOnClickListener(v->shareBackup());
        button("Disconnect when finished",l).setOnClickListener(v->{
            if(RecorderService.instance!=null&&RecorderService.instance.recording())Toast.makeText(this,"Stop and save the recording first.",Toast.LENGTH_LONG).show();
            else if(RecorderService.instance!=null)startService(new Intent(this,RecorderService.class).setAction("DISCONNECT"));
        });
        button("Battery settings",l).setOnClickListener(v->{try{startActivity(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));}catch(Exception ignored){}});
        l.addView(text("Allow notifications and unrestricted battery use. Keep this app visible; do not lock the phone during collection. Recording stops and preserves a flagged partial file if a sensor gap or timing failure is detected. Reconnect to transfer retained files.",14));
        l.addView(text("USB: the laptop launcher sets up the cable connection. Wi-Fi: use a trusted local network; this prototype does not encrypt local Wi-Fi traffic. No camera, microphone, GPS or cloud account is used.",13));
    }
    private android.content.SharedPreferences getPreferences(){return getSharedPreferences("screen",0);}
    @Override protected void onResume(){super.onResume();visible=true;ui.post(refresh);}
    @Override protected void onPause(){visible=false;super.onPause();ui.removeCallbacks(refresh);}
    private void shareBackup(){
        File root=new File(getFilesDir(),"sessions");File[] dirs=root.listFiles();ArrayList<File> backups=new ArrayList<>();
        if(dirs!=null)for(File d:dirs){File f=new File(d,"recording.zip");if(f.isFile())backups.add(f);}
        Collections.sort(backups,(a,b)->Long.compare(b.lastModified(),a.lastModified()));
        if(backups.isEmpty()){Toast.makeText(this,"No completed local archive yet. Reconnect to finish recovery if recording was interrupted.",Toast.LENGTH_LONG).show();return;}
        String[] names=new String[backups.size()];for(int i=0;i<names.length;i++)names[i]=backups.get(i).getParentFile().getName();
        new AlertDialog.Builder(this).setTitle("Choose a local recording").setItems(names,(d,index)->{
            Uri uri=Uri.parse("content://org.aarga.fypcollector.backup/"+names[index]);
            Intent send=new Intent(Intent.ACTION_SEND).setType("application/zip").putExtra(Intent.EXTRA_STREAM,uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            send.setClipData(ClipData.newRawUri("FYP recording",uri));startActivity(Intent.createChooser(send,"Share backup"));
        }).show();
    }
}
