#!/usr/bin/env python2
import feedparser
import subprocess
import json
import os
import sys
import argparse

config = {}
cmdargs = {}

def log(message, source=None):
	if not source is None:
		print "[%s] %s" % (source, message)
	else:
		print message

class lockfile():
	def __init__(self, path):
		self._path = path

	def lock(self):
		if os.path.exists(self._path):
			try:
				f = open(self._path,"r")
				pid = f.read().strip()
				f.close()
				pids= [pid for pid in os.listdir('/proc') if pid.isdigit()]
				return pid in pids
			except:
				print "failed to write to lock file"	
			return False
		else:
			f = open(self._path,"w")
			f.write(str(os.getpid())+"\n")
			f.close()
			return True

	def unlock(self):
		if os.path.exists(self._path):
			os.remove(self._path)

class seenList():
	def __init__(self, path):
		self._path = path
		if os.path.exists(self._path):
			f = open(self._path,"r")
			self._list = json.load(f)
			f.close()
		else:
			self._list = []

	def _save(self):
		f = open(self._path,"w")
		json.dump(self._list,f)
		f.close()

	def hasSeen(self, uid):
		return uid in self._list

	def see(self, uid):
		if not self.hasSeen(uid):
			self._list.append(uid)
			self._save()

class feed():
	def __init__(self, name, url, seenlist, command):
		self._url = url
		self._seenlist = seenList(seenlist)
		self._name = name
		self._items = None
		self._exec = command

	def fetch(self):
		log("Fetching feed...", self._name)
		feed = feedparser.parse(self._url)
		i = 0
		self._items = []
		for item in feed["items"]:
			if not self._seenlist.hasSeen(item["guid"]):
				i+=1
				self._items.append(feedItem(item))

		log("Found %i new items"% (i), self._name)

	def getItems(self):
		return self._items

	def run(self):
		if self._items is None:
			self.fetch()
		for i in self.getItems():
			try:
				if not cmdargs.noop:
					i.run(self._exec)
				self._seenlist.see(i.guid())
			except subprocess.CalledProcessError as e:
				log("Error running command",self._name)


class feedItem():
	def __init__(self, properties):
		self._fmtkeys = ["title","link","guid"]
		self._props = properties

	def formatKeys(self):
		keys = {}
		for k in self._fmtkeys:
			keys[k] = getattr(self, k)()

		return keys

	def title(self):
		if "title" in self._props.keys():
			return self._props["title"]
		else:
			return ""

	def guid(self):
		return self._props["guid"]

	def link(self):
		if "enclosures" in self._props.keys() and len(self._props["enclosures"]) > 0:
			return self._props["enclosures"][0]["href"]
		elif "link" in self._props.keys():
			return self._props["link"]
		else:
			return ""

	def run(self, command):
		cmd = command % self.formatKeys()
		subprocess.check_call(cmd, shell=True)


def loadconfig(cfgFile):
	global config
	f = open(cfgFile,"r")
	config = json.load(f)
	f.close()

def main():
	global cmdargs

	parser = argparse.ArgumentParser(description="Download feed enclosures")
	parser.add_argument("--config",default=os.path.join(os.getcwd(),"config.json"),help="The configuration file to use",dest="cfgFile")
	parser.add_argument("--feed",default="",help="feed to process",dest="feed")
	parser.add_argument("--noop",default=False,action='store_true',help="Don't download anything, just update the seen list",dest="noop")

	cmdargs = parser.parse_args()

	loadconfig(cmdargs.cfgFile)

	if cmdargs.feed == "":
		for f in config['feeds'].keys():
			newargs = sys.argv[1:]
			if not "--feed" in newargs:
				newargs.append("--feed")
				newargs.append(f)

			subprocess.Popen([sys.executable, sys.argv[0]]+newargs)
	else:
		fd = config.copy()
		fd.update(config['feeds'][cmdargs.feed])
		del fd["feeds"]
		log("Trying to get a lock...",cmdargs.feed)
		lock = lockfile(fd["seenfile"]+".lock")
		if lock.lock():
			feedobj = feed(cmdargs.feed,fd["url"],fd["seenfile"],fd["exec"])
			feedobj.run()
			lock.unlock()
		else:
			log("Can't get a lock",cmdargs.feed)

main()
