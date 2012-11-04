#!/usr/bin/python2.7
# encoding: utf-8
'''
hamsterimport -- Hamster import script

import TSV files to hamster as exported with hamster export command

@author:     Sylvain Bannier
        
@license:    license

@contact:    smile.syban@gmail.com
@deffield    updated: 2012-11-03
'''


import datetime as dt
from datetime import date, timedelta
import csv
import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from hamster import client
from hamster.lib import stuff
from mx.DateTime.DateTime import TimeDelta


__all__ = []
__version__ = 0.1
__date__ = '2012-11-03'
__updated__ = '2012-11-03'

DEBUG = 1


class HamsterImport():

    def __init__(self):
        self.storage = client.Storage()
        
    def process_import(self, path):
        with open(path, 'rb') as csvfile:
            csvreader = csv.reader(csvfile, dialect='excel-tab')
            header = False
            updated_times = []
            for row in csvreader:
                utf8row = []
                for col in row:
                    utf8row.append(col.strip().decode('utf-8'))
                (activity,start_time,end_time,duration,category,description,tags) = utf8row
                if header:
                    try:
                        start_time = dt.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                        if start_time not in updated_times:
                            end_time = dt.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                            tags_list = tags.split(',')
                            tags = ''
                            for tag in tags_list:
                                tag = tag.strip()
                                if tag:
                                    tags += ' #'+tag
                            input_line = activity
                            if category:
                                input_line += '@%s'%category
                            if tags or description:
                                input_line += ','
                            if description:
                                input_line += description
                            if tags:
                                input_line += ' '+tags
        
                            facts = self.storage.get_facts(start_time-timedelta(days=1),end_time+timedelta(days=1))
                            fact_found = False
                            if facts:
                                for fact in facts:
                                    if fact.start_time == start_time and fact.end_time == end_time:
                                        print "[UPDATE] [%s - %s] : %s " % (start_time,end_time,input_line)
                                        fact_found = True
                                        self.storage.update_fact(fact.id,stuff.Fact(input_line,
                                                                         start_time = start_time,
                                                                         end_time = end_time))
                            if not fact_found:
                                print "[ADD   ] [%s - %s] : %s " % (start_time,end_time,input_line)
                                self.storage.add_fact(stuff.Fact(input_line,
                                                                 start_time = start_time,
                                                                 end_time = end_time))
                               
                        updated_times.append(start_time)
                    except ValueError:
                        print "[ERROR ] Wrong format for this line : %s\n" % utf8row
                        
                header = True        

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Sylvain Bannier on %s.
  Copyright 2012 Sylvain Bannier. All rights reserved.
  
  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0
  
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument(dest="path", help="path to tsv file to import with header", metavar="path")
        
        # Process arguments
        args = parser.parse_args()
        
        path = args.path
        hamster_csv = HamsterImport()
        hamster_csv.process_import(path)
        
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    sys.exit(main())    
