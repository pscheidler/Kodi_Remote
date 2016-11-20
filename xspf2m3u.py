__author__ = 'pscheidler'

#!/usr/bin/env python
# This file is part of xspf2m3u
#Creator: Anthony Hawkes
#Email: ant@boxzen.com
#Created On: 3/12/2010
#Last Modified:
#Last Modified By:
#xspf2m3u is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#xspf2m3u is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#See <http://www.gnu.org/licenses/>
from mutagen.easyid3 import EasyID3
from BS4 import BeautifulStoneSoup
import os, sys, getopt, sqlite3, xml, re

database = "./musicdb.sqlite"
m3u_file = "./xspf.m3u"
media = ['.mp3']
write_to_m3u = []
verbose = 0


def main(argv):
    """Main program"""
    global m3u_file, verbose
    try:
        opts, args = getopt.getopt(argv, "hb:x:m:v", ["help", "build=", "xspf=", "m3u=", 'verbose'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit(2)
        elif opt in ("-b", "--build"):
            builddb(arg)
            sys.exit(0)
        elif opt in ("-m", "--m3u"):
            m3u_file = arg
        elif opt in ("-x", "--xspf"):
            xspf = arg
            if not os.path.exists(xspf):
                print
                print
                "***xspf not found***"
                print
                usage()
                sys.exit(2)
        elif opt in ("-v", "--verbose"):
            verbose = 1
    try:
        xspf
    except NameError:
        print
        print
        "***No XSPF file specified***"
        print
        usage()
        sys.exit(2)
    no_db = not os.path.exists(database)
    if no_db:
        print
        print
        "***DB does not exist, try build with -b***"
        print
        usage()
        sys.exit(1)
    connection = sqlite3.connect(database)
    process_xspf(xspf, connection)
    write_m3u(write_to_m3u, m3u_file)


def builddb(music_path):
    """This kicks off building the database, other subroutines called in order are: addtodb"""
    global database
    connection = connectdb(database)
    print
    "Now building DB this may take some time..."
    for dirpath, dirnames, filenames in os.walk(music_path):
        for file in filenames:
            if os.path.splitext(file)[1] in media:
                filename_path = os.path.join(dirpath, file)
                info = EasyID3(filename_path)
                artist = info['artist'][0]
                title = info['title'][0]
                addtodb(filename_path, artist, title, connection)


def addtodb(filename_path, artist, title, db):
    """This file adds data to the database in see sub connectdb for structure and details. Other subroutines claled in order are: None"""
    if verbose:
        print
        "Adding ", filename_path, artist, title, "to db"
    cursor = db.cursor()
    cursor.execute("INSERT INTO lib (path, artist, title) VALUES(?, ?, ?)", (filename_path, artist, title))
    db.commit()


def connectdb(db):
    """This is a BUILD DB subroutine only - it is desinged to purge db if exists or create if not exists"""
    create = not os.path.exists(db)
    db = sqlite3.connect(db)
    db.text_factory = str
    if create:
        cursor = db.cursor()
        cursor.execute("CREATE TABLE lib ("
                       "id INTEGER PRIMARY KEY	AUTOINCREMENT UNIQUE NOT NULL, "
                       "path TEXT UNIQUE NOT NULL, "
                       "artist TEXT, "
                       "title TEXT)")
        db.commit()
    else:
        cursor = db.cursor()
        cursor.execute("DELETE FROM lib")
        cursor.execute("VACUUM")
        db.commit()
    return db


def process_xspf(xspf, db):
    """This reads the xspf file"""
    soup = BeautifulStoneSoup(open(xspf).read())
    for trk in soup.findAll('track'):
        title = trk.title.string
        artist = trk.creator.string
        do_find(artist, title, db)


def do_find(artist, title, db):
    """This does the find on the database and adds path to the list of paths to be appened to the m3u"""
    global write_to_m3u
    a = re.sub(r"[^A-Za-z0-9]", '%', artist)
    t = re.sub(r"[^A-Za-z0-9]", '%', title)
    #db = sqlite3.connect(db)
    db.text_factory = str
    cursor = db.cursor()
    #query = "SELECT path FROM lib WHERE artist LIKE '"+a+"' AND title LIKE '"+t+"' LIMIT 1"
    #print query
    cursor.execute("SELECT path FROM lib WHERE artist LIKE ? AND title LIKE ? LIMIT 1", (a, t))
    try:
        path = cursor.fetchone()[0]
        if verbose:
            print
            artist, title, "Found adding to m3u"
        write_to_m3u.append(path)
    except:
        if verbose:
            print
            artist, title, "Not Found"
        else:
            pass


def write_m3u(contents, filename):
    """This actually writes the m3u file"""
    handle = open(filename, 'w')
    for line in contents:
        print >> handle, line


def usage():
    """The funky usage"""
    print
    """Usage: xspf2m3u [OPTIONS]

Tries to convert a XSPF file to a local format
eg. xspf -x xspf_file.xspf -m m3u_file_to_create.m3u

Notes:
-Processes MP3 only.
-Will ignore special characters eg.
	If the xspf contains: Marcel Woods - Advanced(Original Mix) this
	 will also match to Marcel Woods - Advanced - Original Mix,
	 this feature is useful for Beatport and other site users.

Options:
-b, --buid=[MUSIC DB LOCATION]	Builds the music database
-v, --verbose			Outputs everything loudly
-h, --help			Shows this...
-x, --xspf=[XSPF FILENAME]	Use to specific the xspf file to process
-m, --m3u=[M3U FILE TO CREATE]	Use this to specific m3u filename
				 Optional - defaults to ./xspf.m3u

Make sure you build your database first with xspf2m3u -b
	"""

#call the main sub
main(sys.argv[1:])