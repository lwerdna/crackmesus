#!/usr/bin/python

import os
import re
import random
import hashlib
import datetime
import base64

import Cookie

import common
import wrapdb

import cgi
if ('HTTP_HOST' in os.environ) and (os.environ['HTTP_HOST'] == 'localhost'):
    import cgitb
    cgitb.enable()

# main()
# switch on op
form = cgi.FieldStorage()
op = ''
if 'op' in form:
    op = form['op'].value

backpage = 'index.py'
if 'r' in form:
    backpage = base64.b64decode(form['r'].value)

page = common.PageLayout()

# op is nothing, just visiting the page
#
if op == '':
    page.startPage()

    print '<br>'

    common.form({'form_title' : 'Login: ', \
            'action' : 'login.py', \
            'hidden_op' : 'login', \
            'name' : 1, \
            'pass' : 1, \
            'button_name' : 'Login', \
            'hidden_backpage' : backpage \
            });


# op is logging in
#
elif op == 'login':
    wrapdb.connect()
    
    try:
        # verify that name, pass
        if 'name' not in form or 'pass' not in form:
            raise Exception('ERROR: name and/or password(s) not in form data')
        
        name = form['name'].value
        password = form['pass'].value

        common.doublecheck_user(name)
    
        if wrapdb.user_get_status(name) != common.USER_STATUS_ACTIVE:
            raise Exception('ERROR: user %s non-existent or inactive' % name)
     
        if not wrapdb.user_check_creds(name, hashlib.sha1(password).hexdigest()):
            raise Exception('ERROR: invalid user/pass entered')

        wrapdb.user_login(name)

        # set login cookie
        C = Cookie.SimpleCookie();
        C['user'] = name;
        C['pass'] = password;
        page.cookie = C
        # set redirect
        page.redir = backpage
        
        # start page
        page.startPage()       
 
        notice = ''
        notice += "<p>You've logged in.</p>\n"
        notice += "<p>Currently this means that a cookie with the following HTTP headers \
                was sent to you. Your browser will repeat it back on subsequent visits \
                until the cookie expires. Hopefully later this will be wrapped in SSL.</p>"
        notice += "<pre>\n" + str(C) + "</pre>\n"
        
        page.redirNotice(notice)
        
    except Exception, e:
        page.startPage()
        print e

    wrapdb.disconnect()

else:
    print 'unknown op: %s' % op

page.endPage()
