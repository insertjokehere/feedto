#!/usr/bin/env python2
import feedparser
import subprocess
import json
import os
import sys
import argparse
import pipes 
import re

config = {}
cmdargs = {}

def log(message, source=None):
	if not source is None:
		print "[%s] %s" % (source, message)
	else:
		print message

class modification(object):
	def __init__(self, args):
		self.args = args
		del self.args["name"]

	def apply(self, feed):
		pass

class modFilter(modification):
	def __init__(self, args):
		super(modFilter, self).__init__(args)

	def apply(self, feed):
		on = self.args["on"]
		prog = re.compile(self.args["pattern"])
		for i in feed.getItems():
			if on in i._fmtkeys:
				if prog.match(getattr(i,on)()):
					log("Ignoring item %s" % i.title(), "filter")
					feed.rmItem(i.guid())

class modRewrite(modification):
	def __init__(self, args):
		super(modRewrite, self).__init__(args)

	def apply(self, feed):
		prog = re.compile(self.args["pattern"])
		subst = self.args["subst"]
		on = self.args["on"]
		for i in feed.getItems():
			if on in i._fmtkeys:
				old = feed.getFormatArg(on)
				new = prog.sub(subst,old)
				log("'%s' => '%s'" % (old, new), "rewrite")
				feed.setFormatArg(on, new)

mods = {"filter":modFilter, "rewrite":modRewrite}

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
		self._mods = []

	def addMod(self, mod):
		self._mods.append(mod)

	def applyMods(self):
		for m in self._mods:
			m.apply(self)

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

	def rmItem(self, uid):
		self._seenlist.see(uid)
		for i in self._items:
			if i.guid() == uid:
				self._items.remove(i)

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
		self._fmtargs = {}
		self._props = properties

	def getFormatArg(self,arg):
		if arg in self._fmtargs.keys():
			return self._fmtargs[arg]
		elif arg in self._fmtkeys:
			self._fmtargs[arg] = pipes.quote(getattr(self, k)())
			return self._fmtargs[arg]
		else:
			return ""

	def setFormatArg(self, arg, value):
		self._fmtargs[arg] = value

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

	parser = argparse.ArgumentParser(description="Feed -> Anything")
	parser.add_argument("--config",default=os.path.join(os.getcwd(),"config.json"),help="The configuration file to use, or ./config.json by default",dest="cfgFile")
	parser.add_argument("--feed",default="",help="Specific feed to process. If ommited, all feeds will be processed in parallel",dest="feed")
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
			feedobj.fetch()

			if "mods" in fd.keys():
				for m in fd["mods"]:
					if "name" in m and m["name"] in mods.keys():
						feedobj.addMod(mods[m["name"]](m))

				feedobj.applyMods()

			feedobj.run()
			lock.unlock()
		else:
			log("Can't get a lock",cmdargs.feed)

main()
