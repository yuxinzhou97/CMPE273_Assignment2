import fileinput
import sys
import requests
import schedule
import time

def findAction(text, attr):
    start = text.find(attr)
    attrlen = len(attr)
    trimming = text[start+attrlen+1:]
    trimming = trimming.split("&")
    info = {'action': '', 'data': '' }
    if "action" in trimming[0] and "data" in trimming[1]:
        info['action'] = trimming[0][trimming[0].find("::")+len("::"):]
        info['data'] = trimming[1][trimming[1].find("data: ")+len("data: "):].replace("\'", "")
    return info

def invoke(stepList, invokeStep, inputdata):
    curStep = Step.copy(stepList[invokeStep - 1])
    curStep.outbound_url = inputdata
    runStep(curStep)

def runStep(curStep):
    if (curStep.method == "GET"):
        url = curStep.outbound_url
        # print(url)
        r = requests.get(url)
        statusCode = r.status_code
        # check if the status code matches the condition
        if (int(statusCode) == int(curStep.condition)):
            curAction = curStep.thentext['action']
            curData = curStep.thentext['data']
            if "invoke" in curAction:
                # get invoke step number
                invokeStep = int(curAction[curAction.find("step:")+len("step:"):])
                invoke(stepList, invokeStep, curData)
            elif "print" in curAction:
                if "headers" in curData:
                    infoNeeded = curData.split(".")
                    headerInfo = infoNeeded[len(infoNeeded)-1]
                    print(r.headers[headerInfo])
                else:
                    print(curData)
        else:
            curAction = curStep.elsetext['action']
            curData = curStep.elsetext['data']
            if "print" in curAction:
                print(curData)


def findInfo(text, attr):
    start = text.find(attr)
    attrlen = len(attr)
    trimming = text[start+attrlen:]
    trimming = trimming.split("&", 1)
    info = trimming[0]
    return info

def findCondition(text, attr):
    start = text.find(attr)
    attrlen = len(attr)
    trimming = text[start+attrlen+1:]
    trimming = trimming.split("&")
    info = ""
    if "if" in trimming[0] and "equal" in trimming[1] and "http.response.code" in trimming[2]:
        info = trimming[3]
    info = info[info.find('right: ') + len("right: "):]
    return info


class Step:
    def __init__(self, type, method, outbound_url, condition, thentext, elsetext):
        self.type = type
        self.method = method
        self.outbound_url = outbound_url
        self.condition = condition
        self.thentext = thentext
        self.elsetext = elsetext

    @staticmethod
    def copy(anotherStep):
        return Step(anotherStep.type, anotherStep.method, anotherStep.outbound_url, anotherStep.condition, anotherStep.thentext, anotherStep.elsetext)

    def printStepInfo(self):
        print("Step Infomation:")
        print("type: " + self.type)
        print("method: " + self.method)
        print("outbound_url: " + self.outbound_url)
        print("condition code: " + self.condition)
        print("then: " + "action: " + self.thentext['action'] + " data: " + self.thentext['data'])
        print("else: " + "action: " + self.elsetext['action'] + " data: " + self.elsetext['data'])

def runScheduleSteps(orders, stepList):
    for order in orders:
        stepToRun = int(order)
        curStep = stepList[stepToRun - 1]
        runStep(curStep)

def job():
    runScheduleSteps(orders, stepList)

input = "";
lines = fileinput.input()
for line in lines:
    input = input + line

input = input.replace("\n", "&")
input = input.replace("  ", "") #lines now delimited by '&'
# print(input)
# Obtain scheduler information first
scheduler = {'when': '', 'steps': ''}
startIndex = input.find("when");
contents = input[startIndex:].split("\"")
whenStr = contents[1]
scheduler['when'] = whenStr
stepsStr = contents[2][(contents[2].find("[")+2):(contents[2].find("]")-1)]
scheduler['steps'] = stepsStr.split(" ")
# print(scheduler)


# Obtain information of steps
steps = input.split("- "); # split texts about each step
steps.pop(0) #remove first line "Steps: "
# print(steps)
stepList = [];
for step in steps:
    typetext = findInfo(step, 'type: ')
    methodtext = findInfo(step, 'method: ')
    outbound_urltext = findInfo(step, 'outbound_url: ')
    conditiontext = findCondition(step, 'condition:') #find status code in condition
    thentext = findAction(step, 'then:') #find action and data
    elsetext = findAction(step, 'else:')
    newStep = Step(typetext, methodtext, outbound_urltext, conditiontext, thentext, elsetext)
    stepList.append(newStep)
    #newStep.printStepInfo()


orders = scheduler['steps']
curSchedule = scheduler['when'].split(" ")
minuteCode = curSchedule[0]
hourCode = curSchedule[1]
dayOfWeekCode = curSchedule[2]


if (minuteCode != '*' and hourCode == '*' and dayOfWeekCode == '*'):
    schedule.every(int(minuteCode)).minutes.do(job)
elif (dayOfWeekCode == '*'):
    min = 0
    if (minuteCode != '*'):
        min = minuteCode
    hour = 0
    if (hourCode != '*'):
        hour = hourCode
    schedule.every().day.at(hour + ":" + min).do(job)
elif (minuteCode != '*' and hourCode != '*' and dayOfWeekCode != '*'):
    #(0 - 6) (Sunday to Saturday;
    if int(dayOfWeekCode) == 0:
        schedule.every().sunday.at(hourCode + ":" + minuteCode).do(job)
    if int(dayOfWeekCode) == 1:
        schedule.every().monday.at(hourCode + ":" + minuteCode).do(job)
    if int(dayOfWeekCode) == 2:
        schedule.every().tuesday.at(hourCode + ":" + minuteCode).do(job)
    if int(dayOfWeekCode) == 3:
        schedule.every().wednesday.at(hourCode + ":" + minuteCode).do(job)
    if int(dayOfWeekCode) == 4:
        schedule.every().thursday.at(hourCode + ":" + minuteCode).do(job)
    if int(dayOfWeekCode) == 5:
        schedule.every().friday.at(hourCode + ":" + minuteCode).do(job)
    if int(dayOfWeekCode) == 6:
        schedule.every().saturday.at(hourCode + ":" + minuteCode).do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
