#!/usr/bin/env python2
import feedparser
import subprocess
import json
import os
import sys
import argparse

config = {}

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

	parser = argparse.ArgumentParser(description="Download feed enclosures")
	parser.add_argument("--config",default=os.path.join(os.getcwd(),"config.json"),help="The configuration file to use",dest="cfgFile")
	parser.add_argument("--feed",default="",help="feed to process",dest="feed")

	args = parser.parse_args()

	loadconfig(args.cfgFile)

	if args.feed == "":
		for f in config['feeds'].keys():
			subprocess.Popen([sys.executable, sys.argv[0], "--config", args.cfgFile, "--feed", f])
	else:
		fd = config.copy()
		fd.update(config['feeds'][args.feed])
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
			cmd = args["exec"] % {'url':url, 'serverpath':"/".join(url.split("/")[2:-1])+"/"}
			print cmd
			subprocess.check_call(cmd, shell=True)

			#_add(item["links"][0]["href"],"TV")
			print item["links"][0]["href"]
			seenlist.append(item["guid"])
			f = open(args['seenfile'],"w")
			json.dump(seenlist,f)
			f.close()

main()
