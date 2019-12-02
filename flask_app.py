from flask import Flask, request
import telepot
import urllib3
import os
import json
import itertools
import admin

separator = "-$-"

proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

bot = telepot.Bot(admin.token)
bot.setWebhook("https://Bis.eu.pythonanywhere.com/{}".format(admin.secret), max_connections=1)

app = Flask(__name__)

@app.route('/{}'.format(admin.secret), methods=["GET","POST"])
def telegram_webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        if "text" in update["message"]:
            text = update["message"]["text"]
            parse(chat_id, text, update)
            #bot.sendMessage(admin.admin_id,"{}".format(update))
    return "OK"

######################################################
# COOKIES MANAGEMENT
######################################################

def setCookie(chat_id, token):

    deleteCookie(chat_id)

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'cookie.json')

    with open(json_file_path) as f:
        data = json.load(f)

    key = "${}$".format(chat_id)

    data.update({key:token})

    with open(json_file_path, 'w') as f:
            json.dump(data, f)

def getCookie(chat_id):

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'cookie.json')

    with open(json_file_path) as f:
        data = json.load(f)

    key = "${}$".format(chat_id)

    if key in data:
        return data[key]
    else:
        return []

def deleteCookie(chat_id):
    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'cookie.json')

    with open(json_file_path) as f:
        data = json.load(f)

    key = "${}$".format(chat_id)

    if key in data:
        del data[key]

    with open(json_file_path, 'w') as f:
            json.dump(data, f)

######################################################
# COMMAND
######################################################

def parse(chat_id, msg, request):
    token = msg.split(" ")

    for t in token:
        if t == "/cancel":
            deleteCookie(chat_id)
            bot.sendMessage(chat_id, "Ok, what do you want to do?")
            return

    cookie = getCookie(chat_id)

    if len(cookie) > 0:
        cmd = cookie[0].lower()
    else:
        cmd = token[0].lower()

    token = cookie+token

    setCookie(chat_id, token)

    res = True
    status = False

    if(cmd == "/circuits" or cmd == "/circuit"):
        res,status = circuits(chat_id,token)
    elif(cmd == "/list"):
        res,status = list(chat_id)
    elif(cmd == "/pilots"):
        res,status = pilots(chat_id, token)
    elif(cmd == "/pilot"):
        res,status = pilot(chat_id, token)
    elif(cmd == "/newpilot"):
        res,status = newPilot(chat_id, token)
    elif(cmd == "/modify"):
        res,status = modify(chat_id,token)
    elif(cmd == "/delete"):
        res,status = delete(chat_id,token)
    elif(cmd == "/setup"):
        res,status = setup(chat_id,token)
    elif(cmd == "/info"):
        res,status = info(chat_id)
    elif(cmd == "/tyres"):
        res,status = tyres(chat_id,token)
    elif(cmd == "/strategy"):
        res,status = strategy(chat_id,token)
    elif(cmd == "/help"):
        res,status = help(chat_id)
    elif(cmd == "/start"):
        res,status = start(chat_id)
    elif(cmd == "/comment"):
        res,status = comment(chat_id, token)
    #--- ADMIN ---
    elif(cmd == "/adminpanel" or cmd == "/admin"):
        res,status = adminPanel(chat_id)
    elif(cmd == "/adminpilots"):
        res,status = adminPilots(chat_id,token)
    elif(cmd == "/admintest"):
        res,status = adminTest(chat_id, token)
    elif(cmd == "/admincookies"):
        res,status = viewCookies(chat_id)
    else:
        res,status = noCmd(chat_id)

    if res:
        deleteCookie(chat_id)
        report(chat_id, token, request, cmd, status)

def newPilot(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "Add a pilot in your team\n\nParams:\n- pilot's surname\n- pilot's height\n- pilot's wing delta\n\nExample: /newpilot Hamilton 174 -2")
        bot.sendMessage(chat_id, "What's your pilot's surname?")
        return False,False
    elif(len(token)==2):
        bot.sendMessage(chat_id, "How tall is {}?".format(token[1].capitalize()))
        return False,False
    elif(len(token)==3):
        bot.sendMessage(chat_id, "Set {} wing's ability : the delta between your pilot setup and the standard setup\nif you don't know write 0 and you could use /modify after".format(token[1]))
        return False,False

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    key = "{}{}{}".format(chat_id,separator,token[1].lower())

    if(key in data):
        bot.sendMessage(chat_id, "Pilot already registered\nView details with /pilot or the list with /pilots")
        return True,False

    wing = token[3]

    try:
        data.update({key:{'height':int(token[2]), 'wing':int(wing)}})
    except ValueError:
         bot.sendMessage(chat_id, "Error\nHeight and Wing's ability must be numbers")
         return True,False

    with open(json_file_path, 'w') as f:
        json.dump(data, f)

    bot.sendMessage(chat_id, "Pilot registered")
    return True,True

def modify(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "Modify pilot's profile\n\nParams:\n- pilot's surname\n- pilot's height\n- pilot's wing delta\n\nExample: /newpilot Hamilton 175 -1")
        bot.sendMessage(chat_id, "Which pilote do you want to modify?")
        pilots(chat_id,token)
        return False,False
    elif(len(token)==2):
        bot.sendMessage(chat_id, "How tall is {}?".format(token[1].capitalize()))
        return False,False
    elif(len(token)==3):
        bot.sendMessage(chat_id, "Set {} wing's ability : the delta between your pilot setup and the standard setup\nUse /circuit to see the standard setup\nif you don't know write 0 and you could use /modify after".format(token[1]))
        return False,False

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    key = "{}{}{}".format(chat_id,separator,token[1].lower())

    if(key in data):
        wing = token[3]
        try:
            data.update({key:{'height':int(token[2]), 'wing':int(wing)}})
        except ValueError:
            bot.sendMessage(chat_id, "Error:\nHeight and Wing's ability must be numbers")
            return True,False
    else:
        bot.sendMessage(chat_id, "Pilot not registered\nView the list with /pilots")
        return True,False

    with open(json_file_path, 'w') as f:
        json.dump(data, f)

    bot.sendMessage(chat_id, "Pilot's profile changed")
    return True,True


def pilots(chat_id, token):

    msg = "Your Pilots\n\n"
    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    cnt = 0
    for k in data.keys():
        tok = k.split(separator)
        if(int(tok[0]) == int(chat_id)):
            cnt+=1
            msg += tok[1].capitalize()+"\n"
    if(cnt > 0):
        bot.sendMessage(chat_id, msg)
    else:
        bot.sendMessage(chat_id,"Insert a pilot with /newpilot")
        return True,False

    return True,True

def pilot(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "View a pilot's profile\n\nParams:\n- pilot's surname\n\nExample: /pilot Verstappen")
        bot.sendMessage(chat_id, "Which pilot do you want to check?")
        pilots(chat_id,token)
        return False,False

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    key = "{}{}{}".format(chat_id,separator,token[1].lower())

    if(key in data):
        value = data[key]
        bot.sendMessage(chat_id, "Pilot {}\n\nHeight: {}\nWing delta: {}".format(token[1].lower().capitalize(),value["height"],value["wing"]))
    else:
        bot.sendMessage(chat_id,"Pilot not registered: insert a pilot with /newpilot")
        return True,False

    return True,True

def delete(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "Delete a pilot's profile from your team\n\nParams:\n- pilot's surname\n\nExample: /delete Massa")
        bot.sendMessage(chat_id, "Which pilot's profile do you want to delete?")
        pilots(chat_id,token)
        return False,False

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    key = "{}{}{}".format(chat_id,separator,token[1].lower())

    if(key in data):
        del data[key]
    else:
        bot.sendMessage(chat_id, "Pilot not registered\nView the list with /pilots")
        return True,False

    with open(json_file_path, 'w') as f:
            json.dump(data, f)

    bot.sendMessage(chat_id,"Pilot's profile deleted")
    return True,True

def setup(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "Calculate setup for a pilot and a track\n\nParams:\n- pilot's surname\n- track's name (use /list)\n- water level\n\nExample: /setup Vettel Italy 0")
        bot.sendMessage(chat_id, "Which driver do you want to calculate the setup for?\n")
        return False,False
    elif(len(token)==2):
        bot.sendMessage(chat_id, "Which track do you want to calculate the setup for?")
        return False,False
    elif(len(token)==3):
        bot.sendMessage(chat_id, "What's the water level?\nWrite 0 if there is no water")
        return False,False

    mm = 0
    delta = 0
    wetText = ""
    height = 0
    pilot = token[1].lower()
    track = token[2].lower()

    try:
        mm = float(token[3])
        wetText = "with {}mm".format(mm)
    except ValueError:
        bot.sendMessage(chat_id, "Error \nWater level must be a number")
        return True,False

    if mm < 0:
        bot.sendMessage(chat_id, "Error \nWater level must be a positive number")
        return True,False
    elif mm >= 0.3 and mm <=3.2:
        delta = 12
    elif mm >3.2:
        delta = 25

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'circuits.json')
    with open(json_file_path, 'r') as f:
        file = json.load(f)
    msg = ""

    json_file_path1 = os.path.join(my_dir, 'pilots.json')
    with open(json_file_path1, 'r') as f1:
        data = json.load(f1)

    key = "{}{}{}".format(chat_id,separator,pilot)
    if(key in data):
        value = data[key]
    else:
        bot.sendMessage(chat_id,"Pilot not registered\nInsert a pilot with /newpilot or view your pilots with /pilots");
        return True,False

    pilotHeight = int(value["height"])

    if(pilotHeight <= 192 and pilotHeight >= 186 ):
        height = -4
    elif(pilotHeight <= 189 and pilotHeight >= 185 ):
        height = -3
    elif(pilotHeight <= 184 and pilotHeight >= 180 ):
        height = -2
    elif(pilotHeight <= 179 and pilotHeight >= 175 ):
        height = -1
    elif(pilotHeight <= 174 and pilotHeight >= 170 ):
        height = -0
    elif(pilotHeight <= 169 and pilotHeight >= 162 ):
        height = 1
    else:
        bot.sendMessage(chat_id,"Pilot's height out of scale")
        return True,False

    if(track in file):
        info = file[track]
        msg = "Setup for {} in {} {}\n\nSuspension: {}\nRide height: {}\nWing level: {}\n".format(token[1].lower().capitalize(),token[2].lower().capitalize(),wetText, info["suspension"],info["rideHeight"]+delta+height,info["wingLevel"]+delta+int(value["wing"]))
    else:
        msg = "This circuit does not exist in the database use /list to check which ones are present"

    bot.sendMessage(chat_id, msg)
    return True,False

def list(chat_id):

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'circuits.json')
    with open(json_file_path, 'r') as f:
        file = json.load(f)

    msg = "Supported tracks\n\n"
    for k in file.keys():
        msg += k.capitalize()+"\n"

    msg+="\nUse /circuit for view the details of a track"

    bot.sendMessage(chat_id, msg, parse_mode='Markdown')
    return True,True


def circuits(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "View circuit's setup and pit time:\n\nParams:\n- track's name\n- water level\n\nExample: /circuit Monaco 0.3")
        bot.sendMessage(chat_id, "Which track do you want to calculate the setup for?")
        return False,False
    elif(len(token)==2):
        bot.sendMessage(chat_id, "What's the water level?\nWrite 0 if there is no water")
        return False,False

    track = ""
    mm = 0
    delta = 0
    wetText = ""
    track = token[1].lower()

    try:
        mm = float(token[2])
        wetText = "with {}mm".format(mm)
    except ValueError:
        bot.sendMessage(chat_id, "Error \nWater level must be a number")
        return True,False

    if mm < 0:
        bot.sendMessage(chat_id, "Error \nWater level must be a positive number")
        return True,False
    elif mm >= 0.3 and mm <=3.2:
        delta = 12
    elif mm >3.2:
        delta = 25


    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'circuits.json')
    with open(json_file_path, 'r') as f:
        file = json.load(f)
    msg = ""

    if(track in file):
        info = file[track]
        msg = "{} {}\n\nSuspension: {}\nRide height: {}\nWing level: {}\nPit time: {}s\nWeather: [Dark Sky]({}) ".format(token[1].lower().capitalize(),wetText, info["suspension"],info["rideHeight"]+delta,info["wingLevel"]+delta,info["pit"],info["weather"])
    else:
        msg = "This circuit does not exist in the database use /list to check which ones are present"
        return True,False

    bot.sendMessage(chat_id, msg, parse_mode='Markdown')
    return True,True

def tyres(chat_id, token):

    if(len(token) == 1):
        bot.sendMessage(chat_id, "View tyres performance\n\nParam:\n- tyres % consumption (between 1 to 20)\n\nExample /tyres 8")
        bot.sendMessage(chat_id, "Which tyres consumption do you want to examine?")
        return False,False

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'tyres.json')

    with open(json_file_path) as f:
        data = json.load(f)

    if(token[1] in data):
        value = data[token[1]]
        bot.sendMessage(chat_id, "Tyres performance with {}%\n\nOptimal: max {} lap\nNon Optimal: max {} lap\nCritical: max {} lap".format(token[1],int(value["optimal"]),int(value["nonoptimal"])+int(value["optimal"]),int(value["critical"])+int(value["nonoptimal"])+int(value["optimal"])))
        return True,True

    bot.sendMessage(chat_id,"Error \nThe %: must be between 1 to 20")
    return True,False

def strategy(chat_id, token):

    if(len(token) == 1):
        bot.sendMessage(chat_id, "Calculate possible strategies\n\nParam:\n- number of lap\n- super soft % consumption\n- soft % consumption\n- medium % consumption\n- hard % consumption\n- fuel consumption per lap\n\nAll tyre consumption must be between 1 to 20\n\nExample: /strategy 42 16 7 4 3 2.97")
        bot.sendMessage(chat_id, "How many laps do you want to consider?")
        return False,False
    elif(len(token) == 2):
        bot.sendMessage(chat_id, "What is the consumption of Super Soft tires?")
        return False,False
    elif(len(token) == 3):
        bot.sendMessage(chat_id, "What is the consumption of Soft tires?")
        return False,False
    elif(len(token) == 4):
        bot.sendMessage(chat_id, "What is the consumption of Medium tires?")
        return False,False
    elif(len(token) == 5):
        bot.sendMessage(chat_id, "What is the consumption of Hard tires?")
        return False,False
    elif(len(token) == 6):
        bot.sendMessage(chat_id, "What is the fuel consumption per lap?\nIf you are not interested, type 1")
        return False,False

    n=0
    try:
        n = int(token[1])
    except ValueError:
        bot.sendMessage(chat_id,"First param must be a positive number: the number of laps")
        return True,False

    if n <= 0:
        bot.sendMessage(chat_id,"First param must be a positive number: the number of laps")
        return True,False


    fuel = 0
    try:
        fuel = float(token[6])
    except ValueError:
        bot.sendMessage(chat_id,"Fuel consumption must be a number")
        return True,False

    if fuel <= 0:
        bot.sendMessage(chat_id,"Fuel consumption must be a positive number")
        return True,False

    maxFuelLap = int(50/fuel)

    maxLap = [0,0,0,0]

    if n < 36:
        maxStint = 3
    elif n < 56:
        maxStint = 4
    else:
        maxStint = 5

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'tyres.json')

    with open(json_file_path) as f:
        data = json.load(f)

    for index in range(4):
        if(token[index+2] in data):
            maxLap[index] = min(int(data[token[index+2]]["optimal"])+int(data[token[index+2]]["nonoptimal"]),maxFuelLap)
        else:
            bot.sendMessage(chat_id,"The tyres consumption must be between 1 to 20")
            return True,False

    lap = 0
    tyreType = [0,0,0,0]
    good = []

    for i in range(maxStint+1):
        allComb = itertools.combinations_with_replacement([0,1,2,3],i)
        for singleComb in allComb:
            lap = 0
            for tyre in singleComb:
                lap += maxLap[tyre]
                tyreType[tyre]+=1
            if lap >= n:
                b = True
                for g in good:
                    if b and len(g) == len(singleComb):
                        tyres1 = [0,0,0,0]
                        tyres2 = [0,0,0,0]
                        for i in range(len(g)):
                            tyres1[g[i]]+=1
                            tyres2[singleComb[i]]+=1
                        tot = 0
                        for i in range(4):
                            tot += abs(tyres1[i]-tyres2[i])
                        if tot == 2:
                            b = False
                        else:
                            cnt = 0
                            tot = 0
                            for t2 in singleComb:
                                for t1 in g:
                                    if(t2 <= t1):
                                        cnt+=1
                                        break
                            if(cnt < len(singleComb)):
                                b = False
                if b:
                    good.append(singleComb)




    msg = "Tyre Performance\n\nSuper Soft: max {} lap\nSoft: max {} lap\nMedium: max {} lap\nHard: max {} lap\n\n".format(maxLap[0],maxLap[1],maxLap[2],maxLap[3])

    msg += "Good Strategies\n\n"

    for s in good:
        for t in s:
            if t==0:
                msg+="SS "
            if t==1:
                msg+="S "
            if t==2:
                msg+="M "
            if t==3:
                msg+="H "
        msg+="\n"

    msg+="\nAll the strategies are not ordered: you can choose the order in which to use the tyres!"

    bot.sendMessage(chat_id,msg)
    return True,True


######################################################
# UTILITIES
######################################################


def info(chat_id):
    bot.sendMessage(chat_id, "Version: 4\nDeveloped by Giuseppe Bisicchia\nGithub: github.com/GBisi\n\nThanks to [Bruno Brown](https://igpmanager.com/app/d=profile&user=1049971&tab=bio) for his [guide](https://igpmanager.com/forum-thread/21909)!",  parse_mode='Markdown')
    return True,True

def help(chat_id):
    msg = "List of commands\n\n\
/newpilot - Add a pilot in your team\n\
/setup - Calculate setup for a pilot and a track\n\
/strategy - Calculate possible strategies\n\
/circuit - View circuit's setup and pit time\n\
/pilots - View your team\n\
/pilot - View a pilot's profile\n\
/list - View supported tracks\n\
/tyres - View tyres performance\n\
/modify - Modify pilot's profile\n\
/delete - Delete a pilot's profile from your team\n\
/cancel - Restart the session or in case of problems\n\
/comment - Leave a comment or report a problem\n\
/info - Some info\n\
/help - /help\n\n\
In case of problems type /cancel. You can report the problem or leave a comment with /comment\
    "

    bot.sendMessage(chat_id,msg)
    return True,True

def start(chat_id):
    bot.sendMessage(chat_id,"Unofficial iGP Manager Bot\n\n* Manage your team\n* Quick setup for all circuits\n* Calculate possible strategies and tyres performance\n* Get the perfect setup for your pilots on every track\n\nDeveloped by Giuseppe Bisicchia")
    help(chat_id)
    #info(chat_id)
    return True,True

def noCmd(chat_id):
    bot.sendMessage(chat_id,"Command not recognized")
    help(chat_id)
    return True,True

def comment(chat_id, token):
    if(len(token) == 1):
        bot.sendMessage(chat_id,"Did you have a problem or want to leave some suggestions or comments?\nThis space is for you: write everything you want us to know!")
        bot.sendMessage(chat_id,"Leave a comment here.\nIf you want to report a problem start with \"Problem:\", please")
        return False,False

    bot.sendMessage(chat_id,"Thank you!")
    return True,True


def report(chat_id, token, request, operation, status):
    if(not admin.checkAdmin(chat_id)):
        if status:
            msgStatus = "SUCCESS"
        else:
            msgStatus = "FAILED"
        bot.sendMessage(admin.admin_id, "--- REPORT ---\n\n\
OPERATION: {}\n\
STATUS: {}\n\
TOKEN: {}\n\
USER: {}\n\n\
\
{}".format(operation, msgStatus, token, chat_id, request))

    return True,True

######################################################
# ADMIN
######################################################

def adminPilots(chat_id, token):
    if(not admin.checkAdmin(chat_id)):
        noCmd(chat_id)
        return True,False
        
    if(len(token) == 1):
        bot.sendMessage(chat_id, "Do you want to see the database? Y/N")
        return False, False

    msg = "All Pilots\n\n"
    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    cnt = 0
    for k in data.keys():
        tok = k.split(separator)
        cnt+=1
        msg += "{} -> {}\n".format(tok[1].capitalize(),tok[0])
    if(cnt > 0):
        msg+="\nTotal: {}".format(cnt)
        bot.sendMessage(chat_id, msg)
        if(token[1].lower() == "y" or token[1].lower() == "yes"):
            bot.sendMessage(chat_id, data)
    else:
        bot.sendMessage(chat_id,"No pilots in the database!")

    return True,True

def viewCookies(chat_id):
    if(not admin.checkAdmin(chat_id)):
        noCmd(chat_id)
        return True,False

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'cookie.json')

    with open(json_file_path) as f:
        data = json.load(f)

    bot.sendMessage(chat_id, data)

    return True,True


def adminTest(chat_id, token):
    if(not admin.checkAdmin(chat_id)):
        noCmd(chat_id)
        return True,False

    bot.sendMessage(chat_id, "helo")

    return True,True
    
def adminPanel(chat_id):
    if(not admin.checkAdmin(chat_id)):
        noCmd(chat_id)
        return True,False

    bot.sendMessage(chat_id, "***** ADMIN PANEL *****\n\n-> /adminpilots\n-> /admincookies\n-> /admintest")

    return True,True    


















