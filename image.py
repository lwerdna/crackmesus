#!/usr/bin/python

import os
import re
import cgi
import zipfile

if ('HTTP_HOST' in os.environ) and (os.environ['HTTP_HOST'] == 'localhost'):
    import cgitb
    cgitb.enable()

fs = cgi.FieldStorage()

#------------------------------------------------------------------------------
# main()
#------------------------------------------------------------------------------
try:
    if not 'f' in fs:
        raise Exception('ERROR: file name in form data')
    if not 'i' in fs:
        raise Exception('ERROR: image name in form data')

    fileName = fs['f'].value
    imageName = fs['i'].value

    data = None

    # switch on extension
    if re.match(r'.*\.zip$', fileName):
        zfObj = zipfile.ZipFile('./f/%s' % fileName, 'r')
        if not (imageName in zfObj.namelist()):
            raise "file %s not present in %s" % (imageName, fileName)
        data = zfObj.read(imageName)
        zfObj.close()

    # serve data, if found
    mimeType = None

    if re.match(r'.*\.jpg$', imageName):
        mimeType = 'image/jpeg'
    elif re.match(r'.*\.jpeg$', imageName):
        mimeType = 'image/jpeg'
    elif re.match(r'.*\.png$', imageName):
        mimeType = 'image/png'
    elif re.match(r'.*\.gif$', imageName):
        mimeType = 'image/gif'
    else:
        raise "unknown extension in: %s" % imageName

    # server must save all of our stdout, measure it, then prepend headers 
    # (like Content-Length) and then append us
#    print 'Content-Length: %d\x0d\x0a' % len(data)
    print 'Content-Type: %s\x0d\x0a\x0d\x0a' % mimeType,
    print data

except:
    print 'Content-Type: text/html\x0d\x0a\x0d\x0a',
    print sys.exc_info()[0]
