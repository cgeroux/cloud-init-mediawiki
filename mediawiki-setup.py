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
def replaceStrInFile(strMatch,strReplace,fileName):
  """Replace all occurrences of strMatch with strReplace in file fileName
  """
  
  file=open(fileName,mode='r')
  fileText=file.read()
  file.close()
  fileText=fileText.replace(strMatch,strReplace)
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
def setupMediaWiki(version="1.27",patch=".0",tmpDir="/tmp"
  ,documentRoot="/var/www/html",owner="root",group="root",cleanUp=True
  ,purgeDocRoot=True):
  """Downloads media wiki and puts it into document root
  """
  
  tmpMediaWikiDir=os.path.join(tmpDir,"mediawiki-"+version+patch)
  url="https://releases.wikimedia.org/mediawiki/"+version+"/mediawiki-" \
    +version+patch+".tar.gz"
  
  #download and untar mediawiki
  subprocess.call(["wget",url,"--directory-prefix="+tmpDir])
  subprocess.call(["tar","-xzf",tmpMediaWikiDir+".tar.gz","-C",tmpDir])
  
  #remove existing files in document root
  if purgeDocRoot:
    paths=glob.glob(documentRoot+"/*")
    for path in paths:
      try:
        os.remove(path)
      except IsADirectoryError:
        shutil.rmtree(path)
  
  #move files to document root
  paths=glob.glob(tmpMediaWikiDir+"/*")
  for path in paths:
    pathBaseName=os.path.basename(path)
    shutil.move(path,os.path.join(documentRoot,pathBaseName))
  
  #change owner and group
  for path in paths:
    pathBaseName=os.path.basename(path)
    shutil.chown(os.path.join(documentRoot,pathBaseName)
      ,user=owner
      ,group=group)
  
  #clean up temporary files
  if cleanUp:
    os.removedirs(tmpMediaWikiDir)
    os.remove(tmpMediaWikiDir+".tar.gz")
  
  #do basic configure of the wiki
  #TODO: need to make many of these arguments parameters, and need 
  #to test this
  subprocess.call(["php","/var/www/html/maintenance/install.php"
    ,"--scriptpath", "\"\'","--pass","adminpass123","--server"
    ,"http://206.167.181.71","--dbuser","root","--dbserver", "localhost",
    "Test Wiki", "adminuser"])
def restartApache():
  """Restarts apache2
  """
  
  subprocess.call(["service","apache2","restart"])
def main():
  
  #parse command line options
  (options,args)=parseOptions()
  
  setupMediaWiki(cleanUp=True)
if __name__ == "__main__":
 main()