# feedto

RSS -> Anything

Use feedto as:
* A simple, no-nonsense command line podcatcher
* Trigger updates based on new RSS feed items

## Usage

	usage: feedto.py [-h] [--config CFGFILE] [--feed FEED] [--noop]

	Feed -> Anything

	optional arguments:
	  -h, --help        show this help message and exit
	  --config CFGFILE  The configuration file to use, or ./config.json by default
	  --feed FEED       Specific feed to process. If ommited, all feeds will be
	                    processed in parallel
	  --noop            Don't download anything, just update the seen list

## Configuration File

For examples, see [the wiki](https://github.com/insertjokehere/feedto/wiki/Examples).

feedto requires a json formatted configuration file. At a minimum, it should contain a map, with one key 'feeds'. This should contain another map, with feed names paired with configuration maps. Any keys besides 'feeds' in the top level map are merged with the feed configuration maps to produce the final map (see '[Shared configuration](https://github.com/insertjokehere/feedto/wiki/Examples)').

### Feed configuation keys

 * 'url': The URL of the feed to fetch (required)
 * 'exec': The command to execute for each new item. Support [python string replacement]() with a number of keys (see 'string replacement' below) (required)
 * 'seenfile': The file to record GUIDs of feed items already seen (required)
 * 'mods': An array of feed modifiers to use (See 'Feed modifiers' below)

### String replacement

Feed items currently support the following replacement keys:

* 'title': The title of the feed item
* 'link': The url of the first enclosure item, or the url linking to the feed item if this is not present
* 'guid': The GUID of the feed item