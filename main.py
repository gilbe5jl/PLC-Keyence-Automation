'''
#########################################################
# PLC---Keyence
Python program for communicating with an Allen-Bradley PLCs using Ethernet/IP 
and Keyence Vision System Controllers using Ethernet/IP.
The development for this project was aimed at reading/writing data inside an 
Allen-Bradley PLC and sending that data to a Keyence Vision System Controller.
PLCs can be used to control heavy or dangerous equipment, this code is provided "as is" 
and makes no guarantees on its reliability in a production environment. 
This code is being provided as an example of my professional experience and should not be copied or distrubuted. 

Copyright (C) 2022 Jalen Gilbert - All Rights Reserved
You may not use, distribute or modify this code. 
#####################################################
'''
from builtins import WindowsError  
from pycomm3 import CommError
#########
from PLC_ops import PLC_ops as plc 
from keyenceOps import *
from keyenceComs import *
from keyenceString import keyenceString as kString
from csvCreate import csvCreate as csv 
########
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
handler = logging.FileHandler(f"{fn}-{today}.log")
formatter = logging.Formatter(f"{now}-{fn}-%(levelname)s-%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
### END LOGGING ###

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

def cycle(mn: str):
    PLC = plc(mn)
    knString = kString(mn)
    try: 
        PLC.clearFLT_plc()
        if(mn == '14'):
            pass
        else:
           ##########
    except CommError as err: 
    ######
    except TimeoutError as err:
       #######
        logger.warning(err)
    while(True):
        try:
            PLC.flush_PLC()
            PLC_results = PLC.read_from_plc()
            global currStage
            PLC.writeResetTagFaultedTagsLOW()
            #END IF 
            if(currStage == 0):
                resetChecker(mn)
                PLC.writeBusyDoneLOW() 
                PLC.writeReadyHIGH() 
                print(f"\n({mn}) Waiting for Load Program...\n")
                while(PLC_results['LoadProgram'][1] == False):
                   ##########
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
                part_result = PLC_results['PartProgram'][1]
                keyenceString = knString.setKeyenceString(part_result,PartType)
                pun_str = PUN_toString(PLC_results['PUN'][1]) #int list to string function
                date_info = [PLC_results['Month'][1],PLC_results['Day'][1],PLC_results['Hour'][1],PLC_results['Minute'][1],PLC_results['Second'][1]]
                dateInfo_strList = [str(i) for i in date_info]
                for i in range(0,len(dateInfo_strList)):
                    if(len(dateInfo_strList[i]) < 2 ):
                        dateInfo_strList[i] = '0' + dateInfo_strList[i]
                keyenceStr_date = str(pun_str[10:22])+'_'+str(PLC_results['Year'][1])+'-'+str(dateInfo_strList[0]) + '-' + str(dateInfo_strList[1]) + '-' + str(dateInfo_strList[2]) + '-' + str(dateInfo_strList[3]) + '-' + str(dateInfo_strList[4]) + '_' + str(keyenceString)
            ###########
                logger.info(f"\n({mn})LOADING: {keyenceStr_date}\n")
                while(True):
                    data = keyenceOps(mn).LOAD_keyence(str(PLC_results['PartProgram'][1]), keyenceStr_date)
                    if data == True:
                        break
                PLC_results = PLC.read_from_plc()
                currStage += 1
            #END IF, END STAGE 0
            #BEGIN ELIF, START STAGE 1 Program Start & End Sequence
            elif(currStage == 1):
                print(f'\n({mn}) Entering stage 1...\n')
                resetChecker(mn)
                while(PLC_results['StartProgram'][1] == False):
                    PLC.write_plc(PLC_results)
                    
                    PLC_results = PLC.read_from_plc()
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
                       ###############
                        break
                        ######
                PLC.writeBusy(True)
                while(True):
                    if(PLC.monitor_endScan() == True):
                     #########
                        break
                try:
                    keyenceOps(mn).EXIT_keyence()
                ##############
                
              '''
              '''
                currStage += 1
                
            elif(currStage == 2):
               '''
               '''
                while (True):
                    if(PLC_results['EndProgram'][1] == True):
                        PLC.writePassFail_LOW()
                        PLC.writeDone(False)
                        PLC.flush_PLC()
                   ###
                        currStage = 0
                        break
                    else:
                        time.sleep(.05)
        except TimeoutError as err:
            logger.warning(err)
        except CommError as err: 
            logger.warning(err)
        

'''

'''

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
        
'''
#########################################################
# PLC---Keyence
Python program for communicating with an Allen-Bradley PLCs using Ethernet/IP 
and Keyence Vision System Controllers using Ethernet/IP.
The development for this project was aimed at reading/writing data inside an 
Allen-Bradley PLC and sending that data to a Keyence Vision System Controller.
PLCs can be used to control heavy or dangerous equipment, this code is provided "as is" 
and makes no guarantees on its reliability in a production environment. 
This code is being provided as an example of my professional experience and should not be copied or distrubuted. 

Copyright (C) 2022 Jalen Gilbert - All Rights Reserved
You may not use, distribute or modify this code. 
#####################################################
'''
