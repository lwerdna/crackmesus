#!/usr/bin/python

import os
import re

import wrapdb
from common import *

import cgi

if ('HTTP_HOST' in os.environ) and (os.environ['HTTP_HOST'] == 'localhost'):
    import cgitb
    cgitb.enable()

# main()
#
try:
    form = cgi.FieldStorage()
    id = ''
    if 'id' in form:
        id = form['id'].value
    else:
        raise Exception("Missing download ID");
    
    wrapdb.connect()
    path = wrapdb.posts_get_attachment_path(id);
    if not path:
        raise Exception("Invalid download ID");
    
    size = os.path.getsize(path);
    wrapdb.disconnect()   
 
    print "Content-Type: binary/octet-stream"
    print "Content-Length: %d" % size
    print "Content-Disposition: attachment; filename=%s; size=%d" % (os.path.basename(path), size)
    print ''
    
    fin = open(path, 'rb')
    print fin.read()
    fin.close()

except Exception, e:
    content_type_hdr()
    html_header()
    center_div_start()
    print e
    center_div_end()
    html_footer()
