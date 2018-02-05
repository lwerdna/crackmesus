#!/usr/bin/python

import os
import re
import random
import hashlib
import urllib
import base64

import wrapdb
import common

import cgi
import Cookie

if ('HTTP_HOST' in os.environ) and (os.environ['HTTP_HOST'] == 'localhost'):
    import cgitb
    cgitb.enable()

###############################################################################
# subroutines
###############################################################################

def save_image(fileitem, user_id):
    if not fileitem.file:
        raise Exception("form file item has no file data")

    # check size
    fileitem.file.seek(0, os.SEEK_END);
    if fileitem.file.tell() > 2097152:
        raise Exception("image exceeds 2mb limit");
    fileitem.file.seek(0, os.SEEK_SET);

    # split, text extension
    base, ext = os.path.splitext(fileitem.filename)

    if (ext != '.jpg') and (ext != '.gif') and (ext != '.png'):
        raise Exception("attachment required to be .jpg, .gif, .png");

    # generate destination file
    name = ('user%08d' + ext) % user_id
    pathed = os.path.join('images', name)

    # write destination file
    fout = file(pathed, 'wb')
    while 1:
        chunk = fileitem.file.read(100000)
        if not chunk: 
            break
        fout.write (chunk)
    fout.close()

    # done
    return name

###############################################################################
# main()
###############################################################################
creds = common.check_logged_in()

here = 'user.py'
if 'QUERY_STRING' in os.environ:
    here += '?'
    here += os.environ['QUERY_STRING']
   
page = common.PageLayout(here, creds)

wrapdb.connect()

# switch on op
fs = cgi.FieldStorage()

###############################################################################
# default behavior: display a profile
###############################################################################
if not 'op' in fs:
    try:
        page.startPage()

        if not 'user' in fs:
            raise Exception('ERROR: missing \'user\' from form data')
        user = fs['user'].value
        common.doublecheck_user(user)
 
        # normal user data
        #
        user_row = wrapdb.user_get_user(user)

        if not user_row:
            raise Exception("ERROR: user \'%s\' does not exist" % user) 

        user_data = wrapdb.user_to_dictionary(user_row)
      
    
        # is user viewing his own profile? give option to edit it, then
        if creds and (user == creds[0]):
            print '<br>'
            print '<h1>Account Settings*</h1>'
            print '<div class="content">'
            print '  <p><a href=user.py?op=pe&user=%s>Edit Profile</a></p>' % user
            print '  <p><a href=user.py?op=pcp&user=%s>Change Password</a></p>' % user
            print '</div>'
            print '<div class="footnote">'
            print '  *these options only appear for your account'
            print '</div>'

        print '<br>'
        print '<h1>'
        print '%s\'s Data:' % user
        print '</h1>'
    
        print '<table width=100%%>'
        print '<tr>'
        print '  <td align=left>'
        print '    <textarea style="width:100%%" readonly="readonly" cols=64 rows=16>%s</textarea>' % user_data['profile']
        print '  </td>'
        print '</tr>'
        print '<tr bgcolor=#C0C0C0>'
        print '  <td colspan=2 align=center>'
        print '    <b>Name: </b>%s |' % user_data['name']
        print '    <b>Member Since: </b>%s ago |' % common.long_ago_str(user_data['date'])
        print '    <b>Last Logged In: </b>%s ago |' % common.long_ago_str(user_data['date_login'])
        print '    <b>User Status: </b>%s' % common.user_status_to_string(user_data['status'])
        print '  </td>'
        print '</tr>'
        print '</table>'
    
        print '<br>'
    
        # solution data is a normal post row for the crackme appended with solution score
        #
        solution_data = wrapdb.user_get_solutions_all(user)
    
        crackme_posts = []
        solution_scores = []
    
        for data in solution_data: 
            crackme_posts.append(data[0:-2])
            solution_scores.append([ common.vote_colorize_full(data[-2], data[-1]) ])
    
        if crackme_posts:
            fields = {'display_title':'%s\'s Solutions' % user, \
                'title':1, \
            }
    
            extra_cols = ['Solution Rating'];
    
            common.posts_display(crackme_posts, fields, extra_cols, solution_scores)
        else:
            print '<p>(no solutions yet exist from the user)</p>'    
        
        print '<br>'
    
        # crackmes
        #
        crackmes = wrapdb.user_get_posted_crackmes(user)
      
        if crackmes: 
            fields = {'display_title':'%s\'s Crackmes' % user, \
                    'title':1, \
                    'date_posted':1, \
                    'date_activity':1, \
                    'num_replies':1, \
                    'score':1, \
                    'num_votes':1, \
                    'downloads':1, \
                    'solver':1
                }
            
            common.posts_display(crackmes, fields)
        else:
            print '<p>(no crackmes yet exist from this user)</p>'
    
    except Exception, e:
        common.notice(str(e))

###############################################################################
# edit a profile
###############################################################################
elif fs['op'].value == 'pe':
    try:
        page.startPage()

        if not 'user' in fs:
            raise Exception('ERROR: missing \'user\' from form data')
        user = fs['user'].value

        if not creds:
            raise Exception('ERROR: you must be logged in to edit your profile')

        if creds[0] != user:
            raise Exception('ERROR: you may only edit your own profile')

        user_data = wrapdb.user_to_dictionary(wrapdb.user_get_user(user))
 
        print '''
        <h3>Guidelines:</h3>
        <ul>
        <li>profile text limited to 1024 characters after escapement</li>
        </ul>
        '''
        common.form({   'action':'user.py', \
                        'hidden_op':'e', \
                        'hidden_user':user, \
                        'hidden_backpage': 'user.py?user=%s' % user, \
                        'form_title':"Edit Profile", \
                        'profile':user_data['profile']
                     });

    except Exception, e:
        print e 

elif fs['op'].value == 'e':
    try:

        if not 'user' in fs:
            raise Exception('ERROR: missing \'user\' from form data')
        user = fs['user'].value
        common.doublecheck_user(user)

        if not creds:
            raise Exception('ERROR: you must be logged in to edit your profile')

        if creds[0] != user:
            raise Exception('ERROR: you may only edit your own profile')

        r = ''
        if 'r' in fs:
            backpage = base64.b64decode(fs['r'].value)

        user_data = wrapdb.user_to_dictionary(wrapdb.user_get_user(user))

        profile = fs['profile'].value
        common.doublecheck_content(profile)

        wrapdb.user_update(user, cgi.escape(profile,1))
        
        page.redir = backpage
        page.startPage()
        page.redirNotice('Profile updated!');

    except Exception, e:
        page.redir = ''
        page.startPage()
        print e
        
elif fs['op'].value == 'pcp':

    try:
        if not 'user' in fs:
            raise Exception('ERROR: missing \'user\' from form data')
        user = fs['user'].value
        common.doublecheck_user(user)

        if not creds:
            raise Exception('ERROR: you must be logged in to edit your profile')

        if creds[0] != user:
            raise Exception('ERROR: you may only change your own password')

        r = ''
        if 'r' in fs:
            backpage = base64.b64decode(fs['r'].value)
        
        user_data = wrapdb.user_to_dictionary(wrapdb.user_get_user(user))
    
        page.startPage()

        print '''
        <h3>Notes:</h3>
        <ul>
        <li>sha1 of your new password is stored on server</li>
        <li>logged in state is represented by your browser re-sending name/pass plaintext via cookie</li>
        <li>passwords can be sniffed over HTTP traffic</li>
        <li>current password sha1: %s</li>
        </ul>
        ''' % user_data['pwhash']

        common.form({'action':'user.py', \
                        'hidden_user':user, \
                        'form_title':'Choose New Password', \
                        'hidden_op':'cp', \
                        'button_name':'Change Password', \
                        'pw0':1, \
                        'pw1':1 \
                    });

    except Exception, e:
        page.startPage()
        print e

elif fs['op'].value == 'cp':
    try:
        common.form_assert_fields(fs, ['user', 'pw0', 'pw1'])
        
        user = fs['user'].value
        common.doublecheck_user(user)

        if not creds:
            raise Exception('ERROR: you must be logged in to edit your profile')

        if creds[0] != user:
            raise Exception('ERROR: you may only change your own password')
        
        pw0 = fs['pw0'].value
        pw1 = fs['pw1'].value
        if pw0 != pw1:
            raise Exception('ERROR: the two passwords don\'t match')
        
        wrapdb.user_update_password(user, hashlib.sha1(pw0).hexdigest())
      
        # NOW ALSO SET THE NEW LOGIN COOKIE
        C = Cookie.SimpleCookie();
        C['user'] = user;
        C['pass'] = pw0;
        
        page.cookie = C
        page.redir = 'user.py?user=%s' % user 
        page.startPage()
        page.redirNotice('password changed; new cookie set');

    except Exception, e:
        page.redir = ''
        page.startPage()
        print e


else:
    print '<p>Unknown op: %s</p>' % cgi.escape(fs['op'].value, 1)

# cleanup
wrapdb.disconnect()

page.endPage()
