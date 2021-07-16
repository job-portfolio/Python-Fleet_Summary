__author__ = 'rmarshall'

import time,pylab,numpy,csv
from selenium import webdriver
from datetime import datetime, timedelta
from matplotlib.dates import DateFormatter,MINUTES_PER_DAY,SEC_PER_DAY
from operator import itemgetter

"""--- ClockTime Functions ---"""
# Function: Read data from csv into list 'clocktime'
def readfile(fn,listObj):
    with open('U:/rmarshall/To Do/'+fn+'.csv','r') as fR:
        r=csv.reader(fR)

        # capture data into 'listObj'
        for row in r:
            listObj.append(row)
    return listObj


# Function: Make an element of each row in a list uppercase.
def uppercaseEle(listObj,ele):
    for x in range(len(listObj)):
        listObj[x][ele]=listObj[x][ele].upper()
    return listObj


# Function: Transform Driver Names into Reg No's so they're synonymous with skipsGraphData
def NameToReg(clocktime,drvToReg):
    for x in range(len(clocktime)):
        for row in drvToReg:
            if clocktime[x][0]==row[1]:
                clocktime[x][0]=row[0]
                break
    return clocktime


# Function: Create a list that is in a structure synonymous with skipsGraphData: Reg-data-date
def SynonymousStructue(clocktime,clockIN,clockOUT):
    r=1;dl=0                # r=1 because 0 would refer to Reg No rather than the clock-in time of Monday
    for x in range(6):
        for row in clocktime:
            if row[r]=='':                                              # standardising empty times with '00:00:00'
                clockIN.append([row[0],'00:00:00',datelist[dl]])
            else: clockIN.append([row[0],row[r],datelist[dl]])

            if row[r+1]=='':                                            # standardising empty times with '00:00:00'
                clockOUT.append([row[0],'00:00:00',datelist[dl]])
            else: clockOUT.append([row[0],row[r+1],datelist[dl]])

        r+=2
        dl+=1
    return clockIN,clockOUT


# Function: Datetime stamp to string date (DD/MM/YYYY)
def dateStampToStrDate(dateStamp):
    strDate=datetime.strftime(dateStamp,'%d/%m/%Y')
    return strDate


# Function: String date (DD/MM/YYYY) to Datetime stamp
def strDatetoDateStamp(strDate):
    datestamp=datetime.strptime(strDate,'%d/%m/%Y')
    return datestamp


# Function: Change datetime stamps to string dates.
def clockStamptoStr(clockIO):
    for x in range(len(clockIO)):
        clockIO[x][-1]=dateStampToStrDate(clockIO[x][-1])
"""---------------------------"""


# Function:  Place each registration into their own list
def createRegList(vehGD):
    regList=[]

    for x in vehGD[1:]:
        match=False

        for y in regList:
            if x[0]==y:
                match=True

        if match==False:
            regList.append(x[0])

    return regList


# Function:  1. Get all the regs that appear within 'VehData' list for the week (RegL).  2. Compare 'RegL' with each days data and see if any reg no is missing for that day.  3.  Add any missing reg to the list as a line of data where all the fields are zero.  4.  Sort updated list by Reg, then by Date; then pop headings row from end to the beginning
def stanardiseList(vehData):
    RegL=createRegList(vehData)
    missing=[]
    for datetimeObj in datelist:
        strDate=datetime.strftime(datetimeObj,'%d/%m/%Y')

        tempRegL=[]
        tempRegL.extend(RegL)

        for row in vehData[1:]:
            for x in range(len(tempRegL),0,-1):
                if tempRegL[x-1]==row[0] and strDate==row[-1]:
                    tempRegL.pop(x-1)

        # only runs if tempRegL has any elements left (i.e any registration that didn't exist for given instance of strDate
        for r in tempRegL:
            missing.append([[r, 'LIVE', '00:00', '00:00', '0', '00:00:00', '00:00:00', '00:00:00', '00:00:00', '0.0', 'Miles', '0.00', 'MPH', '0.0', 'MPH', '0', 'MPH',strDate]])

    # Add 'missing' list to SkipsData list (at the end)
    for row in missing:
        vehData.extend(row)

    # Capture the headings row into a variable
    tempheadings=[]
    for x in range(len(vehData)):
        if vehData[x][0]=='Registration':
            tempheadings=vehData.pop(x)
            break

    # Order list by Registration Number
    vehData.sort()

    # Order 'vehData' by date.  First: change string dates to datetimes; Second: perform the sort; Third: change datetimes back into string dates
    for x in range(len(vehData)):
        vehData[x][-1]=strDatetoDateStamp(vehData[x][-1])

    vehData=sorted(vehData,key=itemgetter(-1))

    for x in range(len(vehData)):
        vehData[x][-1]=dateStampToStrDate(vehData[x][-1])

    # Headings row will now be at the end the of list.  Move headings row to first row of the list.
    vehData[:0]=[tempheadings]

    return vehData


# Function: Implement clock-in time and clock-out time into VehsData list.
def clockIN_OUTintoSkipsData(VehsData,clockIO):
    for x in range(len(VehsData)):
        match=False
        for row in clockIO:
            if VehsData[x][0]==row[0] and VehsData[x][-1]==row[-1]:
                VehsData[x][-1:-1]=[row[1]]
                match=True
        if match==False:
            VehsData[x][-1:-1]=['00:00:00']


# Function: Check time is in the form 00:00:00, if they're any single digits then add a '0'.
def standardiseTime(time):
    mlist=[]
    mlist=time.split(':')
    for x in range(len(mlist)):
        if int(mlist[x])<10:
            mlist[x]='0'+mlist[x]
    time=':'.join(mlist)
    return time


# Function: Determine the time between clock-in and start time, end time and clock-out.
def clock_fleet_TimeDif(VehsData):
    for x in range(len(VehsData)):
        if x==0:
            continue    # skip heading row

        if VehsData[x][2]=='00:00' or VehsData[x][-3]=='00:00:00':      # if either empty then set clockIn field to zero
            VehsData[x][-3]='00:00:00'
        else:
            # Transform string times into time stamps (startTime,clockIn)
            startTime=datetime.strptime(VehsData[x][2],'%H:%M')
            clockIn=datetime.strptime(VehsData[x][-3],'%H:%M:%S')

            if startTime<clockIn:                                       # if driver turns on vehicle before clock in then set clockIn field to zero
                VehsData[x][-3]='00:00:00'
            else:
                # Find different between 'clock-in time' and 'start time', call the value morning.
                st=timedelta(hours=startTime.hour,minutes=startTime.minute, seconds=startTime.second)
                cIN=timedelta(hours=clockIn.hour,minutes=clockIn.minute, seconds=clockIn.second)
                morning=st-cIN

                # Transform time stamp into time string. (morning)
                hours, remainder = divmod(morning.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                morning=str(hours)+':'+str(minutes)+':'+str(seconds)

                # Check time is in the form 00:00:00, if they're any single digits then add a '0'.
                morning=standardiseTime(morning)

                # overwrite VehData element:  overwrite clock-in with morning.
                VehsData[x][-3]=morning


        if VehsData[x][3]=='00:00' or VehsData[x][-2]=='00:00:00':      # if either empty then set clockIn field to zero
            VehsData[x][-2]='00:00:00'
        else:
            # Transform string times into time stamps (endTime,clockOut)
            endTime=datetime.strptime(VehsData[x][3],'%H:%M')
            clockOut=datetime.strptime(VehsData[x][-2],'%H:%M:%S')

            if endTime>clockOut:                                       # if driver turns on vehicle before clock in then set clockIn field to zero
                VehsData[x][-2]='00:00:00'
            else:
                # Find different between 'clock-out time' and 'end time', call the value evening.
                et=timedelta(hours=endTime.hour,minutes=endTime.minute, seconds=endTime.second)
                cOUT=timedelta(hours=clockOut.hour,minutes=clockOut.minute, seconds=clockOut.second)
                evening=cOUT-et

                # Transform time stamp into time string. (evening)
                hours, remainder = divmod(evening.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                evening=str(hours)+':'+str(minutes)+':'+str(seconds)

                # Check time is in the form 00:00:00, if they're any single digits then add a '0'.
                evening=standardiseTime(evening)

                # overwrite VehData element:  overwrite clock-out with evening.
                VehsData[x][-2]=evening

    return VehsData


# Function:  Turn time strings into time stamps and then add the time stamps together
def addTimes(x,y='empty',z='empty',a='empty',b='empty'):
    d1=datetime.strptime(x,'%H:%M:%S'); dt1=timedelta(hours=d1.hour,minutes=d1.minute, seconds=d1.second)

    if y=='empty':
        totaltime=dt1
    elif z=='empty':
        d2=datetime.strptime(y,'%H:%M:%S'); dt2=timedelta(hours=d2.hour,minutes=d2.minute, seconds=d2.second)
        totaltime=dt1+dt2
    elif a=='empty':
        d2=datetime.strptime(y,'%H:%M:%S'); dt2=timedelta(hours=d2.hour,minutes=d2.minute, seconds=d2.second)
        d3=datetime.strptime(z,'%H:%M:%S'); dt3=timedelta(hours=d3.hour,minutes=d3.minute, seconds=d3.second)
        totaltime=dt1+dt2+dt3
    elif b=='empty':
        d2=datetime.strptime(y,'%H:%M:%S'); dt2=timedelta(hours=d2.hour,minutes=d2.minute, seconds=d2.second)
        d3=datetime.strptime(z,'%H:%M:%S'); dt3=timedelta(hours=d3.hour,minutes=d3.minute, seconds=d3.second)
        d4=datetime.strptime(a,'%H:%M:%S'); dt4=timedelta(hours=d4.hour,minutes=d4.minute, seconds=d4.second)
        totaltime=dt1+dt2+dt3+dt4
    else:
        d2=datetime.strptime(y,'%H:%M:%S'); dt2=timedelta(hours=d2.hour,minutes=d2.minute, seconds=d2.second)
        d3=datetime.strptime(z,'%H:%M:%S'); dt3=timedelta(hours=d3.hour,minutes=d3.minute, seconds=d3.second)
        d4=datetime.strptime(a,'%H:%M:%S'); dt4=timedelta(hours=d4.hour,minutes=d4.minute, seconds=d4.second)
        d5=datetime.strptime(b,'%H:%M:%S'); dt5=timedelta(hours=d5.hour,minutes=d5.minute, seconds=d5.second)
        totaltime=dt1+dt2+dt3+dt4+dt5
    return totaltime


# Function:  Create a list of- Reg, (Stop Time + Journey Time + Idle Time), (Stop Time + Idle Time), Idle Time.
def CreateGraphData(listObj,ReturnsList):
    a=0
    for x in range(len(listObj)):
        if x==0:
            continue

        Reg=listObj[x][0]

        ClockIn_ClockOut_Stop_Motion_Idle=addTimes(listObj[x][-3],listObj[x][-2],listObj[x][6],listObj[x][7],listObj[x][8])
        ClockOut_Stop_Motion_Idle=addTimes(listObj[x][-2],listObj[x][6],listObj[x][7],listObj[x][8])
        Stop_Motion_Idle=addTimes(listObj[x][6],listObj[x][7],listObj[x][8])
        Stop_Idle=addTimes(listObj[x][6],listObj[x][8])
        Idle=addTimes(listObj[x][8])

        ReturnsList.append([Reg,ClockIn_ClockOut_Stop_Motion_Idle,ClockOut_Stop_Motion_Idle,Stop_Motion_Idle,Stop_Idle,Idle])


# Function:  Separate vehGD list into  for different bars
def SeparateVehGD(vehGD,regList):
    ClockIn_ClockOut_Stop_Motion_Idle=[[] for i in range(len(regList))]     # list to hold Clock-in time + Clock-out time + Stop time + Journey Time + Idle Time
    ClockOut_Stop_Motion_Idle=[[] for i in range(len(regList))]             # list to hold Clock-out time + Stop time + Journey Time + Idle Time
    Stop_Motion_Idle=[[] for i in range(len(regList))]                      # list to hold Stop time + Journey Time + Idle Time
    Stop_Idle=[[] for i in range(len(regList))]                             # list to hold Stop Time + Idle Time
    Idle=[[] for i in range(len(regList))]                                  # list to hold Idle Time

    for x in vehGD:

        j=0
        for y in regList:
            if x[0]==y:
                ClockIn_ClockOut_Stop_Motion_Idle[j].append(str(x[1]))
                ClockOut_Stop_Motion_Idle[j].append(str(x[2]))
                Stop_Motion_Idle[j].append(str(x[3]))
                Stop_Idle[j].append(str(x[4]))
                Idle[j].append(str(x[5]))
            j+=1
    return ClockIn_ClockOut_Stop_Motion_Idle,ClockOut_Stop_Motion_Idle,Stop_Motion_Idle,Stop_Idle,Idle


# Function:  Represent a string time in seconds.
def convert(s):
    h,m,s = map(float, s.split(':'))
    return h/24. + m/MINUTES_PER_DAY + s/SEC_PER_DAY


# Function:  Change time strings into seconds + 733681
def getSeconds(listObj):
    for x in range(0,len(regList)):
        for y in range(0,NumberOfDays):
            listObj[x][y]=convert(listObj[x][y])+733681         # each element equal itself (converted into seconds + 733681)
    return listObj


# Function:  Create graph
def createGraph(fig,datelist,regList,veh):
    # list for xticklabels
    xticklabels=[]
    for x in range(len(datelist)):
        xticklabels.extend(regList)

        # don't add a space at the very end. (so graph finishes at the last bar and not at a space after the last bar).
        if x!=len(datelist)-1:
            xticklabels.append(' ')

    # turn datelist datetime stamps into date strings and store in new list 'datelistStr'
    datelistStr=[]
    for v in datelist:
        ds=datetime.strftime(v,'%d.%m.%Y')
        datelistStr.append(ds)


    """
        NOTE: bars are grouped by date. e.g all regs for 06.01.2014 are grouped together.

        w:
            The comfortable bar width when a registration number is a tick label is 0.35
        ind:
            Each item in regList represents a width of 0.35 on the chart.
            The starting position of a new group thus needs to be:
            (the length of the regList * width) + width
            where 0.35 represent a cushion of space (1 bar width wide) between the end of one group and the beginning of another group.
        xtickPosition:
            The position of each tick must be at the central point between the start of a bar and the end of a bar; thus, width/2 .
            'ind' represents the starting location of each group of bars
            arange(start,stop,step):
            start: min(ind)+w/2         -first groups starting position + bar width/2
            stop:  max(ind)+r*w         -last groups starting position + number of reg no's * bar width
            step:  w                    -bar width
        x2tickPosition:
            The position of each tick must be central to the group of bars.
            arange(start,stop,step):
            start: min(ind)+(r*w)/2     -first groups starting position + (length of the group of bars x width) / 2
            stop:  max(ind)+r*w         -last groups starting position + (length of the group of bars x width)
            step:  r*w+w                -(lenth of group of bars x width) + width
        x-axis limits:
            xmax=max(ind)+r*w           -last groups starting position + length of the group of bars x width
    """

    r=len(regList)                                                          # No of vehicles
    w=0.35                                                                  # bar width

    ind=numpy.arange(0,len(datelist)*(r*w+w),r*w+w)                         # the starting x location of each group
    xtickPosition=numpy.arange(min(ind)+w/2, max(ind)+r*w, w)               # position of the bottom x-axis ticks
    x2tickPosition=numpy.arange(min(ind)+(r*w)/2,max(ind)+r*w,r*w+w)        # position of the top x-axis ticks
    ax=fig.add_subplot(111)
    ax2=ax.twiny()

    # Create a 3 bars (one infront of each other) for each Reg no.
    for x in range(len(regList)):
        bar1=ax.bar(ind+x*w,ClockIn_ClockOut_Stop_Motion_Idle[x],facecolor='#B60354',width=w)
        bar2=ax.bar(ind+x*w,ClockOut_Stop_Motion_Idle[x],facecolor='#E59400',width=w)
        bar3=ax.bar(ind+x*w,Stop_Motion_Idle[x],facecolor='#B0E0E6',width=w)
        bar4=ax.bar(ind+x*w,Stop_Idle[x],facecolor='#777777',width=w)
        bar5=ax.bar(ind+x*w,Idle[x],facecolor='#9ACD32',width=w)

    # additions
    ax.legend((bar1[0],bar2[0],bar3[0],bar4[0],bar5[0]),('Clock-in Time','Clock-out time','Journey Time','Stop Time','Idle Time'))

    # y-axis
    ax.yaxis_date()
    ax.yaxis.set_major_formatter(DateFormatter('%H:%M'))
    ax.set_ylim(bottom = 733681, top = 733681.99)            # a necessary factor in removing fromordinal <= error
    ax.set_ylabel('Accountable Time')

    # x-axis
    ax.set_xlabel('Registrations')
    ax.set_xticklabels(xticklabels,rotation=35)
    ax.set_xticks(xtickPosition)
    ax.set_xlim(xmax=max(ind)+r*w)

    # x-axis (top)
    ax2.set_xlabel('\n\nDates')
    ax2.set_xticklabels(datelistStr)
    ax2.set_xticks(x2tickPosition)
    ax2.set_xlim(xmax=max(ind)+r*w)

    # figure
    fig.tight_layout()
    fig.suptitle(veh,fontsize=15)


# Function:  Save figures
def saveFigure():
    fn=datetime.strftime(datetime.today(),'%Y.%m.%d - %H.%M.%S ')
    path='U:/rmarshall/Reporting/Charts/Fleet Day Summary/'
    fig1.savefig(path+fn+'Skips.png')
    fig2.savefig(path+fn+'Tippers.png')


# Initialise the webdriver
chromeOps=webdriver.ChromeOptions()
chromeOps._binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
chromeOps._arguments = ["--enable-internal-flash"]
browser = webdriver.Chrome("C:\\Program Files\\Google\\Chrome\\Application\\chromedriver.exe", port=4445, chrome_options=chromeOps)
time.sleep(3)

# Login to Road Angel
browser.get('http://www.mmgt.co.uk/')           # open login page
browser.find_element_by_id('Login1_UserName').send_keys('ewd')
browser.find_element_by_id('Login1_Password').send_keys('letmein')
browser.find_element_by_id('Login1_LoginButton').click()


"""--- ClockTime Variables ---"""
clocktime=[]                                    # hold data from csv file
drvToReg=[]                                     # hold data: Driver Name -(corresponding to)- Reg No.
clockOUT,clockIN=[[] for i in range(2)]         # hold clock-out data is a form synonymous with skipsGraphData: Reg-data-date
"""---------------------------"""


"""--- User Input and datelist Section ---"""
# Generate user input box.  Userinput form- 'dd/mm/yyyy dd/mm/yyyy'.  Turn the two string dates into two date stamps, and use timedelta to calculate the number of days between the values.
datelist=[]
userInput=input("Enter Start and End Date: ")

sDay,sMonth,sYear=map(int,userInput[0:10].split('/'))           # start day; start month; start year.  split function with results wrapped as ints
eDay,eMonth,eYear=map(int,userInput[11:].split('/'))            # end day; end month; end year.  split function with results wrapped as ints

DTstartDate=datetime(sYear,sMonth,sDay)                         # int wrapping so '01' becomes 1.  1 required to be accepted as datetime arguement.
DTendDate=datetime(eYear,eMonth,eDay)                           # int wrapping so '01' becomes 1.  1 required to be accepted as datetime arguement.

NumberOfDays=(DTendDate+timedelta(days=1)-DTstartDate).days     # obtain number of days from 'DTstartDate' to 'DTendDate'


# Create a list of datetimes within the specified date range value 'NumberOfDays'
for x in range(0,NumberOfDays):
    datelist.append(DTstartDate+timedelta(days=x))
"""---------------------------------------"""


"""--- ClockTime Data Processing ---"""
readfile('ClockTime',clocktime)         # read data from csv
readfile('Driver to Reg',drvToReg)      # read data: Driver Name -(corresponding to)- Reg No.

clocktime=clocktime[2:]     # remove headings

uppercaseEle(clocktime,0)    # Make an element of each row in a clocktime uppercase.
uppercaseEle(drvToReg,1)     # Make an element of each row in a drvToReg uppercase.

clocktime=NameToReg(clocktime,drvToReg)         # driver name to reg

clockIN,clockOUT=SynonymousStructue(clocktime,clockIN,clockOUT)     # turn clocktime list structure into a structure synonymous with skipsGraphData for easy use by CreateGraphData():

clockStamptoStr(clockIN)
clockStamptoStr(clockOUT)
"""---------------------------------"""


# Create two lists to hold skip and tipper data from the html table.  Make a datetime object their initial value (not necessary but will help confirm that datetimeObj matches the date of the screen scraped)
skipsTableData=[];tippersTableData=[]
for datetimeObj in datelist:
    skipsTableData.append([datetimeObj])
    tippersTableData.append([datetimeObj])


# Scrape pages:  Browser to enter Skip and Tipper Fleet Day Summary Report for all dates in 'datelist'.  Extract Skip and Tipper data from table in browser.
ind=-1
for datetimeObj in datelist:
    ind+=1
    strDate=datetime.strftime(datetimeObj,'%d/%m/%Y')

    # Scrape skip data
    print('Scraping Skip '+ strDate)
    browser.get('http://www.mmgt.co.uk/HTMLReport.aspx?ReportName=Fleet%20Day%20Summary%20Report&ReportType=7&CategoryID=4923&Startdate='+strDate+'&email=false')
    time.sleep(10)

    a=1
    while True:
        try:
            el=browser.find_element_by_xpath('//*[@id="ReportHolder"]/table/tbody/tr['+str(a)+']').text
            skipsTableData[ind].append(el)
            a+=1
        except:
            break

    # Scrape tipper data
    print('Scraping Tipper '+ strDate)
    browser.get('http://www.mmgt.co.uk/HTMLReport.aspx?ReportName=Fleet%20Day%20Summary%20Report&ReportType=7&CategoryID=4924&Startdate='+strDate+'&email=false')
    time.sleep(10)

    a=1
    while True:
        try:
            el=browser.find_element_by_xpath('//*[@id="ReportHolder"]/table/tbody/tr['+str(a)+']').text
            tippersTableData[ind].append(el)
            a+=1
        except:
            break

    time.sleep(5)


# Create a table of skips data.  (skipsTableData is in the format of a single string which contains all the different fields of data separated by a space).
SkipsData = [['Registration','Device Type','Start Time','End Time','No. Stops','Lapse Time','Stopped Time','Time in Motion',\
             'Idle Time','Total Distance Covered','Average Speed (Inc Idle)','Average Speed (Exc Idle)','Top Speed']]
i=-1
for row in skipsTableData:
    endofVehData = len(row)-3
    i+=1
    for x in range(3,endofVehData):
        #print(row[x])
        splitStr=row[x].split(' ')                                      # each vehicles daily data is held in one string, split it at space.
        splitStr.append(datetime.strftime(datelist[i],'%d/%m/%Y'))      # add date in string format to end of 'splitStr'
        SkipsData.append(splitStr)


# Create a table of tippers data.  (tippersTableData is in the format of a single string which contains all the different fields of data separated by a space).
TippersData = [['Registration','Device Type','Start Time','End Time','No. Stops','Lapse Time','Stopped Time','Time in Motion',\
             'Idle Time','Total Distance Covered','Average Speed (Inc Idle)','Average Speed (Exc Idle)','Top Speed']]
i=-1
for row in tippersTableData:
    endofVehData=len(row)-3
    i+=1
    for x in range(3,endofVehData):
        splitStr=row[x].split(' ')                                      # each vehicles daily data is held in one string, split it at space.
        splitStr.append(datetime.strftime(datelist[i],'%d/%m/%Y'))      # add date in string format to end of 'splitStr'
        TippersData.append(splitStr)

# ISOLATION:  These print outs allow the user to take 'SkipsData' and 'TippersData' from the 'Run' tab and place them as list in 'Fleet Summary Isolation.py'.  This is used when the table data contents contains an error held in Road Angels database.
print('SkipsData:')
for row in SkipsData:print(row)
print('TippersData')
for row in TippersData:print(row)


# Standardise skips and tippers data:  Add any missing reg's to the list as a data row specifying the Reg No. followed by 0 values and ending in the date.  Then order list by Reg then Date.
SkipsData=stanardiseList(SkipsData)
TippersData=stanardiseList(TippersData)


clockIN_OUTintoSkipsData(SkipsData,clockIN)         # add clock-IN time into SkipsData
clockIN_OUTintoSkipsData(SkipsData,clockOUT)        # add clock-OUT time into SkipsData
clockIN_OUTintoSkipsData(TippersData,clockIN)       # add clock-IN time into TippersData
clockIN_OUTintoSkipsData(TippersData,clockOUT)      # add clock-OUT time into TippersData

SkipsData[0].extend(['Clock-in Time','Clock-out Time'])      # amend heading so that heading matches data
TippersData[0].extend(['Clock-in Time','Clock-out Time'])    # amend heading so that heading matches data

SkipsData=clock_fleet_TimeDif(SkipsData)            # Determine the time between clock-in and start time, end time and clock-out.
TippersData=clock_fleet_TimeDif(TippersData)        # Determine the time between clock-in and start time, end time and clock-out.


# Create a list- Element[0]=Stop Time+Time in Motion+Idle Time; Element[1]=Stop Time+Idle Time; Element[2]=Idle Time
skipsGraphData, tippersGraphData = [[['Registration','clockIn+clockOut+Stop+Motion+Idle','clockOut+Stop+Motion+Idle','Stop+Motion+Idle','Stop+Idle','Idle']] for i in range(2)]
CreateGraphData(SkipsData,skipsGraphData)
CreateGraphData(TippersData,tippersGraphData)

skipsGD=skipsGraphData[1:]          # remove headings
tippersGD=tippersGraphData[1:]      # remove headings


# _/ skips and tipper chart creating (split starts here) \_ #
# -- Skips -- #
regList=createRegList(SkipsData)
ClockIn_ClockOut_Stop_Motion_Idle,ClockOut_Stop_Motion_Idle,Stop_Motion_Idle,Stop_Idle,Idle=SeparateVehGD(skipsGD,regList)

ClockIn_ClockOut_Stop_Motion_Idle=getSeconds(ClockIn_ClockOut_Stop_Motion_Idle)
ClockOut_Stop_Motion_Idle=getSeconds(ClockOut_Stop_Motion_Idle)
Stop_Motion_Idle=getSeconds(Stop_Motion_Idle)
Stop_Idle=getSeconds(Stop_Idle)
Idle=getSeconds(Idle)

fig1=pylab.figure(figsize=(20,8))
createGraph(fig1,datelist,regList,'Skips - Fleet Summary Sheet')
# ----------- #

# -- Tippers -- #
regList=createRegList(TippersData)
ClockIn_ClockOut_Stop_Motion_Idle,ClockOut_Stop_Motion_Idle,Stop_Motion_Idle,Stop_Idle,Idle=SeparateVehGD(tippersGD,regList)

ClockIn_ClockOut_Stop_Motion_Idle=getSeconds(ClockIn_ClockOut_Stop_Motion_Idle)
ClockOut_Stop_Motion_Idle=getSeconds(ClockOut_Stop_Motion_Idle)
Stop_Motion_Idle=getSeconds(Stop_Motion_Idle)
Stop_Idle=getSeconds(Stop_Idle)
Idle=getSeconds(Idle)

fig2=pylab.figure(figsize=(20,8))
createGraph(fig2,datelist,regList,'Tippers - Fleet Summary Sheet')
# ------------- #


saveFigure()            # save both skips and tippers figures


pylab.show()