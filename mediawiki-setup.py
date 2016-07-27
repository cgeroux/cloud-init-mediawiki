#!/usr/bin python3
import optparse as op
import os
import shutil
import subprocess

def parseOptions()
  """Parses command line options
  """
  
  
  parser=op.OptionParser(usage=Usage %prog USERNAME
    ,version=%prog 1.0,description=Sets up Apache2 for the given USERNAME)
  
  #parse command line options
  return parser.parse_args()
def replaceStrInFile(strMatch,strReplace,fileName)
  """Replace all occurrences of strMatch with strReplace in file fileName
  """
  
  file=open(fileName,mode='r')
  fileText=file.read()
  file.close()
  fileText=fileText.replace(strMatch,strReplace)
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
def makePublicHtml(userName)
  """Creates the public html directory and index.html in the users home directory
  """
  
  #make public html directory
  publicHtmlDir=home+userName+public_html
  try
    os.makedirs(publicHtmlDir)
  except FileExistsError
    pass
  
  #make place holder index file
  indexFileName=os.path.join(publicHtmlDir,index.html)
  indexText=h1Edit +indexFileName+ to customize your websiteh1
  file=open(indexFileName,'w')
  file.write(indexText)
  file.close()
  
  #give user ownership
  shutil.chown(publicHtmlDir,user=userName,group=userName)
  shutil.chown(indexFileName,user=userName,group=userName)
def restartApache()
  """Restarts apache2
  """
  
  subprocess.call([service,apache2,restart])
def main()
  
  #parse command line options
  (options,args)=parseOptions()
  print("mediawiki-setup.py run")
  
  
#  if len(args)!=1
#    raise Exception(must have exactly one argument)
#  
#  userName=args[0]
#  
#  #change root directory
#  replaceStrInFile(Directory varwwwhtml,Directory home+userName+public_html,etcapache2apache2.conf)
#  replaceStrInFile(Directory varwww,Directory home+userName+public_html,etcapache2apache2.conf)
#  
#  #change document root
#  replaceStrInFile(DocumentRoot varwwwhtml,DocumentRoot home+userName+public_html,etcapache2sites-available000-default.conf)
#  replaceStrInFile(DocumentRoot varwww,DocumentRoot home+userName+public_html,etcapache2sites-available000-default.conf)
#  
#  #make user's public_html
#  makePublicHtml(userName)
#  
#  restartApache()
if __name__ == __main__
 main()