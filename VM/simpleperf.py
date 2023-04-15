import argparse
import sys
import re
import ipaddress
from socket import *
import _thread as thread
import time
import math
import pickle
from threading import Thread


def check_port(val):                #checks if port-number is valid
    try:
        int(val)                    #Tests if input can be an integer
    except:
        raise argparse.ArgumentTypeError("The port number", val, "is not an integer", type(val))    #Error-message if not integer

    val = int(val)                  #Make the input an integer
    if val >= 1024 and val <= 65535:#Checks if the integer is between 1024 and 65535
        return val                  #Ok to return
    else:
        raise argparse.ArgumentTypeError("The port number must be between 1024 and 65535") #Error-message if not between [1024, 65535]

def check_ip(val):                          #Checks if IP has the right syntax
    try:
        val = ipaddress.ip_address(val)     #Checks with the ipaddress import if it's a valid IP
    except:
        raise argparse.ArgumentTypeError("IP-address syntax wrong") #Error-message if IP-syntax is wrong
    return val                              #If the test was OK, return the value


def check_time(val): #Checks if time is of a reasonable value
    try:
        int(val)    #Checks if the input can become an integer
    except:
        raise argparse.ArgumentTypeError("Time", val ,"must be of type integer") #Error-message if the input cannot be an integer
    
    val = int(val)      #Makes the input an integer
    if val > 0:         #Checks if the input is greater than 0
        return val      #Test OK, return the value
    else:               #If the value is equal or less than 0
        raise argparse.ArgumentTypeError("Time must be more than 0") #Error-message if input is equal or less than 0

def check_parallel(val):    #Checks if the parallel-input is valid
    try:
        int(val)            #Checks if the input can be an integer
    except:
        raise argparse.ArgumentTypeError("The number of parallel connections was not an integer") #Error-message if the input cannot be an integer
    
    val = int(val)          #Makes the input an integer
    if val > 0 and val < 6: #Checks if the input is between 0 and 6 [1, 5]
        return val          #Returns the value if OK
    else:                   #If the input is too high or too low
        raise argparse.ArgumentTypeError("The number of parallel connections must be between 1 and 5") #Error-message input out of range

def check_interval(val):    #Checks if the input for interval is valid
    try:
        int(val)            #Checks if the input can become an integer
    except:
        raise argparse.ArgumentTypeError("Interval must be of type integer")    #Error-message if the input cannot become an integer
    
    val = int(val)          #Makes the input an integer
    if val > 0:             #Checks if the integer is greater than 0
        return val          #If OK, return value
    else:                   #if integer is equal or lower than 0
        raise argparse.ArgumentTypeError("Interval must be above 0")    #Error-message input too low    

def check_bytes(val):   #Checks if the number of bytes is of the right format
    #Source https://www.w3schools.com/python/python_regex.asp
    #Date: 17.03.2023 14:21
    numberArray=re.findall("(\d+)", val)        #Finds the number of the input
    letterArray=re.findall("(\D+)", val)        #finds the letter of the input
    if len(numberArray) > 1:                    #if there are more than one number e.g. 23B12
        raise argparse.ArgumentTypeError("Only write one number") #Error-message if too many numbers
    elif len(numberArray) == 0:                 #if there are no numbers #e.g. B
        raise argparse.ArgumentTypeError("You must specify a number") #Error message not enough numbers
    elif len(letterArray) > 1:                  #If there are too many letters #e.g. B23B
        raise argparse.ArgumentTypeError("Only one word allowed") #Error-message too many letters
    elif len(letterArray) == 0:                 #if there are no letters #e.g. 23
        raise argparse.ArgumentTypeError("You must specify bit size") #Error-message not enough letters
    elif len(list(letterArray[0])) > 1:         #If there are two letters next to each other #e.g 23SS
        raise argparse.ArgumentTypeError("The bit size should only consist of one of these letters: B, K or M") #Error-message to many letters
    elif len(re.findall("[BKM]", letterArray[0])) == 0:     #if there are no instances of the correct letters B, K or M #e.g. 32S
        raise argparse.ArgumentTypeError("The bit size letter must be either B, K or M") #Error-message wrong letter
    else:
        return val      #If the tests arrives here, then all OK, return the value

def sekToClock(sek):    #Converts seconds to clock format e.g. 64 sec = 1:04.0 or 5 sec = 5.0
    min = math.trunc((sek/60)%60)   #Finds number of minutes
    hour = math.trunc(sek/3600)     #Finds the number of hours
    sek = float(sek%60)             #Finds the remaining number of seconds

    #This decides what the output-format should look like
    if hour == 0 and min == 0:      #if time is less than a minute
        out = str(sek)              #send only seconds
        return out
    elif hour == 0:                 #if time is less than an hour
        out = str(min),str(sek)     #send minutes and seconds
        return ":".join(out)        #join them with a ':' e.g. 3:05.0
    else:
        out = str(hour),str(min),str(sek)   #if time is over an hour, send all
        return ":".join(out)                #join them with ':' e.g. 2:43:21.0

def clockToSek(inTime):     #Converts clock-format into seconds
    inTime = inTime.split()[3].split(":")   #Take the time and split them according to ':' 
    sek = float(inTime[2])                  #Take out the seconds and place them in the variable 'sek'
    min = int(inTime[1])                    #take out the minutes and place them in the variable 'min'
    hour = int(inTime[0])                   #take out the hours and place them in the variable 'hour'

    totalsek = sek + min*60 + hour*3600     #calculate the total amount of seconds based on the variables above
    return totalsek                         #return the total amount of seconds

def serverSyncher(connectionSocket, recvWord, sendWord):        #Handshake from the server used in initial and final handshake
    while True:     #infinite loop untill 'break'
        connectionSocket.send(sendWord.encode())        #send the sendWord to client
        message = connectionSocket.recv(2048).decode()
        if message in recvWord:                         #if the message contains the wanted recvWord
            break                                       #exit the loop
    print(recvWord)                                     #print the wanted recvWord

def clientSyncher(client_sd, recvWord, sendWord):           #Handshake from the client used in initial and final handlshake
    while True:     #infinite loop
        message = client_sd.recv(2048).decode() #takes in a message from server if there are any
        if message in recvWord:                 #if message contains recvWord
            client_sd.send(sendWord.encode())   #send message back to server that client got it
            break                               #exit loop
    print(recvWord)                             #print wanted word
    

def intervalServer(goalTime, interval, format, serverip, port, connectionSocket): #If the server is run with intermittent updates
    start = clockToSek(time.ctime())    #Current time
    oldEnd = start                      #previous timecheck (used in display time intervals)
    end = start                         #timechecker for each interval
    recieved = 0                        #nr. of kilobytes per interval if used
    totalRecieved = 0                   # nr. of total kilobytes independent of interval
    flag=True                           #a check to only print once per interval
    rate = 0                            #in Mbps
    ratemultiplier=1                    #for converting to Mbps later

    while end-start < goalTime:                         #checks passed time less than set time
        if connectionSocket.recv(2048).decode() != "":  #if the socket recieved something
            if format == "MB":                          # if the client wants MB format
                recieved += 1/(1000)                    #Converts the recieved bytes into MB: 1KB / 1000 = 0.001MB
                totalRecieved += 1/(1000)               #adds the total
                ratemultiplier=1                        #for converting to Mbps later
            elif format == "KB":                        #if the client wants KB format
                recieved += 1                           #No conversion needed
                totalRecieved += 1                      #Adds the total
                ratemultiplier=1/1000                   #for converting to Mbps later
            elif format == "B":                         #if the client wants B format
                recieved += 1000                        #Converts the recieved bytes into B: 1KB * 1000 = 1000B
                totalRecieved += 1000                   #Adds the total
                ratemultiplier=1/1000000                #for converting to Mbps later
        if (end-start)%interval == 0 and interval != 1: #if the specified interval isn't 1 and the time is dividable by the specified interval
            if flag==True:                              #used to only print once per interval
                print(serverip,":",port,"\t",sekToClock(oldEnd-start),"-", sekToClock(end-start),"\t",math.trunc(recieved),format,"\t",round(rate, 2),"Mbps") #print the rate for this interval
                flag=False                              #used to only print once per interval
                oldEnd = end                            #update the new start-interval
                recieved = 0                            #reset the number of kilo-/mega-/bytes recieved for the next interval
        elif interval != 1:                             #if the interval isn't 1 and time is not dividable by the specified interval
            flag=True                                   #set the flag to True so that the next time the time is dividable by the interval, print the results.
            

        if interval == 1:           #if the specified interval is 1
            if (end-start)%2==0 and flag == True:       #if the time is an even number and flag is True
                print(serverip,":",port,"\t",sekToClock(oldEnd-start),"-", sekToClock(end-start),"\t",math.trunc(recieved),format,"\t",round(rate, 2),"Mbps") #print for current interval
                flag=False                              #used to only print once per interval
                oldEnd = end                            #update the new start-interval
                recieved = 0                            #reset the number of mega-/kilo-/bytes recieved for the next interval
            elif (end-start)%2==1 and flag == False:    #if the time is an odd number and the flag is False (supplementary to the previous if)
                print(serverip,":",port,"\t",sekToClock(oldEnd-start),"-", sekToClock(end-start),"\t",math.trunc(recieved),format,"\t",round(rate, 2),"Mbps") #print current interval
                flag=True                               #used to only print once per interval
                oldEnd = end                            #update the new start-interval
                recieved = 0                            #reset the number of kilobytes recieved for the next interval
            end = clockToSek(time.ctime())              #update the end time to check if the total duration has exceeded the specified timeframe
        
        if ((end-start)-(oldEnd-start)) == 0:           #Used for calculating rate, if the difference between an interval is 0
            rate = recieved*8*ratemultiplier/1          #calculate rate in Mbps, but divide by 1 instead of 0
        else:
            rate=recieved*8*ratemultiplier/((end-start+1)-(oldEnd-start))   #calculates rate in Mbps (Megabit per second)
        end = clockToSek(time.ctime())                                      #updating end-time
    #end of while-loop

    print(serverip,":",port,"\t",sekToClock(oldEnd-start),"-", sekToClock(end-start),"\t",math.trunc(recieved),format,"\t",round(rate, 2),"Mbps\n") #prints the final interval
    
    totalRate = totalRecieved*8*ratemultiplier/(end-start)      #calculate the total rate in Mbps
    print("--------------------------------------------------------------------------\n")   #pretty line
    print(serverip,":",port,"\t","0.0 -", sekToClock(end-start), "\t", math.trunc(totalRecieved),format,"\t", round(totalRate, 2), "Mbps\n") #prints the total duration calculations
  
def nonIntervalServer(goalTime, format, serverip, port, connectionSocket): #if the server is run without intermittent updates
    start = clockToSek(time.ctime())    #Current time
    end = start                         #timechecker for each interval
    recieved = 0                        #nr. of kilobytes per interval if used
    rate = 0                            #in Mbps
    ratemultiplier=1                    #for converting to Mbps later

    while end-start < goalTime:         #A loop lasting the specified duration
            msg = connectionSocket.recv(2048).decode()  #recieve something from the client
            if msg != "":                               #if the message doesn't contain nothing
                if format == "MB":                      #If the client wants to display transfer in Megabytes
                    recieved += 1/(1000)                #Converts the recieved bytes into MB: 1KB / 1000 = 0.001MB
                    ratemultiplier=1                    #for converting to Mbps later
                elif format == "KB":                    #If the client wants to display transfer in Kilobytes
                    recieved += 1                       #no conversion needed
                    ratemultiplier=1/1000               #for converting to Mbps later
                elif format == "B":                     #If the client wants to display transfer in Bytes
                    recieved += 1000                    #converts the recieved bytes into B: 1KB * 1000 = 1000B
                    ratemultiplier=1/1000000            #for converting to Mbps later
            end = clockToSek(time.ctime())              #updates the end-timer to calculate if the elapsed time has exceeded the intended timeframe
    rate=recieved*8*ratemultiplier/goalTime             #calculate rate in Megabit per second
    print(serverip,":",port,"\t0.0 -",sekToClock(end-start),"\t",math.trunc(recieved),format,"\t",round(rate, 2),"Mbps")    #prints the results

def intervalServerChecker(goalTime, interval, format, serverip, port, connectionSocket):    #used to determine if the client wants intermittent updates or not
    
    serverSyncher(connectionSocket, "Start", "Start")         #Synchs up the server to the client.

    if interval != 0:       #if the interval-parameter is not null
        intervalServer(goalTime, interval, format, serverip, port, connectionSocket)    #then the client wants intermittent updates, executes the corresponding function
    else:                   #if the interval-parameter is null
        nonIntervalServer(goalTime, format, serverip, port, connectionSocket)           #then the client does not want intermittent updates, executes the corresponding function

def intervalClient(goalTime, interval, format, serverip, port, client_sd, string): #If the client is run with intermittent-updates
    start = clockToSek(time.ctime())    #Current time
    oldEnd = start                      #previous timecheck (used in display time intervals)
    end = start                         #timechecker for each interval
    sent = 0                            #nr. of kilobytes per interval if used
    totalsent = 0                       #nr. of total kilobytes independent of interval
    flag=True                           #a check to only print once per interval
    rate = 0                            #in Mbps
    ratemultiplier=1                    #for converting to Mbps later
    
    while end-start < goalTime:                     #checks passed time less than set time
            client_sd.send(string.encode())         #sends a string of 1000 bytes
            if format == "MB":                      # if the client wants MB format
                sent += 1/(1000)                    #Converts the recieved bytes into MB: 1KB / 1000 = 0.001MB
                totalsent += 1/(1000)               #adds the total
                ratemultiplier=1                    #for converting to Mbps later
            elif format == "KB":                    #if the client wants KB format
                sent += 1                           #no conversion needed
                totalsent += 1                      #adds the total
                ratemultiplier=1/1000               #for converting to Mbps later
            elif format == "B":                     #if the client wants B format
                sent += 1000                        #converts the recieved bytes into B: 1KB * 1000 = 1000B
                totalsent += 1000                   #adds the total
                ratemultiplier=1/1000000            #for converting to Mbps later


            if (end-start)%interval == 0 and interval != 1: #For every interval bigger than 1
                if flag==True:                              #used to only print once per interval
                    print(serverip,":",port,"\t",sekToClock(oldEnd-start),"-", sekToClock(end-start),"\t",math.trunc(sent),format,"\t",round(rate, 2),"Mbps") #print results for current interval
                    flag=False                              #used to only print once per interval
                    oldEnd = end                            #update the new start-interval
                    sent = 0                                #reset the number of kilobytes sent for the next interval
            elif interval != 1:                             #when the time is not dividable by the interval, and the interval is not 1
                flag=True                                   #set the flag back to True so that the first instance of when the time is dividable by the interval gets used

            
            if interval == 1:   #if interval is 1
                if (end-start)%2==0 and flag == True:       #if the time is an even number, and the flag is True
                    print(serverip,":",port,"\t",sekToClock(oldEnd-start),"-", sekToClock(end-start),"\t",math.trunc(sent),format,"\t",round(rate, 2),"Mbps") #print the results for current interval
                    flag=False                              #used to only print once per interval
                    oldEnd = end                            #update the new start-interval
                    sent = 0                                #reset the number of kilobytes recieved for the next interval
                elif (end-start)%2==1 and flag == False:    #if the time is an odd number and the flag is False (supplementary to the previous if)
                    print(serverip,":",port,"\t",sekToClock(oldEnd-start),"-", sekToClock(end-start),"\t",math.trunc(sent),format,"\t",round(rate, 2),"Mbps") #print the results for the current interval
                    flag=True                               #used to only print once per interval
                    oldEnd = end                            #update the new start-interval
                    sent = 0                                #reset the number of kilobytes recieved for the next interval
                end = clockToSek(time.ctime())              #update the end time to check if the total duration has exceeded the specified timeframe
            if ((end-start)-(oldEnd-start)) == 0:           #checks if the interval is equal to 0
                rate = sent*8*ratemultiplier/1              #Calculates rate, but dividing by 1 instead of 0
            else:                                           #if the interval is not 0
                rate=sent*8*ratemultiplier/((end-start+1)-(oldEnd-start)) #calculates rate in Mbps (Megabit per second)
            end = clockToSek(time.ctime())                  #update the end-timer if interval is not 1
        #while loop-end
    print(serverip,":",port,"\t",sekToClock(oldEnd-start),"-", sekToClock(end-start),"\t",math.trunc(sent),format,"\t",round(rate, 2),"Mbps\n") #prints the last interval
    totalRate = totalsent*8*ratemultiplier/(end-start)      #calculates the total rate for the whole duration
    print("--------------------------------------------------------------------------\n") # pretty line
    print(serverip,":",port,"\t","0.0 -", sekToClock(end-start), "\t", math.trunc(totalsent),format,"\t", round(totalRate, 2), "Mbps\n")    #prints the results for the whole duration

def nonIntervalClient(goalTime, format, serverip, port, client_sd, string): #if the client is run without intermittent updates
    start = clockToSek(time.ctime())    #Current time
    end = start                         #timechecker for each interval
    sent = 0                            #nr. of kilobytes per interval if used
    rate = 0                            #in Mbps
    ratemultiplier=1                    #for converting to Mbps later

    while end-start < goalTime:             #checks if the duration has exceeded the total time specified
            client_sd.send(string.encode()) #send a total of 1000 bytes
            if format == "MB":              #If the client wants to display transfer in Megabytes
                sent += 1/(1000)            #Converts the recieved bytes into MB: 1KB / 1000 = 0.001MB
                ratemultiplier=1            #for converting to Mbps later
            elif format == "KB":            #If the client wants to display transfer in Kilobytes
                sent += 1                   #no conversion needed
                ratemultiplier=1/1000       #for converting to Mbps later
            elif format == "B":             #If the client wants to display transfer in Bytes
                sent += 1000                #converts the recieved bytes into B: 1KB * 1000 = 1000B
                ratemultiplier=1/1000000    #for converting to Mbps later
            end = clockToSek(time.ctime())  #updates the end-timer to calculate if the elapsed time has exceeded the intended timeframe
    rate=sent*8*ratemultiplier/goalTime     #calculate rate in Megabit per second
    print(serverip,":",port,"\t0.0 -",sekToClock(end-start),"\t",math.trunc(sent),format,"\t",round(rate, 2),"Mbps") #print the results

def intervalClientChecker(goalTime, interval, format, serverip, port, client_sd):   #Checks if the client wants intermittent updates or not
    
    clientSyncher(client_sd, "Start", "Start")      #Synchs up the client to the server

    
    string=""               #making a string consisting of 1000 bytes
    for i in range(951):    #exactly 1000 bytes
        string+="a"         #consisting of a's
    

    if interval != 0:       #if the interval parameter isn't 0
        intervalClient(goalTime, interval, format, serverip, port, client_sd, string)   #then the client wants intermittent updates, executes the corresponding function
    else:                   #if the interval parameter is 0
        nonIntervalClient(goalTime, format, serverip, port, client_sd, string)          #then the client does not want intermittent updates, executes the corresponding function

def trackerBytesServer(goalTime, interval, format, serverip, port, num, connectionSocket): #function for server when the number of bytes is specified
    serverSyncher(connectionSocket, "Start", "Start")       #synches up the server to the client
                                
    recieved = 0                                #Defining amount of KB sent
    ratemultiplier = 0                          #Used to calculate rate Mbps
    numberArray=re.findall("(\d+)", num)        #Finds the number in the string e.g. ['50']
    letterArray=re.findall("(\D+)", num)        #Finds the letter in the string e.g. ['M']

    tall = numberArray[0]                       #Making a variable out of the number e.g. tall == '50'
    tall = int(tall)                            #Making this variable an int to do algorithmics tall == 50

    if letterArray[0] == "B":                   #Tests if the amount sendt is in Bytes
        tall = tall/1000                        #Does the corresponding conversion
    elif letterArray[0] == "K":                 #Tests if the amount sendt is in Kilobytes
        tall = tall * 1                         #Does the corresponding conversion
    elif letterArray[0] == "M":                 #Tests if the amount sendt is in Megabytes
        tall = tall*1000                        #Does the corresponding conversion
    
    start = clockToSek(time.ctime())            #finds the current time
    end = start                                 #sets end to be equal starttime
    while True:                                 #an infinite loop
        msg = connectionSocket.recv(1024).decode()  #recieve something from the client
        if msg != "":                               #if the socket recieved something
            if "stop" in msg:                       #if the message contains the word 'stop'
                break                               #exit the loop
            if format == "MB":                      #if the client wants MB format
                recieved += 1/(1000)                #Converts the recieved bytes into MB: 1KB / 1000 = 0.001MB
                ratemultiplier=1                    #for converting to Mbps later
            elif format == "KB":                    #if the client wants KB format
                recieved += 1                       #no conversion needed
                ratemultiplier=1/1000               #for converting to Mbps later
            elif format == "B":                     #if the client wants B format
                recieved += 1000                    #Converts the recieved bytes into B: 1KB * 1000 = 1000B
                ratemultiplier=1/1000000            #for converting to Mbps later
            end = clockToSek(time.ctime())          #updates the end-timer to calculate if the elapsed time has exceeded the intended timeframe
        else:                                       #if the message contains nothing
            break                                   #also exit the loop, since the client wont send anymore data
    if end-start == 0:                              #if the transfer happend over a timespan equal to 0
        rate = math.trunc(recieved*8*ratemultiplier/1) #Calculate the rate using 1 instead of 0
    else:                                           #if the transfer tok more than 0 seconds
        rate=recieved*8*ratemultiplier/(end-start)  #calculate rate in Megabit per second
    print(serverip,":",port,"\t0.0 -",sekToClock(end-start),"\t",math.trunc(recieved),format,"\t",round(rate, 2),"Mbps") #print the results
     
def trackerBytesClient(num, format, client_sd): #function for client when the number of bytes is specified
    clientSyncher(client_sd, "Start", "Start")  #synching the client to the server
    
    sent = 0                                    #Defining amount of KB sent
    string=""                                   #Defining the string of 1000 bytes
    numberArray=re.findall("(\d+)", num)        #Finds the number in the string
    letterArray=re.findall("(\D+)", num)        #Finds the letter in the string

    tall = numberArray[0]                       #Making a variable out of the number
    tall = int(tall)                            #Making this variable an int to do algorithmics

    if letterArray[0] == "B":                   #Tests if the amount sendt is in Bytes
        tall = tall/1000                        #Does the corresponding conversion to KB
    elif letterArray[0] == "K":                 #Tests if the amount sendt is in Kilobytes
        tall = tall * 1                         #Does the corresponding conversion to KB
    elif letterArray[0] == "M":                 #Tests if the amount sendt is in Megabytes
        tall = tall*1000                        #Does the corresponding conversion to KB
 
    for i in range(951):                        #exactly 1000 bytes
        string+="a"                             #fills it with a's

    start = clockToSek(time.ctime())            #starts the clock
    while sent < tall:                          #while the amount sent is less than the number specified that the client want to send
        client_sd.send(string.encode())         #send the string of 1000 bytes
        sent += 1                               #Adds the amount sent to the total
    end = clockToSek(time.ctime())              #Stops timer


    if format == "MB":                          #Tests if the display-format should be Megabytes
        sent = sent/1000                        #Does the corresponding conversion to MB
        ratemultiplier=1                        #for converting to Mbps later
    elif format == "KB":                        #Tests if the display-format should be Kilobytes
        sent = sent*1                           #no conversion needed
        ratemultiplier=1/1000                   #for converting to Mbps later
    elif format == "B":                         #Tests if the display-format should be Bytes
        sent = sent*1000                        #Does the corresponding conversion to B
        ratemultiplier=1/1000000                #for converting to Mbps later
        
   
    client_sd.send("stop".encode())             #send a stop-signal to server to let it know that it should stop expecting packets

    if end-start == 0:                          #if the time duration is equal 0
        rate = (sent*8*ratemultiplier/1)        #calculate the rate using 1 instead of 0
    else:                                       #if the time duration is greater than 0
        rate=sent*8*ratemultiplier/(end-start)  #calculate rate in Megabit per second
    
    print(arguments.serverip,":",arguments.port,"\t0.0 -",sekToClock(end-start),"\t",math.trunc(sent),format,"\t",round(rate, 2),"Mbps") #prints the results

def handleClient(connectionSocket, addr):   #A client-handeler that can support mutliple clients
    print("Client connected with", arguments.serverip,"port",arguments.port)    #prints a message whenever a new client connects to the server

    data = connectionSocket.recv(2048)  #recieve message with pickle with client-options
    client_options = pickle.loads(data) #retrieves the client-options (unpacking)


    if client_options.num == None:      #if the client does not specify number of bytes that it wants to send
        intervalServerChecker(client_options.time, client_options.interval, client_options.format, arguments.serverip, arguments.port, connectionSocket) #execute the corresponding function
    else:                               #if the client specifies the number of bytes it wants to send
        trackerBytesServer(client_options.time, client_options.interval, client_options.format, arguments.serverip, arguments.port, client_options.num, connectionSocket) #execute the corresponding function

    serverSyncher(connectionSocket, "BYE", "ACK:BYE")   #send a "ACK:BYE"-message, expecting a "BYE"-message in return
    connectionSocket.close()                            #close the connection to this particular client

def server(arguments): #initial server function
    serverSocket = socket(AF_INET, SOCK_STREAM) #make a server socket
    try:
        serverSocket.bind((str(arguments.bind), arguments.port))    #Try to bind to a specific port and ip
    except:
        print("Bind failed - Wait and try again, or check if the IP-address is supported") #if the bind failed, report and error-message
        sys.exit()                                                                         #and exit the program
    
    serverSocket.listen(10)                                 #listen to any clients that wants to connect
    print("\nID\t\t\tInterval\tTransfer\tBandwidth\n")      #column headers
    while True: #an infinite loop
        connectionSocket, addr = serverSocket.accept()  #Try to accept incoming connection-requests
        thread.start_new_thread(handleClient, (connectionSocket, addr)) #make a new thread with this new client
        
def client(arguments):    #initial client function, this will run if the program is run in client mode (-c)
    id = 0              #for identifying a particular connection (used in parallel connections)
    connections = {}    #a list contianing all the client sockets
    while id < arguments.parallel:  #if the number of connections is less than the number of parallel connections specified
        connections["client_sd{0}".format(id)] = socket(AF_INET, SOCK_STREAM) 
        connections["client_sd{0}".format(id)].connect((str(arguments.serverip), int(arguments.port)))
            #https://stackoverflow.com/questions/6181935/how-do-you-create-different-variable-names-while-in-a-loop
            #data retrieved 11.04.2023
        
        data_string=pickle.dumps(arguments)                         #create a pickle with the client options 
        connections["client_sd{0}".format(id)].send(data_string)    #sends this pickle to the server
        id += 1                                                     #update the id now that a client is created
 
    print("\nID\t\t\tInterval\tTransfer\tBandwidth\n")              #prints the column headers

    
    if arguments.parallel > 1:                  #If the client wants a parallel connection
        client_connections = []                 #a list containing all the client connections
        for i in range(arguments.parallel):     #iterates through the number of parallel connections in a for-loop
            if arguments.num == None:           #if the client doesn't specify number of bytes
                line = Thread(target=intervalClientChecker, args=(arguments.time, arguments.interval, arguments.format, arguments.serverip, arguments.port, connections["client_sd{0}".format(i)])) #create a thread with the corresponding function
                client_connections.append(line)                 #put the thread in the list of connections
            else:
                line = Thread(target=trackerBytesClient, args=(arguments.num, arguments.format, connections["client_sd{0}".format(i)])) #create a thread with the corresponding function
                client_connections.append(line)                 #put the thread in the list of connections

        for i in client_connections:    #iterates through the list of connections
            i.start()                   #starts each thread
        for i in client_connections:    #iterates throuch the list of connections
            i.join()                    #makes the threads wait for each other
    else:                           #if the number of parallel connections is 1
        if arguments.num == None:   #and the client doesn't specify number of bytes
            intervalClientChecker(arguments.time, arguments.interval, arguments.format, arguments.serverip, arguments.port, connections["client_sd0"]) #execute the corresponding function without thread
        else:                       #if the client wants a specific number of bytes
            trackerBytesClient(arguments.num, arguments.format, connections["client_sd0"])  #execute the corresponding function without thread

    if arguments.parallel > 1:      #if there are parallel connections
        for i in range(arguments.parallel):                                         #iterate through every connection
            clientSyncher(connections["client_sd{0}".format(i)], "ACK:BYE", "BYE")  #Synch every connection to the server and send a BYE-message
    else:                           #if there are only one connection
        clientSyncher(connections["client_sd0"], "ACK:BYE", "BYE")  #synch this one connection to the server and send a BYE-message
       
    
    #closing of all client connections
    if arguments.parallel > 1:                              #if the number of parallel connections is greater than 1
        for i in range(arguments.parallel):                 #iterate through every connection
            connections["client_sd{0}".format(i)].close()   #close every connection
    else:                                                   #if the number of parallel connections is 1
        connections["client_sd0"].close()                   #close this single connection
    
parser = argparse.ArgumentParser(description="Optional Arguments")    #Title in the -h menu over the options available

#Adds options to the program
parser.add_argument("-s", "--server", action="store_true", help="Assigns server-mode")                                          #Server specific
parser.add_argument("-c", "--client", action="store_true", help="Assigns client-mode")                                          #Client specific
parser.add_argument("-p", "--port", default="8088", type=check_port, help="Allocate a port number")                             #Server and Client specific
parser.add_argument("-I", "--serverip", type=check_ip, default="127.0.0.1", help="Set IP-address of server from client")        #Client specific
parser.add_argument("-b", "--bind", type=check_ip, default="127.0.0.1", help="Set IP-address that client can connect to")       #Server specific
parser.add_argument("-f", "--format", default="MB", type=str, choices=("B", "KB", "MB"), help="Choose format for data size")    #Server and Client specific
parser.add_argument("-t", "--time", type=check_time, default=25, help="Choose time in seconds")                                 #Client specific
parser.add_argument("-i", "--interval", type=check_interval, default=0, help="Print statistics every z second")                 #Client specific
parser.add_argument("-P", "--parallel", type=check_parallel, default=1, help="Number of parallel connections")                  #Client specific
parser.add_argument("-n", "--num", type=check_bytes, help="Number of bytes you want to send")                                   #Client specific


arguments=parser.parse_args()       #gathers all the options into a list



if arguments.server or arguments.client:        #Finds out if the program is a server or a client
    if arguments.server and arguments.client:   #if the user has used both -s and -c
        print("Error: you cannont run this program in both server and client mode at the same time")    #Error-message cannot be both server and client
        sys.exit()                              #exits the program
    if arguments.server:                        #if -s is used
        print("-----------------------------------------------\n",
              "A simpleperf server is listening on port", arguments.port,       #print a header on the server side
              "\n-----------------------------------------------\n")
        server(arguments)                       #go into server mode
    if arguments.client:                        #if -c is used
        print("---------------------------------------------------------------\n",
              "A simpleperf client connecting to server", arguments.serverip, "port", arguments.port, #print a header on the client side
              "\n---------------------------------------------------------------\n")
        client(arguments)                       #go into client mode

else:       #if neither -c or -s is used
    print("Error: you must run either in server or client mode")    #print error you must choose
    sys.exit()          #exit program   
