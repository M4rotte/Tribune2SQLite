#!/usr/bin/env python3

"""Tribune2sqlite.py: Store mussel posts in a database file and print a few statistics on it."""
__author__ = "M4rotte"
__copyright__ = "Copyright 2016, Institut Marotte pour un Mouling de Qualitäy"
__license__ = "GPL"
__version__ = "0.4"

import sys                                               
import requests                                          
import xml.etree.ElementTree as etree                    
import sqlite3                                           
import html.parser                        # for its unescape() function
from time import sleep, ctime                            
import lockfile                                          
import daemon                                            
from os import kill,getpid,remove,path                   

import Config 

def updatedb(url,dbfile):
  """updatedb(str,str): Get mussel posts from the piling indicated by url and stuff it in dbfile 
  returns (0, nb_newpost) on success, (1, error) on failure."""	
  session = requests.Session()
  headers = {"User-Agent": "", "Accept": "application/xml"}
  r = requests.Request('GET', url, headers=headers)
  request = r.prepare()
  try:
    response = session.send (request)
  except requests.exceptions.ConnectionError as error:
    return (1, error)
  try:  
    tribune = etree.fromstring(response.text)
  except etree.ParseError as error:
    return (1, error)
  connection = sqlite3.connect(dbfile)
  cursor = connection.cursor()
  # Create the posts table if not exists
  cursor.execute('create table if not exists posts (id int primary key, time int, message text, login text, info text)')

  nb_newposts = 0
  for post in tribune:
    values =  (post.attrib['id'], post.attrib['time'], post[1].text, post[2].text, post[0].text)
    try:
      cursor.execute("insert into posts values (?, ?, ?, ?, ?)", values)
      nb_newposts += 1
    except sqlite3.IntegrityError as error:
      pass 
  connection.commit()
  cursor.close()
  return (0, nb_newposts)

def  calc_stats(dbfile,nb_newposts):

  # Posts statistics
  connection = sqlite3.connect(dbfile)
  cursor = connection.cursor()
  ret = "\n* "+ctime()+" *\n"
  # New posts
  ret += "New\t"+str(nb_newposts)+"\n"
  # Total posts
  cursor.execute("select count(*) from posts")
  ret  += "Total\t"+str(cursor.fetchone()[0])+"\n"
  cursor.execute("select login, time from posts order by time desc")
  last = cursor.fetchone()
  ret += "Last\t"+str(last[1])+" "+str(last[0])+"\n"
  # Last post
  ret += "\nPosts Top 5 :\n"
  # Posts per mussel
  cursor.execute("select count(*) as count, login from posts group by login order by count desc limit 5")
  nb_posts = cursor.fetchall()
  for mussel in nb_posts:
    ret += str(mussel[0])+"\t"+str(mussel[1])+"\n"
  # User-agent statistics
  cursor.execute("select count(*) as count, info from posts group by info order by count desc limit 5")
  ua_stats = cursor.fetchall()  
  ret += "\nUser-Agents Top 5 :\n"
  for ua in ua_stats:
    ret += str(ua[0])+"\t"+html.parser.HTMLParser().unescape(str(ua[1]))+"\n"
  cursor.close()
  return (ret, nb_newposts)

def feed_the_db():

  while True:
    piling = Config.URL
    dbfile = Config.PILING_DB
    update = updatedb(piling,dbfile)
    if not update[0]:
      stats = calc_stats(dbfile, update[1])
    else:
      print(update[1])
      return 1
    sleep_time = 300 - (stats[1] * 2)
    logfile = open(Config.PILING_LOG, 'a')
    logfile.write(stats[0]+"\nI'll sleep for "+str(sleep_time)+" s\n")
    logfile.close()
    sleep(sleep_time)

def start():
  with context:
    pidfile = open(Config.WDIR+scriptname+".pid",'w')
    pidfile.write(str(getpid()))
    pidfile.close()
    feed_the_db()

def stop(pid):
  try:
    kill(int(pid),15)
  except ProcessLookupError:
    print("Nothing to kill… (No process with PID "+pid+")")

if __name__ == "__main__":
  scriptname = sys.argv[0]
  context = daemon.DaemonContext(
  working_directory=Config.WDIR,
  pidfile=lockfile.FileLock(Config.WDIR+scriptname),
  stdout=sys.stdout,
  stderr=sys.stderr)
  try:
    if sys.argv[1] == 'start':
      if not path.isfile(Config.WDIR+scriptname+".pid"):
        start()
      else:
        print(scriptname+".pid"+" exists… Won't start.")
        exit (1)  
    elif sys.argv[1] == 'stop':
      try:
        pidfile = open(Config.WDIR+scriptname+".pid",'r')
        pid = pidfile.read()
        pidfile.close()
        remove(scriptname+".pid")
        print(scriptname+" (PID "+pid+")")
        stop(pid)
      except FileNotFoundError:
        print("Nothing to kill… ("+scriptname+".pid not found)")
    else:
      print("\nUnknown option : "+sys.argv[1]+"\n\nUsage "+sys.argv[0]+" <start|stop>\n")   
  except IndexError:
    print("\nUsage "+sys.argv[0]+" <start|stop>\n")




