import os
import re
import Cookie
import time
import wrapdb
import hashlib
import base64
import random

USER_STATUS_NONEXISTENT = 0
USER_STATUS_APPLIED = 1
USER_STATUS_ACTIVE = 2
USER_STATUS_DISABLED = 3
USER_STATUS_RESERVED = 4

POST_TYPE_CRACKME = 0
POST_TYPE_COMMENT = 1
POST_TYPE_VOTE = 2
POST_TYPE_SOLUTION = 3
POST_TYPE_VOTE_UP = 4
POST_TYPE_VOTE_DOWN = 5

def user_status_to_string(status):
    if status == USER_STATUS_NONEXISTENT:
        return "non-existent"
    if status == USER_STATUS_APPLIED:
        return "applied"
    if status == USER_STATUS_ACTIVE:
        return "active"
    if status == USER_STATUS_DISABLED:
        return "disabled"
    if status == USER_STATUS_RESERVED:
        return "reserved"
    return "unknown"

###############################################################################
# paranoia on user input
###############################################################################
def doublecheck_new_user(name):
    if not re.match('^[a-zA-Z0-9._]+$', name):
        raise Exception('ERROR: illegal characters found in user!')

def doublecheck_user(name):
    if not re.match('^[@a-zA-Z0-9._]+$', name):
        raise Exception('ERROR: invalid characters found in user!')

def doublecheck_pwhash(pwhash):
    if not re.match('^[a-fA-F0-9]+$', pwhash):
        raise Exception('ERROR: non-hex characters found in hash!')

def doublecheck_pow(pow_string):
    # example challenge is like: [794,762]:7386481
    if not re.match('^\[(.*),(.*)\]:(.*)$', pow_string):
        raise Exception('ERROR: malformed proof-of-work string!')

def doublecheck_pass(pw_string):
    if len(pw_string) > 32:
        raise Exception('ERROR: password string is too long!')

def doublecheck_vote(vote):
    if (vote != -1) and (vote != 1):
        raise Exception('ERROR: invalid vote!')

def doublecheck_title(title):
    if len(title) > 64:
        raise Exception('ERROR: posting title is too long (limit: 64) (length checked after HTML escape)')

    m = re.match('[<>]', title)
    if m:
        raise Exception('ERROR: html shit found in title');

#    m = re.match('([^a-zA-Z0-9.!?\s])', title)
#    if m:
#        raise Exception('ERROR: illegal character <p style="color:green"> \
#            %s</p> found in title' % m.group(1));

def doublecheck_content(content):
    if len(content) > 4096:
        raise Exception('ERROR: posting content is too long (limit: 1024) (length checked after HTML escape)')

    m = re.match('[<>]', content)
    if m:
        raise Exception('ERROR: html shit found in content');

#    srch = re.search('[^a-zA-Z0-9.!?\s]', content)
#    if srch:
#        raise Exception('ERROR: illegal character <p style="color:green"> \
#            %s</p> found in content' % srch.group(0));

def doublecheck_attach_base(base):
    if not base:
        return

    if not re.match('^\d\d\d\d\d\d\d\d\.(?:zip|gz|rar)$', base):
        raise Exception('ERROR: illegal attach base: <p style="color:green"> \
            %s</p>' % base)

def doublecheck_attach_path(path):
    if not path:
        return

    if not re.match('^attachments/\d\d\d\d\d\d\d\d\.(?:zip|gz|rar)$', path):
        raise Exception('ERROR: illegal attach path: <p style="color:green"> \
            %s</p>' % path)

def doublecheck_attach_id(id_):
    if type(id_) != type(0):
        raise Exception('ERROR: attach id must be an integer!')

def doublecheck_profile_image_base(path):
    if not path:
        return

    if not re.match('^user\d\d\d\d\d\d\d\d.(?:gif|jpg|png)$', path):
        raise Exception('ERROR: illegal attach path: <p style="color:green"> \
            %s</p>' % path)

def doublecheck_profile_image_path(path):
    if not path:
        return

    if not re.match('^images/user\d\d\d\d\d\d\d\d.(?:gif|jpg|png)$', path):
        raise Exception('ERROR: illegal attach path: <p style="color:green"> \
            %s</p>' % path)

def doublecheck_pwhash(pwhash):
    # 160 bits == 20 bytes == 40 hex chars
    if not re.match('^[a-fA-F0-9]{40,40}$', pwhash):
        raise Exception('ERROR: illegal password hash: %s', pwhash)

###############################################################################
# date stuff
###############################################################################
def long_ago_str(epoch):
    answer = ''
    delta = time.time() - epoch

    if delta < 60:
        answer = '%d sec' % delta
    elif delta < 3600:
        answer = '%d mins' % (delta / 60)
    elif delta < 86400:
        answer = '%d hrs' % (delta / 3600)
    elif delta < 2592000:
        answer = '%d days' % (delta / 86400)
    elif delta < 31536000:
        answer = '%d mos' % (delta / 2592000)
    else:
        answer = '%.1f yrs' % (delta / 31536000.0)

    return answer

###############################################################################
# user session stuff
###############################################################################
def check_logged_in():
    rval = []

    try:
        wrapdb.connect()

        cookie = Cookie.SimpleCookie(os.environ["HTTP_COOKIE"])

        if ('user' in cookie) and ('pass' in cookie):
            user = cookie['user'].value
            password = cookie['pass'].value

            if user and password:
                doublecheck_user(user)
                doublecheck_pass(password)

                if wrapdb.user_check_creds(user, hashlib.sha1(password).hexdigest()):
                    rval = [user, password]

    except (Cookie.CookieError, KeyError):
        rval = []
 
    wrapdb.disconnect()

    return rval

###############################################################################
# common html printing stuff
###############################################################################

class PageLayout:
    def __init__(self, backPage='', creds=[]):
        # URL to return to for bounce back page (login, vote, etc.)
        # unencoded!
        self.backPage = backPage;
        self.redirDelay = 2
        self.doBanner = 1
        self.doMenu = 1
        self.centerDiv = 1
        self.doFooter = 1
        self.cookie = None
        # URL to specify redirect to when htmlHeader() is written
        self.redir = ''
        if creds:
            self.creds = creds
        else:
            self.creds = check_logged_in()

    def contentTypeHeader(self):
        if self.cookie:
            print str(self.cookie)
        print "Content-Type: text/html\x0d\x0a\x0d\x0a",

    def htmlHeader(self, extra_head=''):
        print '<html>'
        print '  <head>'
        print '    <link href="stylesheet.css" rel="stylesheet" type="text/css">'
        print      '%s' % extra_head
        print '  </head>'
        print '  <body>'

    def footer(self):
        try:

            wrapdb.connect()
            print '    <hr>'
            print '    <div style="text-align: right; font-size: small">'
        
            mods = ', '.join(wrapdb.stat_get_moderators())
            print '    Moderators: %s<br>' % mods
            print '    Crackmes.us is devoid of adverts and JS<br>'
            print '    &copy; 2011 whatever'

        except Exception, e:
            print '<p>ERROR accessing moderators</p>'

    def htmlFooter(self):
        print '  </body>'
        print '</html>'
    
    def centerDivStart(self):
        print '<div class="center_pane">'
    
    def centerDivEnd(self):
        print '</div> <!--/center_pane-->'

    # top floating menu thing
    def banner(opts={}):
        print '<div class="top_menu">'
        print '<a href=index.py><img style="margin:2px" src=images/logo.png></a>'
        print '</div>'

    def menu(self):
        print '<div class="top_menu2">'
    
        print '&nbsp;<a href=index.py>Latest</a>'

        encoded = base64.b64encode(self.backPage);

        if self.creds:
            #print '%s ' % creds[0]
            print ' | <a href=post.py?op=pc&r=%s>Post Crackme</a>' \
                    % encoded
            print ' | <a href=user.py?user=%s>Account</a>' \
                    % self.creds[0]
            print ' | <a href=logout.py?r=%s>Log out</a>' \
                    % encoded
        else:
            print ' | <a href=apply.py>Apply</a> '
            print ' | <a href=login.py?r=%s>Login</a>' % encoded

        print ' | <a href=faq.py>FAQ</a>'

        print '</div>\n'

    def redirNotice(self, msg):
        notice('%s <a href=%s><u>Redirecting</u></a> in %d seconds...' \
                % (msg, self.redir, self.redirDelay))

    def startPage(self):
        # content type
        self.contentTypeHeader()

        # html header (including head where meta resides)
        meta_redir = ''
        if self.redir:
            meta_redir = '<meta HTTP-EQUIV="REFRESH" content="2; url=%s">' \
                            % self.redir
 
        self.htmlHeader(meta_redir);

        # banner?
        if self.doBanner:
            self.banner()

        # menu?
        if self.doMenu:
            self.menu()

        # center div
        if self.centerDiv:
            self.centerDivStart()

    def endPage(self):
        # end center div
        if self.centerDiv:
            self.centerDivEnd()

        if self.doFooter:
            self.footer()

        self.htmlFooter() 

def vote_colorize(score_):
    if score_ > 0:
        return '<b><font color=green>+%d</font></b>' % (score_)
    elif score_ < 0:
        return '<b><font color=red>%d</font></b>' % (score_)
    else:
        return '0'

def vote_colorize_full(score, num_votes):
    return vote_colorize(score) + ('/%d' % num_votes)

def vote_display(id_, score_, num_votes_, backpage=''):
    print vote_colorize(score_)

    encoded = base64.b64encode(backpage)

    print ('<a style="color:green" target="_blank" href=post.py?op=vote_up&id=%d&r=%s>&uArr;</a>' + 
            '<a style="color:red" target="_blank" href=post.py?op=vote_down&id=%d&r=%s>&dArr;</a>') \
                 % (id_, encoded, id_, encoded),

def notice(msg):
    print '<br>'
    print '<div class="heading" style="text-align: center">Notice</div>'
    print '<div class="content">%s</div>' % msg

def form(fields):
    if 'action' not in fields:
        raise Exception('ERROR: form action required');

    if 'form_title' not in fields:
        raise Exception('ERROR: form title required');

    print '<div class="heading">'
    print '  %s' % fields['form_title']
    print '</div>'
    print '<div class="content">' 
    print '<form action=%s method=post enctype="multipart/form-data">' % fields['action']

    # the hidden junk
    #
    if 'hidden_op' in fields:
        print '<input type=hidden name=op value=%s>' % fields['hidden_op']

    if 'hidden_id' in fields:
        print '<input type=hidden name=id value=%s>' % fields['hidden_id']

    if 'hidden_backpage' in fields:
        print '<input type=hidden name=r value=%s>' % base64.b64encode(fields['hidden_backpage'])

    if 'hidden_user' in fields:
        print '<input type=hidden name=user value=%s>' % fields['hidden_user']

    # normal junk
    #
    if 'name' in fields:
        print '<label>Name:</label>'
        print '<input type=text name=name><br>'

    if 'pass' in fields:
        print '<label>Password:</label>'
        print '<input type=password name=pass><br>'

    if 'pw0' in fields:
        print '<label>Password:</label>'
        print '<input type=password name=pw0><br>'

    if 'pw1' in fields:
        print '<label>Verify:</label>'
        print '<input type=password name=pw1><br>'

    if 'pow' in fields:
        print '<label>Proof of Work:</label>'
        print '<input type=text name=pow><br>'

    if 'author' in fields:
        print '<label>Author:</label>'
        print '<textarea cols=64 rows=1 name=author>%s</textarea><br>' % fields['author']

    if 'title' in fields:
        print '<label>Title:</label>'
        print '<textarea cols=64 rows=1 name=title>%s</textarea><br>' % fields['title']
    
    if 'content' in fields:
        print '<label>Content:</label>'
        print '<textarea cols=64 rows=16 name=content>%s</textarea><br>' % fields['content']

    if 'attachment' in fields:
        print '<label>Attachment:</label>'
        print '<input type=file name=attachment /><br>'

    if 'profile' in fields:
        print '<label>Profile:</label>'
        print '<textarea cols=64 rows=16 name=profile>%s</textarea><br>' % fields['profile']

    if 'image' in fields:
        print '<label>Image:</label>'
        print '<input type=file name=image /><br>'

    if 'post_type' in fields:
        print '<label>Post Type:</label>'
        print '''
        <select name=post_type>
          <option value="comment">Comment</option>
          <option value="solution">Solution</option>
        </select><br>
        '''

    print '<hr>'
    button_name = 'Post'
    if 'button_name' in fields:
        button_name = fields['button_name']

    print '<input type=submit value=%s />' % button_name

    print '</form>'
    print '</div>'

def posts_display(posts, fields, extra_cols=[], extra_rows=[]):
    # title heading of list of posts 
    display_title = 'Posts'
    if 'display_title' in fields:
        display_title = fields['display_title']
    print '<h1>%s</h1>' % display_title

    # table column headings
    print '<table width=100%>'
    print '<tr>'
    if 'title' in fields:
        print '  <th>title</th>'
    if 'author' in fields:
        print '  <th>author</th>'
    if 'date_posted' in fields:
        print '  <th>posted</th>'
    if 'date_activity' in fields:
        print '  <th>activity</th>'
    if 'num_replies' in fields:
        print '  <th>replies</th>'
    if 'num_votes' in fields:
        print '  <th>vote</th>'
    if 'downloads' in fields:
        print '  <th>dls</th>'
    if 'solver' in fields:
        print '  <th>solver</th>'

    for col in extra_cols:
        print '  <th>%s</th>' % col

    print '</tr>'

    row_color = ['#F1F1EA', '']

    # for every post
    for row_i, row in enumerate(posts):
        post = wrapdb.post_to_dictionary(row)

        print '<tr style="background-color: %s">' % row_color[row_i%2]
    
        if 'title' in fields:
            print '  <td>'
            #print '    <a href=read.py?id=%d><img src=images/chat1.png></a>' % post['id']
            #print '    <a href=download.py?id=%s><img src=images/dl1.png></a>' % post['attachment']
            print '    <a href=read.py?id=%d>%s</a>' % (post['id'], post['title'])
            print '  </td>'
        if 'author' in fields:
            print '  <td>'
#            print '    <a href=user.py?user=%s><img src=images/prof0.png></a> %s' % \
#                        (post['author'], post['author'])
            print '    <a href=user.py?user=%s>%s</a>' % (post['author'], post['author'])
            print '  </td>'
        if 'date_posted' in fields:
            print '  <td>%s ago</td>' % long_ago_str(post['date_posted'])
        if 'date_activity' in fields:
            print '  <td>%s ago</td>' % long_ago_str(post['date_activity'])
        if 'num_replies' in fields:
            print '  <td>%s</td>' % post['num_replies']
        if 'score' in fields:
            print '  <td>'
            if post['score'] > 0:
                print '<b><font color=green>+%d</font></b>/%d' % (post['score'], post['num_votes'])
            elif post['score'] < 0:
                print '<b><font color=red>%d</font></b>/%d' % (post['score'], post['num_votes'])
            else:
                print '0/%d' % post['num_votes']
            print '  </td>'
        if 'downloads' in fields:
            print '  <td>%s</td>' % post['downloads']
        if 'solver' in fields: 
            print '  <td>%s</td>' % post['solver'] 

        for j in range(len(extra_cols)):
            print '  <td>%s</td>' % extra_rows[row_i][j]
    
        print '</tr>'

    print '</table>'

###############################################################################
# random shiz
###############################################################################

def gen_file_name(ext):
    name = ''

    random.seed()

    while 1:
        for i in range(8):
            name += ('%d' % random.randrange(0,10))

        name += ext

        if not os.path.exists('attachments/' + name):
            break

    return name

def form_assert_fields(form, field_list):
    for field in field_list:
        if field not in form:
            raise Exception('ERROR: missing \'%s\' from form data' % field)

