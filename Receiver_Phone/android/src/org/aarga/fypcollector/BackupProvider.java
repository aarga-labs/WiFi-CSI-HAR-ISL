package org.aarga.fypcollector;
import android.content.*;
import android.database.*;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.*;
public class BackupProvider extends ContentProvider {
 public boolean onCreate(){return true;}
 private File file(Uri uri)throws FileNotFoundException{
  String id=uri.getLastPathSegment();if(id==null||!id.matches("[A-Za-z0-9_-]{1,100}"))throw new FileNotFoundException();
  File f=new File(new File(new File(getContext().getFilesDir(),"sessions"),id),"recording.zip");if(!f.isFile())throw new FileNotFoundException();return f;
 }
 public String getType(Uri u){return "application/zip";}
 public Cursor query(Uri u,String[] p,String s,String[] a,String o){
  try{File f=file(u);MatrixCursor c=new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE});c.addRow(new Object[]{f.getParentFile().getName()+".zip",f.length()});return c;}catch(Exception e){return null;}
 }
 public ParcelFileDescriptor openFile(Uri u,String m)throws FileNotFoundException{
  if(!"r".equals(m))throw new FileNotFoundException("Read only");return ParcelFileDescriptor.open(file(u),ParcelFileDescriptor.MODE_READ_ONLY);
 }
 public Uri insert(Uri u,ContentValues v){throw new UnsupportedOperationException();}
 public int update(Uri u,ContentValues v,String s,String[] a){throw new UnsupportedOperationException();}
 public int delete(Uri u,String s,String[] a){throw new UnsupportedOperationException();}
}
