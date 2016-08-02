#!/usr/bin/python3
import optparse as op
import os
import shutil
import subprocess
import glob
import string
import random
import stat
import re
import socket

def parseOptions():
  """Parses command line options
  """
  
  parser=op.OptionParser(usage="Usage %prog SERVER"
    ,version="%prog 1.0",description="Sets up mediawiki."
    +"SERVER is the base url for the server, this should be your domain name "
    +"which points to your machines IP, or your machines IP if you don't have "
    +"a domain name. This script should probably be run with sudo as it will "
    +"likely have to edit and read files which aren't editable or perhaps "
    +"not even readable by standard users.")
  
  parser.add_option("--dry-run",dest="dryRun",action="store_true",default=False
    ,help="If set will not actually do anything, only print out what it would "
    +"have done [not default]")
  parser.add_option("--wiki-version",dest="version",action="store"
    ,type="string",default="1.27"
    ,help="Set the mediawiki version [default: %default].")
  parser.add_option("--wiki-patch",dest="patch",action="store"
    ,type="string",default="0"
    ,help="Set the mediawiki patch version [default: %default].")
  parser.add_option("--name",dest="wikiName",action="store"
    ,type="string",default="CC User Wiki"
    ,help="Sets the name of the wiki [default: %default].")
  permisionTypes=["public","user","sysop"]
  parser.add_option("--read-permission",dest="wikiReadPerm",action="store"
    ,type="choice",choices=permisionTypes,default="user"
    ,help="Sets who can read the wiki pages with the exception of the login "
    +"page. Available choices are "+str(permisionTypes)
    +" [default: %default].")
  parser.add_option("--edit-permission",dest="wikiEditPerm",action="store"
    ,type="choice",choices=permisionTypes,default="user"
    ,help="Sets who can edit the wiki pages. Available choices are "
    +str(permisionTypes)+" [default: %default].")
  parser.add_option("--account-create-permission",dest="wikiAccCreatePerm"
    ,action="store",type="choice",choices=permisionTypes
    ,default="sysop",help="Sets who can create user accounts. Available "
    +"choices are "+str(permisionTypes)+" [default: %default].")
  parser.add_option("--admin-user",dest="wikiAdminName",action="store"
    ,type="string",default=None
    ,help="Sets wiki administrator user name, by default it is randomly "
    +"generated.")
  parser.add_option("--uploads",dest="enableUploads",action="store_true"
    ,default=False
    ,help="Enables file uploads [not default]")
  parser.add_option("--logo-url",dest="logoURL",action="store"
    ,default="$wgResourceBasePath/resources/assets/cc-cloud-wiki-logo.png"
    ,help="Set the url for the wiki logo [default: %default]")
  parser.add_option("--extra-config",dest="extraConfigLines",action="append"
    ,help="Set an extra configuration line by providing a string for "
    +"LocalSettings.php. Can be used multiple times to include multiple extra "
    +"configuration lines.")
  return parser.parse_args()
def replaceStrInFile(strMatch,strReplace,fileName,maxOccurs=None):
  """Replace all occurrences of strMatch with strReplace in file fileName
  up to maxOccurs if specified.
  """
  
  file=open(fileName,mode='r')
  fileText=file.read()
  file.close()
  
  #how many occurrences are there
  numMatches=fileText.count(strMatch)
  
  if maxOccurs!=None:
    fileText=fileText.replace(strMatch,strReplace,max=maxOccurs)
    if numMatches>maxOccurs:
      numMatches=maxOccurs
  else:
    fileText=fileText.replace(strMatch,strReplace)
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
  return numMatches
def replaceStrInFileRe(pattern,replacement,fileName,maxOccurs=None):
  """Replace all occurrences of pattern with strReplace in file fileName
  up to maxOccurs if specified. This version uses regular expression matching 
  also
  """
  
  file=open(fileName,mode='r')
  fileText=file.read()
  file.close()
  
  #how many occurrences are there
  numMatches=len(re.findall(pattern,fileText))
  
  if maxOccurs!=None:
    fileText=re.sub(pattern,replacement,fileText,count=maxOccurs)
    if numMatches>maxOccurs:
      numMatches=maxOccurs
  else:
    fileText=re.sub(pattern,replacement,fileText)
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
  return numMatches
def appendToFile(strsToAppend,fileName):
  """Append multiple string to the end of a file
  """
  
  file=open(fileName,mode='r')
  fileText=file.read()
  file.close()
  for strToAppend in strsToAppend:
    fileText+=strToAppend
  file=open(fileName,mode='w')
  file.write(fileText)
  file.close()
def genNameAndPass(length=16
  ,chars=string.ascii_uppercase+string.ascii_lowercase+string.digits):
  
  name=''
  for i in range(length):
    name+=random.SystemRandom().choice(chars)
    
  passwd=''
  for i in range(length):
    passwd+=random.SystemRandom().choice(chars)
  
  return (name,passwd)
def execute(func,*args,dry=False,**kwargs):
  if not dry:
    func(*args,**kwargs)
  else:
    commandStr=func.__name__+"("
    firstArg=True
    for arg in args:
      if firstArg:
        commandStr+=str(arg)
        firstArg=False
      else:
        commandStr+=","+str(arg)
    for key in kwargs:
      if firstArg:
        commandStr+=key+"="+str(kwargs[key])
        firstArg=False
      else:
        commandStr+=","+key+"="+str(kwargs[key])
    commandStr+=")"
    print(commandStr)
def setupMediaWiki(settings={},dry=False):
  """Downloads media wiki and puts it into document root
  """
  
  (adminName,adminPassWd)=genNameAndPass()
  (dummy,dbPassWd)=genNameAndPass()
  
  defaultSettings={
    "version":"1.27"
    ,"patch":"0"
    ,"wikiName":"Test Wiki"
    ,"wikiReadPerm":"user"          #public, user, sysop
    ,"wikiEditPerm":"user"          #public, user, sysop
    ,"wikiAccCreatePerm":"sysop"    #public, user, sysop
    ,"wikiAdminName":adminName
    ,"wikiAdminPass":adminPassWd
    ,"server":"http://206.167.181.71"
    ,"enableUploads":False
    ,"logoURL":"$wgResourceBasePath/resources/assets/cc-cloud-wiki-logo.png"
    ,"extraConfigLines":[]
    ,"dbserver":"localhost"
    ,"dbuser":"root"
    ,"dbpass":dbPassWd
    ,"documentRoot":"/var/www/html"
    ,"tmpDir":"/tmp"
    ,"owner":"www-data"
    ,"group":"www-data"
    ,"cleanUp":True
    ,"purgeDocRoot":True
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
  execute(subprocess.call,["wget",url,"--directory-prefix="
    +settings["tmpDir"]],dry=dry)
  execute(subprocess.call,["tar","-xzf",tmpMediaWikiDir+".tar.gz","-C"
    ,settings["tmpDir"]],dry=dry)
  
  #remove existing files in document root
  if settings["purgeDocRoot"]:
    paths=glob.glob(settings["documentRoot"]+"/*")
    for path in paths:
      try:
        execute(os.remove,path,dry=dry)
      except IsADirectoryError:
        execute(shutil.rmtree,path,dry=dry)
  
  #move files to document root
  paths=glob.glob(tmpMediaWikiDir+"/*")
  for path in paths:
    pathBaseName=os.path.basename(path)
    execute(shutil.move,path,os.path.join(settings["documentRoot"]
      ,pathBaseName),dry=dry)
  
  #change owner and group
  for path in paths:
    pathBaseName=os.path.basename(path)
    execute(shutil.chown,os.path.join(settings["documentRoot"],pathBaseName)
      ,user=settings["owner"]
      ,group=settings["group"],dry=dry)
  
  #clean up temporary files
  if settings["cleanUp"]:
    execute(os.removedirs,tmpMediaWikiDir,dry=dry)
    execute(os.remove,tmpMediaWikiDir+".tar.gz",dry=dry)
  
  #set mysql root password (initial install has no root password)
  execute(subprocess.call,["mysqladmin","-u","root","password",settings["dbpass"]],dry=dry)
  
  #do basic configure of the wiki
  execute(subprocess.call,["php"
    ,os.path.join(settings["documentRoot"],"maintenance/install.php")
    ,"--scriptpath", ""
    ,"--pass",settings["wikiAdminPass"]
    ,"--server",settings["server"]
    ,"--dbuser",settings["dbuser"]
    ,"--dbpass",settings["dbpass"]
    ,"--dbserver",settings["dbserver"]
    ,settings["wikiName"]
    ,settings["wikiAdminName"]],dry=dry)
  
  localSettingsFile=os.path.join(settings["documentRoot"],"LocalSettings.php")
  
  #enable file uploads
  if settings["enableUploads"]:
    execute(replaceStrInFile,"$wgEnableUploads = false;"
      ,"$wgEnableUploads = true;",localSettingsFile,dry=dry)
  
  #copy default cc-wiki-logo
  src=os.path.join(settings["tmpDir"]
    ,"cloud-init-mediawiki/cc-cloud-wiki-logo.png")
  dest=os.path.join(settings["documentRoot"]
    ,"resources/assets/cc-cloud-wiki-logo.png")
  execute(shutil.copy,src,dest,dry=dry)
  
  #set logo
  execute(replaceStrInFile,
    "$wgLogo = \"$wgResourceBasePath/resources/assets/wiki.png\";"
    ,"$wgLogo = \""+settings["logoURL"]+"\";"
    ,localSettingsFile,dry=dry)
    
  #disable emails as no email client is configured
  execute(replaceStrInFile,"$wgEnableEmail = true;","$wgEnableEmail = false;"
    ,localSettingsFile,dry=dry)
  execute(replaceStrInFile,"$wgEnableUserEmail = true;","$wgEnableUserEmail = false;"
    ,localSettingsFile,dry=dry)
  
  
  #secure LocalSettings.php, only owner needs read access
  execute(shutil.chown,localSettingsFile,user=settings["owner"]
    ,group=settings["group"],dry=dry)
  execute(os.chmod,localSettingsFile,0o400,dry=dry)
  
  #Set read permissions
  if settings["wikiReadPerm"]=="user" or settings["wikiReadPerm"]=="sysop":
    execute(appendToFile,["$wgGroupPermissions['*']['read'] = false;\n"]
      ,localSettingsFile,dry=dry)
    if settings["enableUploads"]:
      print("WARNING: read permission not public but uploads are enabled."
        +" The public will still be able to see uploads if they know the "
        +"correct url to go directly to the file.")
  if settings["wikiReadPerm"]=="sysop":
    execute(appendToFile,["$wgGroupPermissions['user']['read'] = false;\n"]
      ,localSettingsFile,dry=dry)
    
  #ensure the login page is always readable
  execute(appendToFile,["$wgWhitelistRead = array (\"Special:Userlogin\");\n"]
    ,localSettingsFile,dry=dry)
  
  #Set edit permissions
  if settings["wikiEditPerm"]=="user" or settings["wikiEditPerm"]=="sysop":
    execute(appendToFile,["$wgGroupPermissions['*']['edit'] = false;\n"]
      ,localSettingsFile,dry=dry)
  if settings["wikiEditPerm"]=="sysop":
    execute(appendToFile,["$wgGroupPermissions['user']['edit'] = false;\n"]
      ,localSettingsFile,dry=dry)
  
  #Set account creation permissions
  if settings["wikiAccCreatePerm"]=="user" \
    or settings["wikiAccCreatePerm"]=="sysop":
    execute(appendToFile,["$wgGroupPermissions['*']['createaccount'] = false;\n"]
      ,localSettingsFile,dry=dry)
  if settings["wikiAccCreatePerm"]=="sysop":
    execute(appendToFile,["$wgGroupPermissions['user']['createaccount'] = false;\n"]
      ,localSettingsFile,dry=dry)
  
  #add any extra configuration options explicitly set
  execute(appendToFile,settings["extraConfigLines"],localSettingsFile,dry=dry)
  
  return (settings["wikiAdminName"],settings["wikiAdminPass"],settings)
def securePHP(dry=False):
  """Ensures some basic php security settings are set
  """
  
  #ensure register_globals is disabled
  numReplaces=replaceStrInFileRe(
    "(?<!([^\s]))register_globals[\s]*=[\s]*((O|o)n|(O|o)ff)"
    ,"register_globals = Off","/etc/php5/apache2/php.ini")
  if numReplaces==0:#if no strings replaced add it
    execute(appendToFile,"register_globals = Off\n","/etc/php5/apache2/php.ini"
      ,dry=dry)
  
  #disable allow_url_fopen
  numReplaces=replaceStrInFileRe(
    "(?<!([^\s]))allow_url_fopen[\s]*=[\s]*((O|o)n|(O|o)ff)"
    ,"allow_url_fopen = Off","/etc/php5/apache2/php.ini")
  if numReplaces==0:#if no strings replaced add it
    execute(appendToFile,"allow_url_fopen = Off\n","/etc/php5/apache2/php.ini"
      ,dry=dry)
  
  #ensure session.use_trans_sid is off
  numReplaces=replaceStrInFileRe(
    "(?<!([^\s]))session.use_trans_sid[\s]*=[\s]*[0-1]"
    ,"session.use_trans_sid = 0","/etc/php5/apache2/php.ini")
  if numReplaces==0:#if no strings replaced add it
    execute(appendToFile,"session.use_trans_sid = 0\n"
      ,"/etc/php5/apache2/php.ini",dry=dry)
  
  #restart apache for settings to take effect
  execute(restartApache,dry=dry)
def secureMySQL(dry=False):
  """Ensures some basic MySQL security settings are set
  """
  
  #is default for mysql on ubuntu 14.0.4
  #bind-address            = 127.0.0.1
  pass
def secureApache(documentRoot,dry=False):
  """
  """
  
  #disallow any execution of files in the uploads directory
  uploadDirSettings=(
    "<Directory "+os.path.join(documentRoot,"images/")+">\n"
    "# Ignore .htaccess files\n"
    "AllowOverride None\n"
    "\n"
    "# Serve HTML as plaintext, don't execute SHTML\n"
    "AddType text/plain .html .htm .shtml .php .phtml .php5\n"
    "\n"
    "# Don't run arbitrary PHP code.\n"
    "php_admin_flag engine off\n"
    "\n"
    "# If you've other scripting languages, disable them too.\n"
    "</Directory>\n")
  execute(appendToFile,uploadDirSettings,"/etc/apache2/apache2.conf",dry=dry)
  execute(restartApache,dry=dry)
def restartApache():
  """Restarts apache2
  """
  
  subprocess.call(["service","apache2","restart"])
def validateHostName(hostName):
    """source:
    https://en.wikipedia.org/wiki/Hostname#Restrictions_on_valid_host_names
    
    1) must be under 253 characters
    2) each label (seperated by ".") must be between 1 and 63 characters long
    3) each label must contain only ASCII letters 'a' - 'Z' (case-insensitive)
      , '0' - '9', and '-'
    4) labels must not start or end with a '-'
    5) must be case-insensitive (i.e. will convert upper case to lower case)
    
    """
    
    allowed=set(string.ascii_lowercase+string.digits+"-"+string.ascii_uppercase)
    
    #1) check for overall length
    if(len(hostName)>252):
      raise Exception("hostName \""+hostName+"\" is longer than 253 characters")
    
    labels=hostName.split(".")
    
    
    for label in labels:
      
      #2) check for length of label
      if not (len(label) <= 63 and len(label) >= 1):
        raise Exception("hostName label \""+label+"\" is "+str(len(label))
        +" characters long which is not between 1 and 63 characters long")
      
      #3) check for invalid characters
      if not (set(label) <= allowed):
        raise Exception("hostName label \""+label
          +"\" contains characters which are not allowed, \""
          +str(set(label)-allowed)+"\"")
      
      #4) must not start with a '-'
      if label[0]=='-':
        raise Exception("label \""+label
        +"\" starts with a '-' which is not allowed")
    
    return True
def verifyServerName(serverName):
  
  #is it an IP
  try:
    socket.inet_aton(serverName)
  except socket.error:
    #is it a domain Name
    if not validateHostName(serverName):
      raise Exception(serverName+" is not a valid domain name or IP")
def main():
  
  #parse command line options
  (options,args)=parseOptions()
  
  #ensure we have the right number of arguments
  if len(args) != 1:
    raise Exception("Must have at least one argument specifying the wiki "
      +"server's IP or Domain name")
  
  #verify that the server name is valid (will not contain an http://)
  verifyServerName(args[0])
  
  #map options onto settings
  dryRun=options.dryRun
  settings={}
  settings["version"]=options.version
  settings["patch"]=options.patch
  settings["wikiName"]=options.wikiName
  settings["wikiReadPerm"]=options.wikiReadPerm
  settings["wikiEditPerm"]=options.wikiEditPerm
  settings["wikiAccCreatePerm"]=options.wikiAccCreatePerm
  settings["wikiAdminName"]=options.wikiAdminName
  settings["server"]="http://"+args[0]
  settings["enableUploads"]=options.enableUploads
  settings["extraConfigLines"]=options.extraConfigLines
  settings["logoURL"]=options.logoURL
  
  
  #adjust some php settings to improve security
  securePHP(dry=dryRun)
  
  #adjust some mysql settings to improve security
  secureMySQL(dry=dryRun)
  
  #setup the wiki
  (adminUser,adminPassWd,settingsUsed)=setupMediaWiki(
    settings=settings,dry=dryRun)
  
  #adjust some apache settings to improve security
  secureApache(settingsUsed["documentRoot"],dry=dryRun)
  
  print("Wiki Admin Username:"+adminUser)
  print("Wiki Admin password:"+adminPassWd)
if __name__ == "__main__":
 main()