
# (Setup 1/3) database
So easy! Python just `import sqlite3` and the db file is crackmes.db. Optionally grab http://crackmesus.dreamhosters.com/crackmes.db to get started.

Note that wrapdb.py is the only thing that imports this because, all database requests are supposed to funnel thru this module so that there's a central place to sanitize input.

# (Setup 2/3) crackmes files
Not in the repo, but create directory ./attachments and seed it with http://crackmesus.dreamhosters.com/attachments.

# (Setup 3/3) server setup
I test during development with thttpd, invoking it with `thttpd -p 8080 -c "*.py" -D` and navigating my browser to http://localhost:8080/index.py.

Any other server just needs to be configured to execution python. For servers support .htaccess style directives (apache, nginx), I use:
```
DirectoryIndex index.py
Options +ExecCGI
AddHandler cgi-script .py
AddHandler cgi-script .cgi
```


