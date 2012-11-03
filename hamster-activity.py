#!/usr/bin/python2.7
# encoding: utf-8

import gobject
import datetime as dt
import dbus
import os
from dbus.mainloop.glib import DBusGMainLoop
import fileinput
import sys
import urllib

BASEDIR = '/home/user'
GTK_BOOKMARKS_FILE = '/home/user/.gtk-bookmarks' 
DOWNLOAD_DIR = u'/home/user/Téléchargements' 
DOWNLOAD_DEFAULT = u'/tmp' 
DESKTOP_DIR = u'/home/user/Bureau' 
DESKTOP_DEFAULT = u'/home/user' 

HAMSTER_INTERFACE = 'org.gnome.Hamster'
TELEPATHY_DBUS = 'org.freedesktop.Telepathy.Connection.gabble.jabber'
TELEPATHY_DBUS_PRESENCE_INTERFACE = 'org.freedesktop.Telepathy.Connection.Interface.SimplePresence'
TELEPATHY_ACCOUNT_PREFIX = 'user@domain'

def busAsPath(bus):
    return "/" + bus.replace(".", "/")

def jidToDbus(jid):
    return jid.replace(".", "_2e").replace("@", "_40").replace("/", "_2f")

class HamsterIntegration():

    def __init__(self, bus):
        self.bus = bus
        self.bus.add_signal_receiver(self.hamster_facts_changed, 'FactsChanged', HAMSTER_INTERFACE)
        self.session_presence = self.bus.get_object(HAMSTER_INTERFACE,'/org/gnome/Hamster')

    def deactivate(self):
        self.bus.remove_signal_receiver(self.hamster_facts_changed,
            "FactsChanged", dbus_interface=HAMSTER_INTERFACE)

    def get_path_from_fact(self,fact):
        directory = BASEDIR
        
        if fact['category']:
            directory += '/'+fact['category']
        directory += '/'+fact['fact']
        
        directory = directory.encode('utf8')
        
        return directory  

    
    def delete_empty_dir(self,dir_path):
        if os.path.isdir(dir_path):
            files = os.listdir(dir_path)
            if len(files) == 0:
                os.rmdir(dir_path)
    
    def move_link(self,from_dir,to_dir):
        if os.path.islink(from_dir):
            os.unlink(from_dir)
        self.delete_empty_dir(from_dir)
        os.symlink(to_dir,from_dir)
        
    def change_im_state(self,new_status):
        mybus = TELEPATHY_DBUS+'.' + jidToDbus(TELEPATHY_ACCOUNT_PREFIX)

        for bus in self.bus.list_names():
            if bus.startswith(mybus):
                self.bus.get_object(bus, busAsPath(bus)).SetPresence("available", new_status,
                dbus_interface = "org.freedesktop.Telepathy.Connection.Interface.SimplePresence")

    def hamster_facts_changed(self, *args, **kw):
        # get hamster tags
        facts = self.session_presence.GetTodaysFacts(
            dbus_interface=HAMSTER_INTERFACE)
        if not facts:
            return
        if self.from_dbus_fact(facts[-1])['end_time']:
            self.move_link(DOWNLOAD_DIR,DOWNLOAD_DEFAULT)
            self.move_link(DESKTOP_DIR,DESKTOP_DEFAULT)
            self.change_im_state('')
            return

        last_fact = self.from_dbus_fact(facts[-1])
        bookmark_replace_string = ''
        if len(facts) > 1:
            previous_fact = self.from_dbus_fact(facts[-2])
        
            previous_fact_directory = self.get_path_from_fact(previous_fact)
        
            #delete previous dir if empty
            self.delete_empty_dir(previous_fact_directory)
            
            bookmark_replace_directory = previous_fact_directory
        else:
            bookmark_replace_directory = BASEDIR
        
        #create new ones    
        last_fact_directory = self.get_path_from_fact(last_fact)
        
        if not os.path.exists(last_fact_directory):
            os.makedirs(last_fact_directory)

        directory_url = 'file://'+urllib.pathname2url(last_fact_directory)
        bookmark_replace_string = 'file://'+urllib.pathname2url(bookmark_replace_directory)
        
#        found=False
#        for line in fileinput.input(GTK_BOOKMARKS_FILE, inplace=1):
#            if bookmark_replace_string+"\n" == line:
#                found=True
#                print directory_url
#            elif directory_url+"\n" == line:
#                print line 
#                found=True
#            else:
#                print line
#        if not found:
#            with open(GTK_BOOKMARKS_FILE, "a") as myfile:
#                myfile.write(directory_url)

        found=False
        bookmarks_lines = []
        for line in fileinput.input(GTK_BOOKMARKS_FILE):
            if bookmark_replace_string+"\n" == line:
                found=True
                bookmarks_lines.append(directory_url+"\n")
            elif directory_url+"\n" == line:
                found=True
                bookmarks_lines.append(line)
            else:
                bookmarks_lines.append(line)
        if not found:
            bookmarks_lines.append(directory_url+"\n")
        with open(GTK_BOOKMARKS_FILE, "w") as bookmarkfile:
            bookmarkfile.writelines(bookmarks_lines)
                
        #create download and desktop symlink
        self.move_link(DOWNLOAD_DIR,last_fact_directory)
        self.move_link(DESKTOP_DIR,last_fact_directory)
        
        self.change_im_state(last_fact['category'])

    def from_dbus_fact(self, fact):
        '''unpack the struct into a proper dict'''
        return dict(fact=fact[4],
            start_time=dt.datetime.utcfromtimestamp(fact[1]),
            end_time=dt.datetime.utcfromtimestamp(fact[2]) if fact[2] else None,
            description=fact[3],
            activity_id=fact[5],
            category=fact[6],
            tags=fact[7],
            date=dt.datetime.utcfromtimestamp(fact[8]).date(),
            delta=dt.timedelta(days=fact[9] // (24 * 60 * 60),
            seconds=fact[9] % (24 * 60 * 60)),
            id=fact[0])

if __name__ == '__main__':
    # Setup message bus and register signal.
    bus = dbus.SessionBus(mainloop=DBusGMainLoop())
    
    hamster_integration = HamsterIntegration(bus)
    
    # Create and enter the event loop.
    loop = gobject.MainLoop()
    loop.run()
