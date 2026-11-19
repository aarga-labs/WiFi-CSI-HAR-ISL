#!/usr/bin/env python3
"""Build the small Java Android app with official Android SDK binaries."""
from pathlib import Path
import argparse
import os
import secrets
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parent
def run(args):subprocess.run([str(x) for x in args],check=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sdk',default=str(Path.home()/'.cache/fyp_android_sdk/unpacked'));args=ap.parse_args()
    sdk=Path(args.sdk);jar=next(sdk.rglob('android.jar'));tools=next(sdk.rglob('aapt2')).parent
    build=ROOT/'build';classes=build/'classes';dex=build/'dex'
    classes.mkdir(parents=True,exist_ok=True);dex.mkdir(parents=True,exist_ok=True)
    run(['javac','--release','8','-encoding','UTF-8','-classpath',jar,'-d',classes,*sorted((ROOT/'android/src').rglob('*.java'))])
    run([tools/'d8','--lib',jar,'--min-api','26','--output',dex,*sorted(classes.rglob('*.class'))])
    unsigned=build/'unsigned.apk'
    run([tools/'aapt2','link','-I',jar,'--manifest',ROOT/'android/AndroidManifest.xml','-o',unsigned])
    with zipfile.ZipFile(unsigned,'a',compression=zipfile.ZIP_STORED) as z:z.write(dex/'classes.dex','classes.dex')
    run([tools/'zipalign','-f','4',unsigned,build/'aligned.apk'])
    keydir=Path.home()/'.local/share/fyp-phone-collector';keydir.mkdir(parents=True,exist_ok=True);keydir.chmod(0o700)
    key=keydir/'research.keystore';pw=keydir/'signing-password.txt'
    if not pw.exists():pw.write_text(secrets.token_urlsafe(28));pw.chmod(0o600)
    if not key.exists():
        run(['keytool','-genkeypair','-keystore',key,'-storepass:file',pw,'-keypass:file',pw,'-alias','research','-keyalg','RSA','-keysize','3072','-validity','3650','-dname','CN=FYP Research Recorder, OU=Group 067, O=Local Research, C=IN'])
        key.chmod(0o600)
    out=ROOT/'FYP_Phone_Collector.apk'
    run([tools/'apksigner','sign','--ks',key,'--ks-key-alias','research','--ks-pass','file:'+str(pw),'--out',out,build/'aligned.apk'])
    run([tools/'apksigner','verify','--verbose',out]);print('Built:',out)
if __name__=='__main__':main()
