'''

██████╗░██╗░░██╗░█████╗░███████╗███╗░░██╗██╗██╗░░██╗  ██╗███╗░░░███╗░█████╗░░██████╗░██╗███╗░░██╗░██████╗░
██╔══██╗██║░░██║██╔══██╗██╔════╝████╗░██║██║╚██╗██╔╝  ██║████╗░████║██╔══██╗██╔════╝░██║████╗░██║██╔════╝░
██████╔╝███████║██║░░██║█████╗░░██╔██╗██║██║░╚███╔╝░  ██║██╔████╔██║███████║██║░░██╗░██║██╔██╗██║██║░░██╗░
██╔═══╝░██╔══██║██║░░██║██╔══╝░░██║╚████║██║░██╔██╗░  ██║██║╚██╔╝██║██╔══██║██║░░╚██╗██║██║╚████║██║░░╚██╗
██║░░░░░██║░░██║╚█████╔╝███████╗██║░╚███║██║██╔╝╚██╗  ██║██║░╚═╝░██║██║░░██║╚██████╔╝██║██║░╚███║╚██████╔╝
╚═╝░░░░░╚═╝░░╚═╝░╚════╝░╚══════╝╚═╝░░╚══╝╚═╝╚═╝░░╚═╝  ╚═╝╚═╝░░░░░╚═╝╚═╝░░╚═╝░╚═════╝░╚═╝╚═╝░░╚══╝░╚═════╝░

'''
from builtins import WindowsError  # type: ignore
from pycomm3 import CommError
from stringListBuilder import *
from PLC_ops import PLC_ops as plc 
from keyenceOps import *
from keyenceComs import *
from keyenceString import keyenceString as kString
from csvCreate import csvCreate as csv 
from write_part_results import write_part_results as resWriter
import os
from threading import Thread
##################### LOGGING ###########################
import time
import logging
from datetime import date, datetime
from inspect import currentframe, getframeinfo
#########################################################
frame = getframeinfo(currentframe())
path = frame.filename
filename = path.split("/")[-1]
fn = filename.rsplit(".")[0]
today = date.today().strftime("%a-%b-%d-%Y")
now = datetime.now().strftime("%I:%M:%S.%f")[:-3]
logging.basicConfig(level=logging.INFO, filename = f"{today}.log",filemode = "w",
format = f"{now}-%(levelname)s-%(message)s")
logger = logging.getLogger(fn)
#Create File handler
handler = logging.FileHandler(f"{fn}-{today}.log")
#Create logging format
formatter = logging.Formatter(f"{now}-{fn}-%(levelname)s-%(message)s")
#Add format to handler
handler.setFormatter(formatter)
#add the file handler to the logger
logger.addHandler(handler)
### END LOGGING ###

Phoenix = open('Phoenix.txt').read()
print(Phoenix)
currStage = 0
partResults = ''
mn1 = '14'
mn2 = '15'

def resetChecker(mn):
    bool = plc(mn).checkReset()
    if(bool == True):
        plc(mn).flush_PLC()
        plc(mn).writeResetTagFaultedTagsLOW()
        cycle(mn)
    else:
        pass
def PUN_toString(num):
    rtn = ''
    for i in range(len(num)):
        rtn += chr(num[i])
    return rtn    


#Function to be looped twice for each machineNumber 
def cycle(mn: str):
    PLC = plc(mn)
    knString = kString(mn)
    try: 
        PLC.clearFLT_plc()
        if(mn == '14'):
            pass
        else:
            print("PLC connected\n")
    except CommError as err: #WINDOWS 
        print("PLC commError")
        logger.warning(err)
    except TimeoutError as err:
        print("PLC TimeoutError")
        logger.warning(err)
    while(True):
        try:
            PLC.flush_PLC()
            PLC_results = PLC.read_from_plc()
            #resetRead = PLC.readRESET()
            #RESET = resetRead[1]
            #if(RESET == True):
            global currStage
            #currStage = 0 
            PLC.writeResetTagFaultedTagsLOW()
            #END IF 
            if(currStage == 0):
                print(f'\n({mn})START stage ZERO...\n')
                resetChecker(mn)
                PLC.writeBusyDoneLOW() #Busy,Done,Pass,Fail ->False
                PLC.writeReadyHIGH() #writeReadyHigh
                print(f"\n({mn}) Waiting for Load Program...\n")
                while(PLC_results['LoadProgram'][1] == False):
                    print('\r~\r',end='')
                    PLC_results = PLC.read_from_plc()
                    if(PLC_results['LoadProgram'][1] == True):
                        print(f"\n({mn})Part Program:",PLC_results['PartProgram'][1])
                        part_result = PLC_results['PartProgram'][1]
                        break
                    time.sleep(0.005)
                    #END IF
                #END WHILE
                PLC_results = PLC.read_from_plc()
                PLC.writeReadyLOW()
                PartType = PLC_results['PartType'][1]
                print(f'\nPart Type after LOAD {PartType}\n')
                logger.info(f'\nPart Type after LOAD {PartType}\n')
                #keyenceString = keyenceString(mn)
                part_result = PLC_results['PartProgram'][1]
                keyenceString = knString.setKeyenceString(part_result,PartType)
                
                #####
                pun_str = PUN_toString(PLC_results['PUN'][1]) #int list to string function
                date_info = [PLC_results['Month'][1],PLC_results['Day'][1],PLC_results['Hour'][1],PLC_results['Minute'][1],PLC_results['Second'][1]]
                dateInfo_strList = [str(i) for i in date_info]
                for i in range(0,len(dateInfo_strList)):
                    if(len(dateInfo_strList[i]) < 2 ):
                        dateInfo_strList[i] = '0' + dateInfo_strList[i]
                keyenceStr_date = str(pun_str[10:22])+'_'+str(PLC_results['Year'][1])+'-'+str(dateInfo_strList[0]) + '-' + str(dateInfo_strList[1]) + '-' + str(dateInfo_strList[2]) + '-' + str(dateInfo_strList[3]) + '-' + str(dateInfo_strList[4]) + '_' + str(keyenceString)
                print(f"\n({mn})LOADING: {keyenceStr_date}\n")
                logger.info(f"\n({mn})LOADING: {keyenceStr_date}\n")
                while(True):
                    data = keyenceOps(mn).LOAD_keyence(str(PLC_results['PartProgram'][1]), keyenceStr_date)
                    if data == True:
                        break
                #PLC.flush_PLC()
                PLC_results = PLC.read_from_plc()
                #PLC_temp = PLC_results
                #PLC.write_plc(PLC_results)
                #print(PLC_results)
                PLC.writeReadyHIGH()
                currStage += 1
            #END IF, END STAGE 0
            #BEGIN ELIF, START STAGE 1 Program Start & End Sequence
                
            elif(currStage == 1):
                print(f'\n({mn}) Entering stage 1...\n')
                resetChecker(mn)
                while(PLC_results['StartProgram'][1] == False):
                    PLC.write_plc(PLC_results)
                    print('\r#\r',end='')
                    PLC_results = PLC.read_from_plc()
                    #print(PLC_results)
                    
                    if(PLC_results['StartProgram'][1] == True):
                        print(f'\n({mn})\nProgram Started \n')
                        break
                    time.sleep(0.005)
                    #END IF
                #END WHILE
                    
                while(True):
                    try:
                        data = keyenceOps(mn).TRIG_keyence()
                        if(data == True):
                            break
                    except TimeoutError as err:
                        print(f'({mn}) TriggerKeyence timeout error PhoenixFltCode : 2',err)
                            # plc.write(
                            # ('Program:HM1450_VS' + machine_num + '.VPC1.I.PhoenixFltCode', 2),
                            # ('Program:HM1450_VS' + machine_num + '.VPC1.I.Faulted', True))
                        break
                PLC.writeReadyLOW()
                PLC.writeBusy(True)
                while(True):
                    if(PLC.monitor_endScan() == True):
                        print(f'\nEnd Scan\n')
                        break
                
                try:
                    keyenceOps(mn).EXIT_keyence()
                    print(f'\nExit\n')
                              
##                '''while(True):
##                    if(keyenceOps(mn).monitor_KeyenceNR() == False):
##                        print(f'\nkeyenceNRn\')
##                        break'''
                except TimeoutError as err:
                    print(f'({mn}) TriggerKeyence timeout error PhoenixFltCode : 3',err)
                    # plc.write(
                    # ('Program:HM1450_VS' + machine_num + '.VPC1.I.PhoenixFltCode', 3),
                    # ('Program:HM1450_VS' + machine_num + '.VPC1.I.Faulted', True)
                
                keyenceResults = keyenceOps(mn).keyence_toPLC()
                print('results sent: ', keyenceResults)
                PLC.writeBusy(False)
                PLC.writeDone(True)
                scan_duration = 0
                csv(mn, PLC_results, keyenceResults, keyenceStr_date, scan_duration).create()
                
                #global partResults
                #partResults = resWriter(mn, partResults, PLC_results, keyenceStr_date, scan_duration ).gerrybudd()
                keyenceComs(mn).message_Keyence('MW,#PhoenixControlContinue,1\r\n')
                currStage += 1
                
            elif(currStage == 2):
                print('\nEntering Stage 2...\n')
                resetChecker(mn)
                while (True):
                    if(PLC_results['EndProgram'][1] == True):
                        PLC.writePassFail_LOW()
                        PLC.writeDone(False)
                        PLC.flush_PLC()
                        print('flushing PLC')
                        currStage = 0
                        break
                    else:
                        #print('waiting for end program')
                        time.sleep(.05)

                    
##                if(PLC_results['EndProgram'][1] == False and doneCheck[1] == False):
##                    PLC.writeReadyHIGH()
##                    currStage = 0
        

    ###################################
    #File Cleanup( Name: def Dylan() )?
    ###################################          
    
        except TimeoutError as err:#verify for windows 
            print("PLC communication TimeoutError")
            logger.warning(err)
        except CommError as err: #verify for windows 
            print("PLC communication error")
            logger.warning(err)
        
#cycle('mn1')

def getListOfFiles(dirName):
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
    return allFiles

def logCleaner(dirName):
    allFiles = getListOfFiles(dirName) #puts file names into list
    for i in allFiles:
        bDay = os.path.getmtime(i)
        now = datetime.datetime.now()  # type: ignore
        now = datetime.datetime.timestamp(now)*1000  # type: ignore
        age = (float(bDay)-float(now))/(60*60*24) #time between file creation and current time
        if age > 1209600:
            try:
                os.remove(i) #removes files older than two weeks
            except WindowsError as e:
                print('Attempt to remove old log files gave ', e)
        else:
            pass

def thread_one(mn):
    PLCops = PLC_ops(mn)
    t1 = Thread(target = cycle, args = (mn,))
    t2 = Thread(target = PLCops.heartbeat_PLC, args = (mn,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

def thread_two(mn):
    PLCops = PLC_ops(mn)
    t1 = Thread(target = cycle, args = (mn,))
    t2 = Thread(target = PLCops.heartbeat_PLC, args = (mn,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

def main():
    print(f"Starting threads for ({mn1}) & ({mn2})")
    t1 = Thread(target=thread_one,args=(mn1,))
    t2 = Thread(target=thread_two,args=(mn2,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ ==  "__main__":
    while(True):
        main()