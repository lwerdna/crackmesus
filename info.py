#!/usr/bin/python

import os
import re
import cgi
import string
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

    fileName = fs['f'].value

    readme = None
    imageNames = []

    # switch on extension
    if re.match(r'.*\.zip$', fileName):
        
        zfObj = zipfile.ZipFile('./f/%s' % fileName, 'r')

        for name in zfObj.namelist():
            if string.lower(name) == 'readme.txt':
                readme = zfObj.read(name)
            elif re.match(r'.*\.jpg', name):
                imageNames.append(name)
            elif re.match(r'.*\.jpeg', name):
                imageNames.append(name)
            elif re.match(r'.*\.gif', name):
                imageNames.append(name)
            elif re.match(r'.*\.png', name):
                imageNames.append(name)

        zfObj.close()

    print 'Content-Type: text/html\x0d\x0a\x0d\x0a',
    print '<html>'
    print ' <head>'
    print '  <link rel="stylesheet" href="stylesheet.css" type="text/css" />'
	
    if imageNames:
	print '  <link rel="image_src" href="http://crackmes.us/image.py?f=%s&i=%s" />' % (fileName, imageNames[0])

    print ' </head>'
    print ' <body>'
    print '  <div class="main_container">'
    print '   <center>'

    for imageName in imageNames:
        print '     <img src="./image.py?f=%s&i=%s" /><br>' % (fileName, imageName)

    print '   </center>'
    print '   <pre>'

    print cgi.escape(readme)

    print '   </pre>'
    print '  </div>'
    print ' </body>'
    print '</html>'
 
except:
    print 'Content-Type: text/html\x0d\x0a\x0d\x0a',
    print sys.exc_info()[0]
