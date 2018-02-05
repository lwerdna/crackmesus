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

def print_post(post_data, user, depth):
    post = wrapdb.post_to_dictionary(post_data)

#    # post title
#
#    if post['title']:
#        print '''
#        <div class="post_title">%s</div>
#        ''' % post['title']
  
    depth_px = 32*depth
 
    # post stats
    status_class = 'post_stats'
    status_description = 'Comment by '
    if post['type'] == common.POST_TYPE_SOLUTION:
        status_description = '<b style="color:green">Solution Attempt</b> by '
    elif post['type'] == common.POST_TYPE_CRACKME:
        status_description = '<b>Crackme <i>%s</i></b> by ' % post['title']

    print ('<div class="%s" style="margin-left:%dpx">\n' + \
          '  %s <a href=user.py?user=%s><b>%s</b></a> | %s ago') \
            % (status_class, depth_px, status_description, post['author'], \
                post['author'], common.long_ago_str(post['date_posted'])),

    if post['date_edited']:
        print '| Last Edited: %s ago' % common.long_ago_str(post['date_edited']),

    print '| Votes: ',
    common.vote_display(post['id'], post['score'], post['num_votes'], here);

    print '\n</div> <!--/post_stats-->'

    # post body
    body = post['content']
    body = re.sub("\n", "<br>\n", body)
    #body = body.replace("\n", "<br>\n");

    style = "margin-left:%dpx" % depth_px
    if post['type'] == common.POST_TYPE_CRACKME:
        style += "; font-family:monospace"

    print ('<div class="post_body" style="%s">\n' + \
            '%s\n' + \
          '</div> <!--/post_body-->\n') % (style, body)

    # post footer
    print ('<div class="post_footer" style="margin-left:%dpx">\n') % depth_px;

    if post['attachment']:
        print '(downloaded %d times) ' % post['downloads']
        print '<a href=download.py?id=%s><img src=images/dl1.png></a>\n' \
                % post['attachment'],

    print '  <a href=read.py?id=%d><img src=images/reply0.png></a>\n' % post['id']

    # post edit, delete?
    if user and (post['author']==user or user[0]=='@'):
        print '  <a href=post.py?op=pep&id=%d&r=%s><img src=images/ed0.png></a>' % \
                    (post['id'], base64.b64encode(here))
        print '  <a href=post.py?op=dp&id=%d><img src=images/rm0.png></a>' % post['id']

    print '</div> <!--/post_footer-->\n'


def print_posts_recursive(id_, user, depth=0):
    post_data = wrapdb.posts_get(id_)
    print_post(post_data, user, depth)
    print '<br>\n'

    # for every child, print at a deeper depth
    reply_ids = wrapdb.posts_get_replies_ids(id_)

    if len(post_data):
        for reply_id in reply_ids:
            print_posts_recursive(reply_id[0], user, depth+1);

# main()
#
creds = common.check_logged_in()

here = 'read.py?' + os.environ['QUERY_STRING']

page = common.PageLayout(here, creds)
page.startPage()

wrapdb.connect()

# switch on op
fs = cgi.FieldStorage()

try:
    if not 'id' in fs:
        raise Exception('ERROR: missing post id from form data')

    print '<br>'

    id_ = fs['id'].value

    post = wrapdb.post_to_dictionary(wrapdb.posts_get(id_))
    if post['parent']:
        print '<p>You are deep within a crackme\'s conversation. Optionally, \
                <u><a href=read.py?id=%d>go up one level</a></u>!</p>' % post['parent']
        print '<br>'

    user = creds[0] if creds else ''
    print_posts_recursive(id_, user)

    print '<br>'

    # give user chance to reply
    if user:
        common.form({  'action':'post.py',
                'hidden_op':'post_comment',
                'hidden_id':id_,
                'hidden_backpage': here,
                'form_title':'Post Reply',
                'post_type':1,
                'content':'',
                'attachment':1,
                'button_name':'Reply'
            });
    else:
        print '<p><a href=login.py?r=%s><u>Login</u></a> to reply!</p>' % base64.b64encode(here)

except Exception, e:
    print e
    

# cleanup
wrapdb.disconnect()

page.endPage()
