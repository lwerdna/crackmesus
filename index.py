#!/usr/bin/python

import os
import re
import random

import wrapdb
import common

import Cookie

import cgi
if ('HTTP_HOST' in os.environ) and (os.environ['HTTP_HOST'] == 'localhost'):
    import cgitb
    cgitb.enable()

page = common.PageLayout('index.py')
page.startPage()

wrapdb.connect()
data = wrapdb.posts_get_latest()

print '<br>'

fields = {'display_title':'Latest Crackmes', \
            'title':1, \
            'author':1, \
            'date_posted':1, \
            'date_activity':1, \
            'num_replies':1, \
            'score':1, \
            'num_votes':1, \
            'downloads':1, \
            'solver':1
        }

common.posts_display(data, fields)

wrapdb.disconnect()
page.endPage()
