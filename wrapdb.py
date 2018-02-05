#!/usr/bin/python

import os
import re
import sqlite3
import time
import common
import traceback

###############################################################################
# globals
###############################################################################
g_connection = 0
g_cursor = 0

###############################################################################
# connect/disconnect
###############################################################################
def connect():
    global g_connection
    global g_cursor

    if not g_connection:
        g_connection = sqlite3.connect('crackmes.db')
        g_cursor = g_connection.cursor()
    else:
        print '<p>warning: double database connect</p>\n'

def disconnect():
    global g_connection
    global g_cursor

    if g_cursor:
        g_cursor.close()
        g_cursor = 0

        g_connection.commit()
        g_connection.close()
        g_connection = 0


###############################################################################
# user related db retrieval functions
###############################################################################
def user_get_status(name):
    common.doublecheck_user(name);

    global g_cursor
    g_cursor.execute("select status from users where name=? COLLATE NOCASE;", (name,));
    result = g_cursor.fetchall()

    if not result:
        return common.USER_STATUS_NONEXISTENT

    # result = [(0,), (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,)]
    # result[0] is first row, result[1] is second row, etc...
    return result[0][0]

def user_apply(name, work, pwhash):
    common.doublecheck_new_user(name)

    now = int(time.time())

    global g_cursor
    g_cursor.execute("insert into users(id, name, status, profile, date, extra, pwhash, date_login, image) \
        values(null,?,?,?,?,?,?,?,?)", \
        (name, common.USER_STATUS_APPLIED, 'profile', now, work, pwhash, now, 'user99999999.jpg'))

def user_check_creds(name, pwhash):
    common.doublecheck_user(name)
    common.doublecheck_pwhash(pwhash)
    
    global g_cursor
    g_cursor.execute("select extra from users where name=? and pwhash=?", (name, pwhash));
 
    if not g_cursor.fetchall():
        return False

    return True

def user_get_pow(name):
    common.doublecheck_new_user(name)

    global g_cursor
    g_cursor.execute("select extra from users where name=? COLLATE NOCASE", (name,));
    result = g_cursor.fetchall()

    return result[0][0]

def user_activate(name):
    common.doublecheck_new_user(name)
    
    global g_cursor
    g_cursor.execute("update users set status=? where name=? COLLATE NOCASE;", \
        (common.USER_STATUS_ACTIVE, name,))

def user_login(name):
    common.doublecheck_user(name)

    global g_cursor
    g_cursor.execute("update users set date_login=? where name=?;", \
        (int(time.time()), name,))

def userstate_is_logged_in():
    return True

###############################################################################
# convenience things
###############################################################################
  
def get_root_post(id_):
    global g_cursor

    curr = id_
    while 1:
        g_cursor.execute('select parent from posts where id=?', id_)
        parent = g_cursor.fetchone()[0] 

        # no parent? then this is root
        if parent==0:
            return curr

        # otherwise, ascend
        curr = parent
 
def recalculate_votes_score(id_):
    global g_cursor

    # get ups
    g_cursor.execute('select count(id) from posts where parent=? and type=?', \
                        (id_, common.POST_TYPE_VOTE_UP,))
    ups = g_cursor.fetchone()[0]

    # get downs
    g_cursor.execute('select count(id) from posts where parent=? and type=?', \
                        (id_, common.POST_TYPE_VOTE_DOWN,))
    downs = g_cursor.fetchone()[0]

    # update
    g_cursor.execute('update posts set num_votes=?, score=? where id=?', \
                        (ups+downs, ups-downs, id_,))

def recalculate_solver(id_):
    global g_cursor

    # get author, type
    g_cursor.execute('select author, type from posts where id=?', (id_,))
    data = g_cursor.fetchone()
    crackme_author, crackme_type = data[0], data[1]

    # if the type is not a crackme, don't worry about recalculating the solver
    if crackme_type != common.POST_TYPE_CRACKME:
        return

    # get the solutions (earliest posted first)
    g_cursor.execute('select id, author, score from posts where parent=? and type=? order by date_posted', \
                        (id_, common.POST_TYPE_SOLUTION,))
    solutions = g_cursor.fetchall()

    solver = ''
    # test solutions to see if author qualifies as solver
    for solution_data in solutions:
        sol_id = solution_data[0]
        sol_author = solution_data[1]
        sol_score = solution_data[2]

        # if author himself has upvoted this solution, solver is found!
        g_cursor.execute('select id from posts where parent=? and type=? and author=?',
                            (sol_id, common.POST_TYPE_VOTE_UP, crackme_author,))

        if g_cursor.fetchone():
            solver = sol_author
            break;

        # otherwise, see if solution is +4 score
        if sol_score > 3:
            solver = sol_author
            break;

    # update solver
    g_cursor.execute('update posts set solver=? where id=?',
                        (solver, id_,))

def recalculate_num_replies(id_):
    global g_cursor

    g_cursor.execute('select count(id) from posts where parent=?', (id_,))
    count = g_cursor.fetchone()[0]
    g_cursor.execute('update posts set num_replies=? where id=?', (count, id_,))

###############################################################################
# removal functions
###############################################################################
def remove_votes(id_, author):
    global g_cursor

    # delete author's previous votes
    g_cursor.execute("delete from posts where author=? and parent=? and (type=? or type=?)", \
                        (author, id_, common.POST_TYPE_VOTE_UP, common.POST_TYPE_VOTE_DOWN))

def remove_post(id_):
    global g_cursor

    # save parent for reply calculation
    g_cursor.execute('select parent from posts where id=?', (id_,))
    data = g_cursor.fetchone()

    parent = data[0]

    # collect given post and all children
    delete_ids = [id_]

    queue = [id_]
    while queue:
        curr = queue[0]
        queue = queue[1:]

        # who's posted under curr?
        g_cursor.execute("select id from posts where parent=?;", (curr,))
        for row in g_cursor.fetchall():
            delete_ids.append(row[0])
            queue.append(row[0])

    # now delete
    for di in delete_ids:
        # delete potential attachment
        g_cursor.execute("select attachment from posts where id=?;", (di,))
        attach_id = int(g_cursor.fetchone()[0])

        if attach_id:
            post_delete_attachment(attach_id)

        # delete the post itself
        g_cursor.execute("delete from posts where id=?;", (di,))
    
    # update parent's reply calculation
    if parent:
        recalculate_num_replies(parent) 
 
###############################################################################
# crackme posting related functions
###############################################################################

def post_to_dictionary(post):
    dic = {}
    dic['id'], dic['type'], dic['parent'], dic['date_posted'], dic['author'], \
        dic['title'], dic['content'], dic['attachment'], dic['score'], \
        dic['num_replies'], dic['date_activity'], dic['date_edited'], \
        dic['downloads'], dic['num_votes'], dic['solver'] = \
        post

    return dic

# insert a reference in the attachments table
# INPUT:
#   attach_base is a non-pathed name of file, like "31677303.gz"
# OUTPUT:
#   the id of the attached file
def post_enter_attachment(attach_base):
    global g_cursor

    common.doublecheck_attach_base(attach_base)

    g_cursor.execute("insert into attachments \
                        values(null, ?)", (attach_base,))

    g_cursor.execute("select id from attachments \
                        where path=?", (attach_base,))

    return g_cursor.fetchone()[0]

# remove attachment (file itself and reference in table)
# INPUT:
#   integer if you want to delete by id, string if delete by name
# OUTPUT:
#   none
def post_delete_attachment(id_or_base):
    global g_cursor

    # get file path
    base = ''
    if type(id_or_base) == type(0):
        g_cursor.execute("select path from attachments where id=?", \
                            (id_or_base,))    
        base = g_cursor.fetchone()[0]

    elif type(id_or_base) == type(""):
        base = id_or_base

    else:
        raise ValueError('invalid type supplied')

    # sanitize, delete
    common.doublecheck_attach_base(base)

    path = 'attachments/%s' % base
    common.doublecheck_attach_path(path)

    os.remove(path)

    # drop the entry from the attachment table
    if type(id_or_base) == type(0):
        g_cursor.execute("delete from attachments where id=?", \
                            (id_or_base,))    
    elif type(id_or_base) == type(""):
        g_cursor.execute("delete from attachments where path=?", \
                            (id_or_base,))

def post_crackme(name, title, content, attach_id):
    global g_cursor

    common.doublecheck_user(name)
    common.doublecheck_title(title)
    common.doublecheck_content(content)

    # ensure that attach_id exists in attachment table
    g_cursor.execute("select path from attachments where id=?", \
                        (attach_id,))

    if not g_cursor.fetchone():
        raise Exception("attachment id not valid")

    # insert crackme into table 
    now = int(time.time())

    g_cursor.execute("insert into posts \
                        values(null,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", \
                        (common.POST_TYPE_CRACKME, 0, now, name, title, content, \
                            attach_id, 0, 0, now, now, 0, 0, '',));

def post_edit(id_, name, title, content, attach_id):
    common.doublecheck_user(name)
    common.doublecheck_title(title)
    common.doublecheck_content(content)
    common.doublecheck_attach_id(attach_id)
    
    now = int(time.time())

    g_cursor.execute("update posts set author=?, title=?, content=?, \
                        attachment=?, date_edited=? where id=?", \
                        (name, title, content, attach_id, now, id_,))

def post_comment(id_, name, title, content, post_type, attach_base):
    common.doublecheck_user(name)
    common.doublecheck_title(title)
    common.doublecheck_content(content)
    common.doublecheck_attach_base(attach_base)
 
    global g_cursor

    attach_id = 0
    if attach_base:
        # insert attachment entry into table
        g_cursor.execute("insert into attachments \
                            values(null,?)", (attach_base,))

        # 
        g_cursor.execute("select id from attachments where path=?",
                            (attach_base,));
        attach_id = g_cursor.fetchall()[0][0]
   
    # insert reply into table 
    now = int(time.time())

    if (post_type != common.POST_TYPE_COMMENT) and (post_type != common.POST_TYPE_SOLUTION):
        raise Exception('ERROR: invalid post_type: %s' % type_)

    g_cursor.execute("insert into posts \
                        values(null,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", \
                        (post_type, id_, now, name, title, content, \
                            attach_id, 0, 0, now, 0, 0, 0, '',));
    
    # now must increment parent "replies"
    g_cursor.execute("update posts set num_replies=num_replies+1 where id=?", (id_,))

    # now must bubble-up last_activity
    id_bubble = int(id_)
    while 1:
        g_cursor.execute("update posts set date_activity=? where id=?", \
            (now, id_bubble,))

        g_cursor.execute("select parent from posts where id=?", (id_bubble,))
        id_bubble = g_cursor.fetchall()[0][0];

        if not id_bubble:
            break

def post_vote(id_, name_, dir_):
    common.doublecheck_user(name_)

    global g_cursor

    # remove old votes (also recalculates votes/score/solver)
    remove_votes(id_, name_)

    # update num_votes, score
    if dir_ == 'up':
        g_cursor.execute("update posts set num_votes=num_votes+1, score=score+1 \
                            where id=?", (id_,))
    elif dir_ == 'down':
        g_cursor.execute("update posts set num_votes=num_votes+1, score=score-1 \
                            where id=?", (id_,))
    else:
        raise Exception('ERROR: invalid vote direction: %s', dir_)  
 
    # add the actual post
    now = int(time.time())
    post_type = common.POST_TYPE_VOTE_UP
    if dir_ == 'down':
        post_type = common.POST_TYPE_VOTE_DOWN
    g_cursor.execute("insert into posts \
                        values(null,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", \
                        (post_type, id_, now, name_, '', '', \
                            0, 0, 0, now, now, 0, 0, '',))

    # recalculate the votes/score
    recalculate_votes_score(id_)

    # if this post is a solution to a crackme, the crackme itself may require
    # recalculation of its solver member
    g_cursor.execute('select type, parent from posts where id=?', (id_,))
    data = g_cursor.fetchone()
    if data[0] == common.POST_TYPE_SOLUTION:
        recalculate_solver(data[1])

###############################################################################
# crackme post retrieval functions
###############################################################################

def posts_get_latest():
    global g_cursor
    g_cursor.execute("select * from posts where type=? order by date_activity \
                        desc limit 128", (common.POST_TYPE_CRACKME,))
    return g_cursor.fetchall()

def posts_get(id_):
    global g_cursor
    g_cursor.execute("select * from posts where id=?", (id_,))
    data = g_cursor.fetchone()
    return data

def posts_get_replies_ids(id_):
    global g_cursor
    g_cursor.execute("select id from posts where (type=? or type=?) and parent=?", \
                        (common.POST_TYPE_COMMENT, common.POST_TYPE_SOLUTION, id_,))
    data = g_cursor.fetchall()
    return data

def posts_get_replies(id_):
    global g_cursor
    g_cursor.execute("select * from posts where (type=? or type=?) and parent=?", \
                        (common.POST_TYPE_COMMENT, common.POST_TYPE_SOLUTION, id_,))
    data = g_cursor.fetchall()
    return data

def posts_get_attachment_path(id_):
    global g_cursor

    # get post id and number of downloads for this download id
    g_cursor.execute("select id from posts where attachment=?", \
                        (id_,))
    id_post = g_cursor.fetchone()[0]

    # bump up the download count for this post id
    g_cursor.execute("update posts set downloads=downloads+1 where id=?", \
                        (id_post,))

    # retrieve the download path for this download id    
    g_cursor.execute("select path from attachments where id=?", (id_,))
    path = 'attachments/' + g_cursor.fetchone()[0]

    return path

###############################################################################
# statistics junk
###############################################################################
def stat_get_num_users():
    global g_cursor
    g_cursor.execute("select count(id) from users");
    return g_cursor.fetchone()[0]

def stat_get_num_users_login_since(since):
    global g_cursor
    g_cursor.execute("select count(id) from users where date_login > ?", \
                        (since,));
    return g_cursor.fetchone()[0]
   
def stat_get_num_crackmes():
    global g_cursor
    g_cursor.execute("select count(id) from posts where type=?", \
                        (common.POST_TYPE_CRACKME,));
    return g_cursor.fetchone()[0]

def stat_get_num_crackmes_good():
    global g_cursor
    g_cursor.execute("select count(id) from posts where type=? and score>0", \
                        (common.POST_TYPE_CRACKME,));
    return g_cursor.fetchone()[0]

def stat_get_moderators():
    global g_cursor
    g_cursor.execute("select name from users where name like '@%';")
    rows = g_cursor.fetchall()
    mods = []
    for row in rows:
        mods.append(row[0])
    return mods

###############################################################################
# user info stuff
###############################################################################

def user_to_dictionary(row):
    return {'id':row[0],
            'name':row[1],
            'status':row[2],
            'profile':row[3],
            'date':row[4],
            'extra':row[5],
            'pwhash':row[6],
            'date_login':row[7],
            'image':row[8]}

def user_get_user(user):
    global g_cursor

    common.doublecheck_user(user)

    g_cursor.execute("select * from users where name=?", (user,))

    return g_cursor.fetchone();
 
def user_get_posted_crackmes(user):
    global g_cursor

    common.doublecheck_user(user)

    g_cursor.execute("select * from posts where type=? and author=? order by \
                        date_posted desc", \
                        (common.POST_TYPE_CRACKME, user,))

    return g_cursor.fetchall()

def user_get_solutions_all(user):
    global g_cursor

    common.doublecheck_user(user)

    # collect the parent ids of solution posts
    #g_cursor.execute("select * from posts where type=? and id in \
    #                    (select parent from posts where type=? and author=?)", \
    #                    (POST_TYPE_CRACKME, POST_TYPE_SOLUTION, user,));
    g_cursor.execute('select c.*, s.score, s.num_votes from posts as c \
                        join posts as s \
                        on (c.id = s.parent) \
                        where c.type=? and s.type=? \
                            and s.author=? \
                        order by date_posted;', \
                        (common.POST_TYPE_CRACKME, common.POST_TYPE_SOLUTION, user,));

    return g_cursor.fetchall()


def user_update(user, profile):
    global g_cursor

    common.doublecheck_user(user)
    common.doublecheck_content(profile)

    g_cursor.execute('update users set profile=? where name=?;', \
                        (profile, user,))

def user_update_password(user, pwhash):
    common.doublecheck_user(user)
    common.doublecheck_pwhash(pwhash)

    global g_cursor
    g_cursor.execute("update users set pwhash=? where name=?", (pwhash,user,))
