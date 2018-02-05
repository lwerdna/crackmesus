#!/usr/bin/python

import os
import cgi
import Cookie
import common
import base64

import cgi
if ('HTTP_HOST' in os.environ) and (os.environ['HTTP_HOST'] == 'localhost'):
    import cgitb
    cgitb.enable()

# print a cleared cookie header
C = Cookie.SimpleCookie();
C['user'] = '';
C['pass'] = '';
print str(C)

# see if redir existed in form
form = cgi.FieldStorage()
backpage = 'index.py'
if 'r' in form:
    backpage = base64.b64decode(form['r'].value)

page = common.PageLayout()
page.redir = backpage

page.startPage()
page.redirNotice('Clearing cookies.');
page.endPage()
