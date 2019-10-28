#!/usr/bin/python
from __future__ import absolute_import
import sys, getopt, json, os, argparse

from pladmin.database import Database 
from pladmin.files import Files

# parser.add_argument('integers', metavar='N', type=int, nargs='+', default=max, help='an integer for the accumulator')
# parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max, help='sum the integers (default: find the max)')




def main():
    files = Files()
    db = Database()

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('action', metavar='action', type=str, help='Push the method name')

    args = parser.parse_args()
    action = args.action
    
    # Update schema command
    if action == 'updateSchema':
        update = db.updateSchema()
        print(update)

        #TODO List file removed and drop it from database


    # Create schema command
    if action == 'createSchema':
        invalids = db.createSchema()
        
        if len(invalids):
            print(invalids)
        else:
            print('Schema created successfully!')


    if action == 'compileInvalids':
        # Get invalid objects
        invalids = db.getObjects(status='INVALID')

        # Try to compile it 
        db.compileObj(invalids)

        result = db.getObjects(status='INVALID')
        print(result)

    # print(args.action)
    # files.localChanges()
    # files.remoteChanges()



if __name__ == '__main__':
    sys.exit(main())