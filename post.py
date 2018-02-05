#!/usr/bin/python

import re
import random
import hashlib
import datetime
import common

import base64
import Cookie

import wrapdb
from common import *

import cgi
if ('HTTP_HOST' in os.environ) and (os.environ['HTTP_HOST'] == 'localhost'):
    import cgitb
    cgitb.enable()


# given a cgi fileitem, save that attachment in the ./attachments folder
# with randomly generated filename, return the name
def save_attachment(fileitem):
    if not fileitem.file:
        raise Exception("form file item has no file data")

    # check size
    fileitem.file.seek(0, os.SEEK_END);
    if fileitem.file.tell() > 4194304:
        raise Exception("attachment exceeds 4mb limit");
    fileitem.file.seek(0, os.SEEK_SET);

    # split, text extension
    base, ext = os.path.splitext(fileitem.filename)

    if (ext != '.zip') and (ext != '.gz') and (ext != '.rar'):
        raise Exception("attachment required to be .zip, .gz, or .rar");

    # generate destination file
    name = common.gen_file_name(ext)
    pathed = os.path.join('attachments', name)

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


# switch on op
form = cgi.FieldStorage()
op = ''
if 'op' in form:
    op = form['op'].value

backpage = '';
if 'r' in form:
    backpage = base64.b64decode(form['r'].value)

page = common.PageLayout()
    
# main()
creds = check_logged_in()
if not creds:
    page.startPage()
    common.notice('You must be logged in to post.<br>\n \
                    Click to the <a href=login.py>login page</a>\n')

elif op == '':
    page.startPage()
    common.notice('This page is not meant to be invoked alone.\n')

elif op == 'pc':
    page.startPage()
    print '''
    <h3>Guidelines:</h3>
    <ul>
    <li>only zip/gzip/rar attachment allowed</li>
    <li>please do not include your name in crackme title (eg: "Foo's Crackme #1")</li>
    <li>describe precisely what is required of a valid solution</li>
    </ul>
    '''
    common.form({   'action':'post.py', \
                    'hidden_op':'post_crackme', \
                    'hidden_backpage': backpage, \
                    'form_title':"Post Crackme", \
                    'title':'', \
                    'content':'', \
                    'attachment':'' \
                 });

elif op == 'vote_up' or op == 'vote_down':
    page.redir = backpage
    page.startPage()

    try:

        if 'id' not in form:
            raise Exception('ERROR: required field id is not in form data');
        id = form['id'].value
        
        wrapdb.connect()
        if op == 'vote_up':
            wrapdb.post_vote(id, creds[0], "up")
        else:
            wrapdb.post_vote(id, creds[0], "down")

        page.redirNotice('Vote cast!');
    
    except Exception, e:
        print e
        
    wrapdb.disconnect()

elif op == 'post_crackme':
    page.redir = backpage
    page.startPage()

    try:
        required_fields = ['title', 'content', 'attachment']
        for field in required_fields:
            if field not in form:
                raise Exception('ERROR: required field %s is not form data' % field)
        
        title = form['title'].value
        content = form['content'].value
        attachment = form['attachment']
       
        user = creds[0]
        doublecheck_user(user)
        
        file_base = save_attachment(attachment);

        wrapdb.connect()
        attach_id = wrapdb.post_enter_attachment(file_base)
        wrapdb.post_crackme(user, title, cgi.escape(content,1), attach_id)

        page.redirNotice('Crackme Posted!');

    except Exception, e:
        print e

    wrapdb.disconnect()

# [P]ost [E]dit
elif op == 'pe':

    try:
        # get user info
        user = creds[0] if creds else ''
        if not user:
            raise Exception('must log in to edit posts')
        common.doublecheck_user(user)
        isOp = (user[0]=='@')

        # check field presence / get fields
        common.form_assert_fields(form, ['id', 'title', 'content', 'attachment'])
        id_= form['id'].value
        title_ = form['title'].value
        content_ = form['content'].value
        attachment = form['attachment']

        if not isOp and ('author' in form):
            raise Exception('can\' change author without being mod')

        author_ = ''
        if isOp:
            common.form_assert_fields(form, ['author'])
            author_ = form['author'].value
    
        # validate fields
        common.doublecheck_title(title_)
        common.doublecheck_content(content_)

        if author_:
            common.doublecheck_user(author_)

        # get post info
        wrapdb.connect()
        post = wrapdb.post_to_dictionary(wrapdb.posts_get(id_))

        # ensure only mod or author is editing this post
        if (user[0] != '@') and (user != post['author']):
            raise Exception('can only edit your own posts')

        # if no author given, default to post's current author
        if not author_:
            author_ = post['author']

        # attached file
        attach_id = post['attachment']
        if attachment.filename:
            # delete old attachment
            wrapdb.post_delete_attachment(int(post['attachment']))
            # upload new attachment        
            attach_base = save_attachment(attachment)
            # enter new attachment in database
            attach_id = wrapdb.post_enter_attachment(attach_base)

        # finally, edit the post
        wrapdb.post_edit(post['id'], author_, title_, content_, attach_id)
    
        page.redir = backpage
        page.startPage()
        page.redirNotice('Post Edited!')

    except Exception, e:
        page.startPage()
        print e

    wrapdb.disconnect()


# [P]ost [E]dit [P]repare
elif op == 'pep':
    page.startPage()

    try:
        common.form_assert_fields(form, ['id'])
        id_= form['id'].value

        # get post info
        wrapdb.connect()
        post = wrapdb.post_to_dictionary(wrapdb.posts_get(id_))

        # get user info
        user = creds[0] if creds else ''
        doublecheck_user(user)

        if not user:
            raise Exception('must log in to edit posts')
        if (user[0] != '@') and (user != post['author']):
            raise Exception('can only edit your own posts')

        form_options = {  'action': 'post.py',
                            'hidden_op': 'pe',
                            'hidden_id': id_,
                            'hidden_backpage': backpage,
                            'form_title': 'Edit Post',
                            'title': post['title'],
                            'content': post['content'],
                            'attachment': 1,
                            'button_name': 'Edit'
                }

        # mods have ability to change author 
        if user[0] == '@':
            form_options['author'] = post['author']

        print '''
            <h3>Guidelines:</h3>
            <ul>
            <li>choosing an attachment will overwrite previous attachment</li>
            </ul>
        '''

        common.form(form_options)

    except Exception, e:
        print e

    wrapdb.disconnect()

elif op == 'post_comment':
    page.redir = backpage
    page.startPage()

    try:
        required_fields = ['content', 'id', 'post_type']
        for field in required_fields:
            if field not in form:
                raise Exception('ERROR: required field %s is not form data' % field)
       
        id_ = form['id'].value 
        content = form['content'].value
        post_type = form['post_type'].value
        attachment = form['attachment']
       
        user = creds[0]
        doublecheck_user(user)
       
        attached_file = ''
        if attachment.filename:
            attached_file = save_attachment(attachment);

        post_type_code = 0
        if post_type == 'comment':
            post_type_code = POST_TYPE_COMMENT
        elif post_type == 'solution':
            print 'SOLUTION!<br>\n'
            post_type_code = POST_TYPE_SOLUTION
        else:
            raise Exception('ERROR: illegal post type from form: %s' % post_type)

        wrapdb.connect()
        wrapdb.post_comment(id_, user, '', cgi.escape(content,1) , post_type_code, attached_file)

        page.redirNotice('Comment Posted!')

    except Exception, e:
        print e

    wrapdb.disconnect()

elif op == 'dp':
    try:
        common.form_assert_fields(form, ['id'])
        id_ = form['id'].value 
     
        wrapdb.connect()
        post = wrapdb.post_to_dictionary(wrapdb.posts_get(id_))

        user = creds[0]
        doublecheck_user(user)
     
        if (user != post['author']) and (user[0] != '@'):
            raise Exception('you don\'t have the right to delete posts') 

        wrapdb.remove_post(id_)

        # send user along now
        if post['parent']:
            page.redir = 'read.py?id=%s' % post['parent']
        else:
            page.redir = 'index.py'

        page.startPage()
        page.redirNotice('Post deleted! Redirecting to parent post!')

    except Exception, e:
        page.startPage()
        print e

    wrapdb.disconnect()
 

else:
    print 'unknown op: %s' % op


page.endPage()

