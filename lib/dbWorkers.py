import sqlite3
import time
import datetime
import sys
import os
from config import *
import logger

msg=logger.msg
getTime=logger.getTime
getDate=logger.getDate
logFileObj=logger.logFileObj
myConnection = None
myCursor = None

# intiate DB connection
# returns 1 for success and 0 for failure
def startConnection(IP=''):
    global myCursor, myConnection
    isSuccess = 0;
    msg(0, "START_DB", "Creating connection to " + DBNAME + "." + DBTABLE, IP)
    try:
        myConnection = sqlite3.connect('db/' + DBNAME)
        myCursor = myConnection.cursor()
        isSuccess = 1
        msg(0, "START_DB", "Success. Connected to: " + DBNAME + "." + DBTABLE, IP)
    except sqlite3.Error as e:
        myCursor.execute(open('db/%s.sql' % DBNAME).read())
        msg(1, "START_DB", " Fail! %s" % (e.args[0]) + DBNAME + "." + DBTABLE, IP)
        
    return isSuccess

# stopping DB connection
# returns 1 for success and 0 for failure
def stopConnection(IP=''):
    global myCursor, myConnection, logFileObj
    opType = "STOP_DB"
    isClosed = 0;
    msg(0, opType, "Closing connection to " + DBNAME + "." + DBTABLE, IP)
    try:
        myConnection.close()
        myConnection = None
        myCursor = None
        isClosed = 1
        msg(0, opType, "Connection closed to " + DBNAME + "." + DBTABLE, IP)
    except:
        msg(1, opType, "Failed to close connection to " + DBNAME + "." + DBTABLE, IP)
    if logFileObj:
        logFileObj.close()
        logFileObj = None
    return isClosed

# get the value of a given key
# returns retFlags,values
# retFlags
# 	0  - if key present
# 	1  - if key not present
# 	-1 - failure
def get(key, IP=''):
    global myCursor, myConnection
    retFlag = 0
    opType = "GET"
    if not myCursor:
        startConnection(IP)
    value = ''
    try:
        sqlSmt = "SELECT value from " + DBTABLE + " where key = '" + key + "'"
        msg(0, opType, "SQL: " + sqlSmt, IP)
        myCursor.execute(sqlSmt)
        d = myCursor.fetchone()
        if d:
            value = d[0]
            retFlag = 0
            msg(0, opType, "key='" + key + "' found!", IP)
        else:
            retFlag = 1
            msg(0, opType, "key='" + key + "' not found!", IP)
    except:
        retFlag = -1
        print sys.exc_info()
        msg(1, opType, "operation failed for key='" + key + "'!", IP)

    return retFlag, value

# get all the key-values pairs
# returns retFlags,count,allData
# retFlags
#       0  - if at least 1 present
#       1  - if no keys present
#       -1 - failure
# count: number of key-values pairs found
# allData: 2d array with key-value pairs 
def getAll(IP=''):
    global myCursor, myConnection
    opType = "GET_ALL"
    allData = []
    count = 0
    retFlag = -1
    if not myCursor:
        startConnection()
    value = ''
    try:
        sqlSmt = "SELECT * FROM " + DBTABLE
        #msg(0, opType, "SQL: " + sqlSmt, IP)
        for row in myCursor.execute(sqlSmt):
            allData.append((row[0], row[1]))
            count = count + 1
        msg(0, opType, str(count) + " row(s) fetched", IP)
        if count == 0:
            retFlag = 1
        else:
            retFlag = 0
    except:
        retFlag = -1
        print sys.exec_info()
        msg(1, opType, "getting all key-value pairs failed!")
    return retFlag, count, allData

# inserts/updates the value of a given key
# returns retFlags,oldValue
# retFlags
# 	0  - if key present hence updated
# 	1  - if key not present hence inserted
# 	-1 - failure
def put(key, value, IP=''):
    global myCursor, myConnection
    opType = "PUT"
    retFlag = -1
    if not myCursor:
        startConnection()
    try:
        #msg(0, opType, "adding key='" + key + "' & value='" + value[:20] + "'", IP)
        retFlag, oldValue = get(key, IP)
        if retFlag == -1:
            raise
        elif retFlag == 1: # key not found
            sqlSmt = "INSERT INTO " + DBTABLE + " VALUES ('" + key + "','" + value + "');"
            #msg(0, opType, "SQL: " + sqlSmt, IP)
            myCursor.execute(sqlSmt)
            myConnection.commit()
        else: # key found
            if oldValue != value:
                sqlSmt = "UPDATE " + DBTABLE + " SET value='" + value + "' where key='" + key + "'"
                myCursor.execute(sqlSmt)
                myConnection.commit()
            #msg(0, opType, "SQL: " + sqlSmt, IP)
            #msg(0, opType, "value updated from '" + oldValue + "' to '" + value + "'", IP)
        msg(0, opType, "successful", IP)
    except:
        msg(1, opType, "failed!", IP)

    return retFlag, oldValue

# deletes a key-value pair if found
# returns retFlags,oldValue
# retFlags
#       0  - if key present hence deleted
#       1  - if key not present hence not deleted
#       -1 - failure
def delete(key, IP=''):
    global myCursor, myConnection
    opType = "DELETE"
    retFlag = -1
    if not myCursor:
        startConnection()
    try:
        msg(0, opType, "deleting key='" + key + "'", IP)
        retFlag, oldValue = get(key, IP)
        if retFlag == -1:
            raise
        elif retFlag == 0:
            sqlSmt = "DELETE FROM " + DBTABLE + " WHERE key='" + key + "'"
            msg(0, opType, "SQL: " + sqlSmt, IP)
            myCursor.execute(sqlSmt)
            msg(0, opType, "value='" + oldValue + "' deleted!", IP)
        else:
            msg(0, opType, "key to be deleted not found.", IP)
        myConnection.commit()
        msg(0, opType, "successful", IP)
    except:
        msg(1, opType, "failed!", IP)

    return retFlag, oldValue

def unit_test():
    #UNIT TEST BELOW!
    myIP = "localhost:unit_test"
    print ""
    print "*****      TEST 0 START: starting connection"
    startConnection(myIP);
    print "*****      TEST 0 END"
    testKey = getTime()
    print ""
    print "*****      TEST 1 START: adding an new value"
    res, oldValue = put(testKey, "newValue", myIP)
    print "*****      OUTPUT: ", res
    print "*****      TEST 1 END"
    print ""
    print "*****      TEST 2 START: adding an old value"
    res, oldValue = put(testKey, "newValue", myIP)
    print "*****      OUTPUT: ", res
    print "*****      TEST 2 END"
    print ""
    print "*****      TEST 3 START: get an value that exist"
    res, value = get("1", myIP)
    print("*****      Value for Key=1 is " + value)
    print "*****      OUTPUT: ", res
    print "*****      TEST 3 END"
    print ""
    print "*****      TEST 4 START: get an value that does not exist"
    res, value = get("IdontExist", myIP)
    print("*****      Value for Key=IdontExist is " + value)
    print "*****      OUTPUT: ", res
    print "*****      TEST 4 END"
    print ""
    print "*****      TEST 5 START: delete a value that does not exist"
    res, value = delete("IdontExist", myIP)
    print("*****      Old Value for Key=IdontExist is " + value)
    print "*****      OUTPUT: ", res
    print "*****      TEST 5 END"
    print ""
    print "*****      TEST 6 START: delete a value that exists"
    res, value = delete(testKey, myIP)
    print("*****      Old Value for Key=" + testKey + " is " + value)
    print "*****      OUTPUT: ", res
    print "*****      TEST 6 END"
    print ""
    print "*****      TEST 8 START: get all (key,value)"
    res, count, allData = getAll(myIP)
    localCount = 0
    for row in allData:
        localCount = localCount + 1
        print("*****            Key='" + row[0] + "' ---> value='" + row[1] + "' ... [" + str(localCount) \
              + "/" + str(count) + "]")
    print "*****      OUTPUT: ", res
    print "*****      TEST 8 END"
    print ""
    print "*****      TEST 8 START: close connection"
    stopConnection(myIP);
    print "*****      TEST 8 END"
    print ""
    print "*****      TEST 9 START: get an value that exist with connection closed!"
    res, value = get("1", myIP)
    print("*****      Value for Key=1 is " + value)
    print "*****      OUTPUT: ", res
    stopConnection(myIP);
    print "*****      TEST 9 END"
    print ""

if __name__ == '__main__':
    unit_test()
