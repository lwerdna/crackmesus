#!/usr/bin/python

import os
import re
import random
import hashlib
import time

import Cookie

import common
import wrapdb

import cgi
if ('HTTP_HOST' in os.environ) and (os.environ['HTTP_HOST'] == 'localhost'):
    import cgitb
    cgitb.enable()

page = common.PageLayout()
page.backPage = 'faq.py'
page.startPage()

print '''
    <h2>What's Crackmes.us? What's a crackme?</h2>
    <p>Crackmes.us is an enthusiast site for crackmes. See
        <a href=http://en.wikipedia.org/wiki/Crackme>Wikipedia's crackme page</a> for an explanation.</p>

    <h2>What's Crackmes.us purpose in relation to Crackmes.de?</h2>
    <p>
        During the great dark downtime of crackmes.de during mid 2011, Crackmes.us was made
        to provide a temporary substitute. Once crackmes.de returns, it will hopefully provide
        an alternative.
    </p>

    <p>
        It's also an experiment in a new type of model for a crackmes website. Instead of explicitly
        named moderators who control the publication of crackmes and solutions, the community itself
        acts as the moderators by voting.
    </p>

    <h2>How does Crackmes.us work? What are the details of the model?</h2>
    <p>
        The main content is essentially a forum. The forum can contain several types of posts:
        crackmes, solutions, and comments. Every post can be voted on and have file attachments.
    <p>

    <p>
        The root of every discussion thread (or equivalently every topic) must be of type crackme
        and contain an attachment. Below this can exist comments and solutions. The front page
        just shows a list of crackmes. Discussion can be entered by descending into one of the
        discussion thread links.
    <p>

    <p>
        A post of type solution can be made under a crackme. The author of the crackme post can
        ultimately approve or disapprove a solution with his/her vote. If the author is not present,
        a vote score threshold must be met by other members before the solution is accepted. Ties
        are broken byte post date: earliest post becomes the solution. Accepted solutions appear 
        in the solver property of a crackme on its front page.
    </p>

    <h2>How active is the site?</h2>

    <p>The following data is real-time up-to-date:</p>
'''

try:
    now = int(time.time())
    mo_ago = now - 2592000

    wrapdb.connect()
    num_users = wrapdb.stat_get_num_users()
    num_users_active = wrapdb.stat_get_num_users_login_since(mo_ago)
    num_crackmes = wrapdb.stat_get_num_crackmes()
    num_crackmes_good = wrapdb.stat_get_num_crackmes_good()
    wrapdb.disconnect()

    print '<p>There are %d total users registered. Of those, %d have logged in within the last \
            month. There are %d crackmes, of which %d have a positive non-zero vote score.</p>' \
            % (num_users, num_users_active, num_crackmes, num_crackmes_good)
    
except Exception, e:
    print '(error retrieving statistics) + %s' % e


print '''
    <h2>Who's responsible for Crackmes.us?</h2>
    <p>
        Crackmes.us is dead, unless the mighty Tamaroth revives it!
    </p>

    <h2>Where can I contact people about the site?</h2>
    <p>
        Meet us on channel #crackmesde (sic) on IRC dalnet.
    </p>
'''

page.endPage()
