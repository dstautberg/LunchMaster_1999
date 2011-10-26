import dbi, odbc, string, cgi, sys, traceback, os, os.path, time
from urllib import quote, unquote

def GetDateToday():
    return time.strftime ('%A %B %d, %Y', time.localtime(time.time()))

def GetTimeStamp():
    return time.time()

def MakeNonNull (value):
    if value == None: return "&nbsp;"
    elif len(string.strip(str(value))) == 0: return "&nbsp;"
    else: return str(value)

def CleanDbResults (results):
    # Clean up the results a bit to avoid null values (None) and to replace quoted "special characters"
    for i in range(len(results)):
        row = results[i]
        row = [ MakeNonNull(row[0]), MakeNonNull(row[1]), MakeNonNull(row[2]), MakeNonNull(row[3]), MakeNonNull(row[4]), MakeNonNull(row[5]), MakeNonNull(row[6]), MakeNonNull(row[7]) ]
        row = [ unquote(row[0]), unquote(row[1]), unquote(row[2]), unquote(row[3]), unquote(row[4]), unquote(row[5]), unquote(row[6]), unquote(row[7]) ]
        results[i] = row
    return results

def GetLunchData (dbname, dbuser, dbpwd):
    # Run the query to get everyone's lunch plans
    conn = odbc.odbc ("%s/%s/%s" % (dbname, dbuser, dbpwd))
    cur = conn.cursor()
    cur.execute ('select * from LunchInfo')
    results = CleanDbResults (cur.fetchall())

    # Delete any row whose timestamp is over 12 hours old
    dataChanged = 0
    for row in results:
        if (time.time() - float(row[7])) > (12.0 * 60.0 * 60.0):
            # Make sure to use the quoted username, since that's what's in the database
            sql = "delete from LunchInfo where user='%s'" % (quote(row[0]))
            cur.execute (sql)
            dataChanged = 1

    # Refresh the query if the data was changed
    if dataChanged:
        cur.execute ('select * from LunchInfo')
        results = CleanDbResults (cur.fetchall())

    conn.close()
    conn, cur = (None, None)
    return results

def InsertUserData (dbname, dbuser, dbpwd, data):
    try: 
        # Make sure the data has no special characters
        data = [ quote(data[0]), quote(data[1]), quote(data[2]), quote(data[3]), quote(data[4]), quote(data[5]), quote(data[6]) ]

        # First delete any current row for this user
        conn = odbc.odbc ("%s/%s/%s" % (dbname, dbuser, dbpwd))
        cur = conn.cursor()
        sql = "delete from LunchInfo where user='%s'" % (data[0])
        cur.execute (sql)

        # Then insert a row with the new data
        sql = "insert into LunchInfo values ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (data[0], data[1], data[2], data[3], data[4], data[5], data[6], GetTimeStamp())
        cur.execute (sql)
        conn.close()
        conn, cur = (None, None)
    except:
        print '<font size="+1">SQL Error: %s</font>: %s<BR>' % sys.exc_info()[:2]
        print '<PRE>%s</PRE>' % (sql)

def service():
    # Start the page
    print "Content-type: text/html"
    print
    print '<!DOCTYPE html public "-//W3C//DTD HTML 4.0 Transitional//EN">'
    print '<HTML>'
    print '<HEAD>'
    print '<META HTTP-EQUIV="expires" CONTENT="0"><META HTTP-EQUIV="pragma" CONTENT="no-cache">'
    print '<META HTTP-EQUIV="refresh" CONTENT="30 ;url=%s">' % (os.environ['SCRIPT_NAME'])
    print '<TITLE>Lunch Master</TITLE>'
    print '</HEAD>'
    print '<BODY bgcolor="tan">'

    print '<FONT SIZE="+1" COLOR="#CC0000">Sorry folks, but LunchMaster is down because of technical difficulties. :-(<BR>'
    print 'Please check back tomorrow.</FONT>'
    return

    DB_NAME, DB_USER, DB_PWD = 'Lunch', '', ''
    try: execfile ('LunchMaster.cfg')
    except: pass

    # Get form data if any
    pName, pStatus, pVendalunch, pTime, pFlextime, pPlace, pFlexplace = '', '', '', '', '', '', ''
    form = cgi.FieldStorage()
    if form.has_key("username"):   pName = form["username"].value
    if form.has_key("status"):     pStatus = form["status"].value
    if form.has_key("vendalunch"): pVendalunch  = form["vendalunch"].value
    if form.has_key("time"):       pTime = form["time"].value
    if form.has_key("flextime"):   pFlextime  = form["flextime"].value
    if form.has_key("place"):      pPlace = form["place"].value
    if form.has_key("flexplace"):  pFlexplace = form["flexplace"].value

    remoteHost, remoteAddr = os.environ['REMOTE_HOST'], os.environ['REMOTE_ADDR']

    # If we have form data, add it to the database
    if len(pName) > 0:
        InsertUserData (DB_NAME, DB_USER, DB_PWD, [pName, pStatus, pVendalunch, pTime, pFlextime, pPlace, pFlexplace])

    print '<TABLE width="100%" border="0">'
    print '    <TR>'
    print '        <TD align="middle">'
    print '            <IMG alt="" border=0 height=35 src="/images/lunchbag_small.gif" width=24>&nbsp;'
    print '            <FONT size="5" face="Arial">Lunch Plans for %s</FONT>&nbsp;' % (GetDateToday())
    print '            <IMG alt="" border=0 height=35 src="/images/lunchbag_small.gif" width=24>'
    print '        </TD>'
    print '    </TR>'
    print '</TABLE>'
    
    # Write the header row for everyone's lunch plans
    print '<TABLE border="1" width="100%">'
    print '    <TR>'
    print '        <TH bgcolor="cornflowerblue">Name</TH>'
    print '        <TH bgcolor="cornflowerblue">Status</TH>'
    print '        <TH bgcolor="cornflowerblue">VendaLunch?</TH>'
    print '        <TH bgcolor="cornflowerblue">Desired Time</TH>'
    print '        <TH bgcolor="cornflowerblue">Flexible on Time?</TH>'
    print '        <TH bgcolor="cornflowerblue">Desired Place(s)</TH>'
    print '        <TH bgcolor="cornflowerblue">Flexible on Place?</TH>'
    print '    </TR>'

    # Write the data rows
    results = GetLunchData (DB_NAME, DB_USER, DB_PWD)
    if len(results) > 0:
        for data in results:
            print '<TR>'
            print '<TD align="middle"><B>%s</B></TD>' % (data[0])

            if data[1] == 'packed':       print '<TD align="middle"><font color="#000088">packed</font></TD>'
            elif data[1] == 'have plans': print '<TD align="middle"><font color="#770000">have plans</font></TD>'
            elif data[1] == 'going out':  print '<TD align="middle"><font color="#005500">going out</font></TD>'
            else:                         print '<TD align="middle"><font color="#000000">???</font></TD>'

            if data[2] == "ok": print '<TD align="middle"><font color="#005500">ok</font></TD>'
            else:               print '<TD align="middle"><font color="#770000">no</font></TD>'

            print '<TD align="middle">%s</TD>' % (data[3])

            if data[4] == "yes": print '<TD align="middle"><font color="#005500">yes</font></TD>'
            else:                print '<TD align="middle"><font color="#770000">no</font></TD>'
            
            print '<TD align="middle">%s</TD>' % (data[5])

            if data[6] == "yes": print '<TD align="middle"><font color="#005500">yes</font></TD>'
            else:                print '<TD align="middle"><font color="#770000">no</font></TD>'
            
            print '</TR>'
    else:
        print '<TR><TD colspan="7" align="middle"><BR><B>No one has entered lunch plans for today.</B><BR><BR></TD></TR>'

    print '</TABLE>'

    # Write a separator row of food images
    print '<TABLE border="0" width="100%">'
    print '    <TR>'
    print '        <TD align="left" width="33%"><IMG alt="" border=0 height=39 src="/images/Hamburger4_small.gif" width=50></TD>'
    print '        <TD align="middle" width="33%"><IMG alt="" border=0 height=50 src="/images/Taco_small.gif" width=85></TD>'
    print '        <TD align="right" width="33%"><IMG alt="" border=0 height=47 src="/images/chickennuggets-small.gif" width=50></TD>'
    print '    </TR>'
    print '</TABLE>'
    print '<HR>'

    # Add a form for users to enter their own lunch plans
    print '<FORM name="form" action="%s">' % (os.environ['SCRIPT_NAME'])
    print '<FONT size="5">Add your Lunch Plans</FONT>'
    print '<BR><BR>'
    print '<TABLE border="0">'
    print '    <TR>'
    print '        <TD><b>Your name:</b></TD>'
    print '        <TD>&nbsp;<INPUT name="username" type="text"></TD>'
    print '    </TR>'
    print '    <TR><TD><b>Lunch status:</b></TD><TD><INPUT name="status" type="radio" value="packed">&nbsp;I packed lunch&nbsp;</TD></TR>'
    print '    <TR><TD>&nbsp;</TD><TD><INPUT name="status" type="radio" value="going out">&nbsp;I need to go out to get lunch</TD></TR>'
    print '    <TR><TD>&nbsp;</TD><TD><INPUT name="status" type="radio" value="have plans">&nbsp;I already have lunch plans or I\'m not eating lunch</TD></TR>'
    print '    </TR>'
    print '</TABLE>'
    print '<TABLE border="0">'
    print '    <TR>'
    print '        <TD><b>I\'m willing to get food from cafeteria vending machines:</b></TD>'
    print '        <TD>'
    print '            <INPUT name="vendalunch" type="radio" value="ok">Yes'
    print '            <INPUT name="vendalunch" type="radio" value="no">No'
    print '        </TD>'
    print '    </TR>'
    print '</TABLE>'
    print '<TABLE>'
    print '    <TR>'
    print '        <TD><b>When would you like to eat?</b></TD>'
    print '        <TD><INPUT name="time" type="text"></TD>'
    print '        <TD>&nbsp;Are you flexible about this time?</TD>'
    print '        <TD>'
    print '            <INPUT name="flextime" type="radio" value="yes">Yes'
    print '            <INPUT name="flextime" type="radio" value="no">No'
    print '        </TD>'
    print '    </TR>'
    print '    <TR>'
    print '        <TD><b>Where would you like to eat?</b></TD>'
    print '        <TD><INPUT name="place" type="text"></TD>'
    print '        <TD>&nbsp;Are you flexible about where to eat?</TD>'
    print '        <TD>'
    print '            <INPUT name="flexplace" type="radio" value="yes">Yes'
    print '            <INPUT name="flexplace" type="radio" value="no">No'
    print '        </TD>'
    print '    </TR>'
    print '</TABLE>'
    print '<IMG alt="" border=0 height=50 src="/images/Sandwich_small.gif" width=68>&nbsp;&nbsp;'
    print '<INPUT type="submit" value="Submit">&nbsp;&nbsp;'
    print '<INPUT type="reset" value="Reset" onclick="javascript:document.form.reset();">'
    print '<FONT SIZE="-1" COLOR="#444444">'
    print '&nbsp;&nbsp;&nbsp;Note: If you need to change your lunch plans later, just re-submit them using the same name.<BR>'
    print '<FONT>'
    print '</P>'
    print '</FORM>'
    print '</BODY>'
    print '</HTML>'

# --------------------------------------------------------------------------------------------------
try:
    service()

except:
    print "Content-type: text/html"
    print
    print '<BODY>'
    print '<font size="+1">Error: %s</font>: %s<BR>' % sys.exc_info()[:2]
    print '<PRE>'
    print 'Traceback:'
    traceback.print_tb (sys.exc_info()[2], file=sys.stdout)
    print '</PRE>'
    print '</BODY>'
