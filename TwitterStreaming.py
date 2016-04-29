#!/usr/bin/env python

from textwrap import TextWrapper

import tweepy
import os
import datetime
import time
import threading
import Queue


import json

#opening new file to write to
print "Opening new file to write to..."
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('%H-%M-%S')
fileName = "indiaTweets" + st + ".json"
file = open(fileName, "w")

#initializing file, counter, and exitflag
file.write("{")
counter = 0
exitFlag = 0

#subclass of Thread, pass in lock and queue of data
class myThread (threading.Thread):
    def __init__(self, qLock, workQ):
        print "Initializing thread..."
        threading.Thread.__init__(self)
        self.qLock = qLock
        self.workQ = workQ
    def run(self):
        process_data(self.qLock, self.workQ)

#process data using separate thread
def process_data(qLock, workQ):
    global counter
    #print exitFlag
    while not exitFlag:
        qLock.acquire()
        if not workQ.empty():
            #print "Have something in workQ... Processing..."
            data = workQ.get()
            qLock.release()
            decoded = json.loads(data)
            try:
                #print decoded['text']
                if ("autism" in decoded['text'] or "autistic" in decoded['text'] or "developmental disorder" in decoded['text'] or "child development" in decoded['text']):
                #if ("#india" in decoded['text']):
                    counter += 1
                    #print "useful data found from:"
                    file.write('"' + "tweet" + str(counter) + '": ')
                    print decoded['user']['screen_name']
                    json.dump(decoded, file, indent=4, ensure_ascii=True)
                    file.write(",")
                    #print "is this happening1"
                    file.write("\n")
                    #print "is this happening2"
            except Exception, e: 
                print str(e)
        else:
            qLock.release()
            #print "workQ empty, qLock released by data_processor..."

class StreamWatcherListener(tweepy.StreamListener):
    global counter
    def __init__(self, q=None, qLock=None, api=None):
        super(StreamWatcherListener, self).__init__()
        self.q = q
        self.qLock = qLock

    def on_data(self, data):
        #decoded = json.loads(data)
        #print "This tweet was created at: " + decoded['created_at']
        #ts = time.time()
        #st = datetime.datetime.fromtimestamp(ts).strftime('%H-%M-%S')
        #print "This tweet was processed at: " + st
        self.qLock.acquire()
        #print "qLock acquired by on_data..."
        self.q.put(data)
        #print self.q.qsize()
        self.qLock.release()
        #print "qLock released by on_data..."

    def on_error(self, status_code):
        print 'An error has occured! Status code = %s' % status_code
        return True  # keep stream alive

    def on_timeout(self):
        print 'Snoozing Zzzzzz'


def main():
    global exitFlag

    # Prompt for login credentials and setup stream object
    print "Setting up keys and tokens..."
    consumer_key = "qRqv74RtDSHDLYduSlhjpOaPN"
    consumer_secret = "z3FQaAGaB6YTEL7OQr48MlnPk6RFJjaA3kW4mnZ7lehKsjcDPl"
    access_token = "2830438275-1dmOOhi3CLknDYL5MnvNytZyPQL46JZpDKQrdnv"
    access_token_secret = "qDHAYBJBlNtsw7NCGA62UJxcgK58pCKnxImsRsDWavwVt"

    print "Setting up authorization handler..."
    auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    # Prompt for mode of streaming
    print "Setting up parameters..."
    #keywords = ["autism", "autistic", "developmental disorder", "child development"]
    #keywords = ["india"]
    latUpper = 36
    latLow = 8
    lonLow = 70
    lonUpper = 88
    result = None

    print "Creating qLock, workQ, and thread"
    qLock = threading.Lock()
    workQ = Queue.Queue(0)
    thread = myThread(qLock, workQ)
    print "Starting thread..."
    thread.start()

    while result is None:
        try:
            print "Connecting to stream..."
            stream = tweepy.Stream(auth, StreamWatcherListener(workQ, qLock), timeout=None)
            stream.filter(locations=[lonLow, latLow, lonUpper, latUpper])
        except KeyboardInterrupt:
            print "Handling keyboard interrupt..."
            while not workQ.empty():
                pass
            exitFlag = 1
            thread.join()
            print "Exiting main thread..."
            print "Finishing writing to and closing file..."
            #print "in function interrupt handler"
            if (os.stat(fileName).st_size > 3):
                file.seek(-1, os.SEEK_END)
                file.truncate()
                file.seek(-1, os.SEEK_END)
                file.truncate()
                file.seek(-1, os.SEEK_END)
                file.truncate()
            file.write("}")
            file.close()
            break
        except:
            print "Error in stream, trying again..."
            continue


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        #print '\nGoodbye!'
        #print "in main interrupt handler"
        if (os.stat(fileName).st_size > 3):
            file.seek(-1, os.SEEK_END)
            file.truncate()
            file.seek(-1, os.SEEK_END)
            file.truncate()
            file.seek(-1, os.SEEK_END)
            file.truncate()
        file.write("}")
        file.close()
