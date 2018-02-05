#!/usr/bin/python

import os
import re
import random
import hashlib
import common

import cgi

import wrapdb

if ('HTTP_HOST' in os.environ) and (os.environ['HTTP_HOST'] == 'localhost'):
    import cgitb
    cgitb.enable()

# 2049-bit prime
#p = 395872389572038572039857239857203857203985230895723958723078952357892 \
#    350789235902384293499827698724987129381908209810910928975757726524324 \
#    539290784894769673653447859493475785898953883577235982837463555434545 \
#    353646636243234908098102984757571098209198283838921098287750918282832 \
#    222222223812831029172057157571283129299181827456554142444256362626262 \
#    655448888888888888888883294723598723999191982819892819828198288477775 \
#    747363133731333731337313373133731337313337999999999999999999999999999 \
#    999999999999999923423423423423523523987198198349813759834872834729838 \
#    48388837438292383427839423983874382938473828737737777232331341117
p = 39587238957203857203985723985720385720398523089572395872307895235789235078923590238429349982769872498712938190820981091092897575772652432453929078489476967365344785949347578589895388357723598283746355543454535364663624323490809810298475757109820919828383892109828775091828283222222222381283102917205715757128312929918182745655414244425636262626265544888888888888888888329472359872399919198281989281982819828847777574736313373133373133731337313373133731333799999999999999999999999999999999999999999992342342342342352352398719819834981375983487283472983848388837438292383427839423983874382938473828737737777232331341117

def display_application(pow_str):
    match = re.match('^\[(.*),(.*)\]:(.*)$', pow_str)
    if not match:
        raise Exception('ERROR: (internal) malformed proof of work string')
    
    window_start = int(match.group(1))
    window_end = int(match.group(2))
    window_value = int(match.group(3))

    # echo it to user
    html = '' + \
        '<pre style=\'background-color:#E0E0C0\'>Calculate e, such that:\n\n' + \
        '65537^e (mod p)\n\n' + \
        'has bits [%d..%d] set to %d\n\n' + \
        'where:\n\n' + \
        'p = 395872389572038572039857239857203857203985230895723958723078952357892\n' + \
        '    350789235902384293499827698724987129381908209810910928975757726524324\n' + \
        '    539290784894769673653447859493475785898953883577235982837463555434545\n' + \
        '    353646636243234908098102984757571098209198283838921098287750918282832\n' + \
        '    222222223812831029172057157571283129299181827456554142444256362626262\n' + \
        '    655448888888888888888883294723598723999191982819892819828198288477775\n' + \
        '    747363133731333731337313373133731337313337999999999999999999999999999\n' + \
        '    999999999999999923423423423423523523987198198349813759834872834729838\n' + \
        '    48388837438292383427839423983874382938473828737737777232331341117\n\n' + \
        'This is intended to require you to brute force search by trial exponentiation\n' + \
        'of successive values e. We, however, can efficiently raise 65537 by your e to\n' + \
        'verify the result.</p>\n' + \
        '</pre>\n'
    print html % (window_start, window_end, window_value)

# main()
#
page = common.PageLayout('index.py')

# switch on op
#
form = cgi.FieldStorage()
op = ''
if 'op' in form:
    op = form['op'].value

# op is nothing, just visiting the page
#
if op == '':
    page.startPage()

    print '<br>'

    common.form({'action':'apply.py', \
                    'form_title':'Apply For Account', \
                    'hidden_op':'apply', \
                    'button_name':'Apply', \
                    'name':1, \
                    'pw0':1, \
                    'pw1':1 \
                });

    print '<br>'

    common.form({'action':'apply.py', \
                    'form_title':'Retrieve Application', \
                    'hidden_op':'retrieve', \
                    'button_name':'Retrieve', \
                    'name':1, \
                    'pass':1, \
                });
    
    print '<br>'

    common.form({'action':'apply.py', \
                    'form_title':'Activate Account', \
                    'hidden_op':'activate', \
                    'button_name':'Activate', \
                    'name':1, \
                    'pass':1, \
                    'pow':1, \
                });

# javascript asking us if a given name is available
#
elif op == 'check_availability':
    page.startPage()
    wrapdb.connect()

    try:
        if 'name' not in form:
            raise Exception('ERROR: name not in form data')

        name = form['name'].value

        common.doublecheck_new_user(name)

        if not wrapdb.user_get_status(name):
            print 'available',
        else:
            print 'unavailable',

    except Exception, e:
        print e

    wrapdb.disconnect()

elif op == 'apply':
    wrapdb.connect()

    try:
        # verify that name, pw0, pw1 were even given
        if 'name' not in form or 'pw0' not in form or 'pw1' not in form:
            raise Exception('ERROR: name and/or password(s) not in form data')
        
        name = form['name'].value
        pw0 = form['pw0'].value
        pw1 = form['pw1'].value

        common.doublecheck_new_user(name)

        if pw0 != pw1:
            raise Exception('ERROR: passwords don\'t match!')

        status = wrapdb.user_get_status(name)

        if status == common.USER_STATUS_RESERVED:
            raise Exception('ERROR: user \'%s\' is reserved; if this is you, contact a mod' % name)

        if status != common.USER_STATUS_NONEXISTENT:
            raise Exception('ERROR: user \'%s\' already exists' % name)
        
        # generate work
        window_bits = 16
        p_bits = 2049

        # generate target window start: [p_bits-1 ... window_bits-1]
        random.seed()
        window_start = random.randrange(window_bits-1, p_bits, 1);
        window_end = window_start - window_bits + 1;

        # generate target value 
        window_value = random.getrandbits(window_bits);
        
        # final proof of work
        pow_string = '[%d,%d]:%d' % (window_start, window_end, window_value)

        # hash password
        sha1 = hashlib.sha1(pw0).hexdigest();

        # insert this info in the database
        wrapdb.user_apply(name, pow_string, sha1)

        # echo it to user
#        html = '' + \
#            '<h2>Application Accepted</h2>\n' + \
#            '<p>%s, for your account to be activated, you must peform a ' + \
#            '<a href=http://en.wikipedia.org/wiki/Proof-of-work_system>' + \
#            'proof-of-work</a>:</p>\n'

        # for now, activation is free
        wrapdb.user_activate(name)

        page.redir = 'login.py'
        page.startPage()
        page.redirNotice('Account %s Activated' % name)

#        display_application(pow_string);
#
#        print '<p>When you are done, return to the <a href=apply.py> \
#                    application page</a> to submit your work.</p>'

    except Exception, e:
        page.startPage()
        common.notice(str(e))

    wrapdb.disconnect()

elif op == 'retrieve':
    wrapdb.connect()

    try:
        # verify that name, pw0, pw1 were even given
        if 'name' not in form or 'pass' not in form:
            raise Exception('ERROR: name and/or password(s) not in form data')

        name = form['name'].value
        password = form['pass'].value
        
        if not wrapdb.user_check_creds(name, hashlib.sha1(password).hexdigest()):
            raise Exception('ERROR: user/pass is not valid or application expired');

        if wrapdb.user_get_status(name) != common.USER_STATUS_APPLIED:
            raise Exception('ERROR: user is not in application state (already activated?)');
      
        # example challenge is like: [794,762]:7386481
        pow_string = wrapdb.user_get_pow(name);

        if not pow_string:
            raise Exception('ERROR: returned challenge in invalid, wtf?');

        # echo it to user
        print '<h2>Application Retrieved</h2>\n'
        display_application(pow_string);
 
        display_application

    except Exception, e:
        print e

    wrapdb.disconnect()

elif op == 'activate':
    page.startPage()
    wrapdb.connect()

    try:
        # verify that name, pass were even given
        if 'name' not in form or 'pass' not in form or 'pow' not in form:
            raise Exception('ERROR: name and/or password(s) not in form data')
        
        name = form['name'].value
        password = form['pass'].value
        proof = form['pow'].value

        if not wrapdb.user_check_creds(name, hashlib.sha1(password).hexdigest()):
            raise Exception('ERROR: user/pass is not valid or application expired');

        if wrapdb.user_get_status(name) != common.USER_STATUS_APPLIED:
            raise Exception('ERROR: user is non-existent, application expired, or not in application state');
      
        # example challenge is like: [794,762]:738648a1
        challenge = wrapdb.user_get_pow(name)

        if not challenge:
            raise Exception('ERROR: returned challenge in invalid, wtf?');

        match = re.match('^\[(.*),(.*)\]:(.*)$', challenge)
        start = int(match.group(1))
        end = int(match.group(2))
        target = int(match.group(3))
        exp = int(proof)
        result = pow(65537, exp, p)
        mask = (pow(2, start-end+1)-1) << end
        result = (result & mask) >> end

        if result != target:
            print "Your proof of work is incorrect. Retrieve your applicatoin and re-check your work.";
        else:
            wrapdb.user_activate(name);
            print "<p>Your proof of work is accepted; account activated.<p>\n";
            print "<p>You may now <a href=login.py>login</a> or return to the <a href=index.py> \
                    top level</a> page<p>\n";

        # generate work
        window_bits = 32
        p_bits = 2049
    except Exception, e:
        print e 
    
    wrapdb.disconnect()

else:
    print 'unknown op: %s' % op

page.endPage()
