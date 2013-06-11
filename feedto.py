#!/usr/bin/env python2
import feedparser
import subprocess
import json
import os
import sys
import argparse

config = {}
cmdargs = {}

def lockFile(lockfile):
	if os.path.exists(lockfile):
		return False
	else:
		f = open(lockfile,"w")
		f.close()
		return True

def unlock(lockfile):
	if os.path.exists(lockfile):
		os.remove(lockfile)

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
		if lockFile(fd["seenfile"]+".lock"):
			rss(fd)
			unlock(fd["seenfile"]+".lock")

def rss(args):
	feed = feedparser.parse(args['url'])
	seenlist = []
	if os.path.exists(args['seenfile']):
		f = open(args['seenfile'],"r")
		seenlist = json.load(f)
		f.close()
	for item in feed["items"]:
		if not item["guid"] in seenlist and "links" in item.keys():
			#print item["guid"]
			url = item["links"][0]["href"]

			replace = {}

			for k in item.keys():
				replace[k] = item[k]

			replace['url'] = url
			replace['serverpath'] = "/".join(url.split("/")[2:-1])+"/"

			cmd = args["exec"] % replace

			if not cmdargs.noop:
				subprocess.check_call(cmd, shell=True)

			#_add(item["links"][0]["href"],"TV")
			print item["links"][0]["href"]
			seenlist.append(item["guid"])
			f = open(args['seenfile'],"w")
			json.dump(seenlist,f)
			f.close()

main()
