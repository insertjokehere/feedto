#!/usr/bin/env python2
import feedparser
import subprocess
import json
import os
import sys

config = {}

def loadconfig(cfgFile):
	global config
	f = open(cfgFile,"r")
	config = json.load(f)
	f.close()

def main():
	if len(sys.argv) > 1:
		cfgFile = sys.argv[1]
	else:
		cfgFile = os.path.join(os.getcwd(),"config.json")

	loadconfig(cfgFile)

	for f in config['feeds']:
		fd = config.copy()
		fd.update(f)
		del fd["feeds"]
		rss(fd)


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
			#print args["exec"] % {'url':item["links"][0]["href"]}
			subprocess.check_call(args["exec"] % {'url':item["links"][0]["href"]},shell=True)

			#_add(item["links"][0]["href"],"TV")
			print item["links"][0]["href"]
			seenlist.append(item["guid"])
	f = open(args['seenfile'],"w")
	json.dump(seenlist,f)
	f.close()

main()
