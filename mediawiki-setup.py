#!/usr/bin/python3
import optparse as op
import os
import shutil
import subprocess
import glob

def parseOptions():
  """Parses command line options
  """
  
  parser=op.OptionParser(usage="Usage %prog"
    ,version="%prog 1.0",description="Sets up mediawiki")
  
  #parse command line options
  return parser.parse_args()
def replaceStrInFile(strMatch,strReplace,fileName,maxOccurs=None):
  """Replace all occurrences of strMatch with strReplace in file fileName
  """
  
  file=open(fileName,mode='r')
  fileText=file.read()
  file.close()
  if maxOccurs!=None:
    fileText=fileText.replace(strMatch,strReplace,max=maxOccurs)
  else:
    fileText=fileText.replace(strMatch,strReplace)
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
def genNameAndPass(length=6
  ,chars=string.ascii_uppercase+string.ascii_lowercase+string.digits):
  
  name=''
  for i in range(length):
    name+=random.SystemRandom().choice(chars)
    
  passwd=''
  for i in range(length):
    passwd+=random.SystemRandom().choice(chars)
  
  return (name,passwd)
def setupMediaWiki(settings={}):
  """Downloads media wiki and puts it into document root
  """
  
  (adminName,adminPassWd)=genNameAndPass()
  (dummy,dbPassWd)=genNameAndPass()
  
  defaultSettings={
    "version":"1.27"
    ,"patch":"0"
    ,"wikiName":"Test Wiki"
    ,"wikiAdminName":adminName
    ,"wikiAdminPass":adminPassWd
    ,"server":"http://206.167.181.71"
    ,"dbserver":"localhost"
    ,"dbuser":"root"
    ,"dbpass":dbPassWd
    ,"documentRoot":"/var/www/html"
    ,"tmpDir":"/tmp"
    ,"owner":"www-data"
    ,"group":"www-data"
    ,"cleanUp":True
    ,"purgeDocRoot":True
    ,"enableUploads":False
    ,"logoURL":"$wgResourceBasePath/resources/assets/cc-cloud-wiki-logo.png"
    }
  
  #set settings to default if no settings given or if setting is None
  for key in defaultSettings.keys():
    
    if key not in settings.keys():
      settings[key]=defaultSettings[key]
    else:
      if settings[key]==None:
        settings[key]=defaultSettings[key]
  
  tmpMediaWikiDir=os.path.join(settings["tmpDir"],"mediawiki-"
    +settings["version"]+"."+settings["patch"])
  url="https://releases.wikimedia.org/mediawiki/"+settings["version"] \
    +"/mediawiki-"+settings["version"]+"."+settings["patch"]+".tar.gz"
  
  #download and untar mediawiki
  subprocess.call(["wget",url,"--directory-prefix="+settings["tmpDir"]])
  subprocess.call(["tar","-xzf",tmpMediaWikiDir+".tar.gz","-C"
    ,settings["tmpDir"]])
  
  #remove existing files in document root
  if settings["purgeDocRoot"]:
    paths=glob.glob(settings["documentRoot"]+"/*")
    for path in paths:
      try:
        os.remove(path)
      except IsADirectoryError:
        shutil.rmtree(path)
  
  #move files to document root
  paths=glob.glob(tmpMediaWikiDir+"/*")
  for path in paths:
    pathBaseName=os.path.basename(path)
    shutil.move(path,os.path.join(settings["documentRoot"],pathBaseName))
  
  #change owner and group
  for path in paths:
    pathBaseName=os.path.basename(path)
    shutil.chown(os.path.join(settings["documentRoot"],pathBaseName)
      ,user=settings["owner"]
      ,group=settings["group"])
  
  #clean up temporary files
  if settings["cleanUp"]:
    os.removedirs(tmpMediaWikiDir)
    os.remove(tmpMediaWikiDir+".tar.gz")
  
  #set mysql root password (initial install has no root password)
  suprocess.call(["mysqladmin","-u","root","password",settings["dbpass"]])
  
  #do basic configure of the wiki
  subprocess.call(["php"
    ,os.path.join(settings["documentRoot"],"maintenance/install.php")
    ,"--scriptpath", ""
    ,"--pass",settings["wikiAdminPass"]
    ,"--server",settings["server"]
    ,"--dbuser",settings["dbuser"]
    ,"--dbpass",settings["dbpass"]
    ,"--dbserver",settings["dbserver"]
    ,settings["wikiName"]
    ,settings["wikiAdminName"]])
  
  localSettingsFile=os.path.join(settings["documentRoot"],"LocalSettings.php")
  
  #enable file uploads
  if settings["enableUploads"]:
    replaceStrInFile("$wgEnableUploads = false;","$wgEnableUploads = true;"
      ,localSettingsFile)
  
  #copy default cc-wiki-logo
  src=os.path.join(settings["tmpDir"],"cloud-init-mediawiki/cc-cloud-wiki-logo.png")
  dest=os.path.join(settings["documentRoot"],"resources/assets/cc-cloud-wiki-logo.png")
  shutil.copy(src,dest)
  
  #set logo
  replaceStrInFile(
    "$wgLogo = \"$wgResourceBasePath/resources/assets/wiki.png\";"
    ,"$wgLogo = \""+settings["logoURL"]+"\";"
    ,localSettingsFile)
  
  #secure LocalSettings.php
  shutil.chown(localSettingsFile,user=settings["owner"],group=settings["group"])
  shutil.chmod(localSettingsFile,'0600')
  
  print("Wiki:adminuser: "+settings["wikiAdminName"])
  print("Wiki:adminpass: "+settings["adminPassWd"])
  print("Wiki:dbuser: "+settings["dbuser"])
  print("Wiki:dbpass: "+settings["dbpass"])
  
def restartApache():
  """Restarts apache2
  """
  
  subprocess.call(["service","apache2","restart"])
def main():
  
  #parse command line options
  (options,args)=parseOptions()
  
  setupMediaWiki(settings={"enableUploads":True})
if __name__ == "__main__":
 main()