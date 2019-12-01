from flask import Flask, request
import telepot
import urllib3
import os
import json
import itertools
import admin

proxy_url = "http://proxy.server:3128"
telepot.api._pools = {
    'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
}
telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))

bot = telepot.Bot(admin.token)
bot.setWebhook("https://Bis.eu.pythonanywhere.com/{}".format(admin.secret), max_connections=1)

app = Flask(__name__)

pilotList = {}

@app.route('/{}'.format(admin.secret), methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        if "text" in update["message"]:
            text = update["message"]["text"]
            parse(chat_id, text)
    return "OK"


def parse(chat_id, msg):
    token = msg.split(" ")
    cmd = token[0]

    if(cmd == "/circuits"):
        circuits(chat_id,token)
    elif(cmd == "/list"):
        circuits(chat_id, "/circuits list".split(" "))
    elif(cmd == "/pilots"):
        pilots(chat_id, token)
    elif(cmd == "/pilot"):
        pilot(chat_id, token)
    elif(cmd == "/newpilot"):
        newPilot(chat_id, token)
    elif(cmd == "/modify"):
        modify(chat_id,token)
    elif(cmd == "/delete"):
        delete(chat_id,token)
    elif(cmd == "/setup"):
        setup(chat_id,token)
    elif(cmd == "/info"):
        info(chat_id)
    elif(cmd == "/tyres"):
        tyres(chat_id,token)
    elif(cmd == "/strategy"):
        strategy(chat_id,token)
    elif(cmd == "/help"):
        help(chat_id)
    elif(cmd == "/start"):
        start(chat_id)
    #--- ADMIN ---
    elif(cmd == "AdminAllPilots"):
        allPilots(chat_id)
    elif(cmd == "AdminTest"):
        test(chat_id, token)
    else:
        noCmd(chat_id)

def newPilot(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "Add a pilot in your team\n\nParams:\n- pilot's surname\n- pilot's height\n- pilot's wing ability (optionally)\n\nExample: /newpilot Hamilton 174")
        return

    if(len(token) < 3):
        bot.sendMessage(chat_id, "Insert new pilot\n\nParams must be name, height and wing ability (optionally)")
        return
    else:
        my_dir = os.path.dirname(__file__)
        json_file_path = os.path.join(my_dir, 'pilots.json')

        with open(json_file_path) as f:
            data = json.load(f)

        key = "{}-{}".format(chat_id,token[1].lower())

        if(key in data):
            bot.sendMessage(chat_id, "Pilot already registered View details with /pilot or the list with /pilots")
            return

        if(len(token) == 3):
            wing = "0"
        else:
            wing = token[3]

        try:
            data.update({key:{'height':int(token[2]), 'wing':int(wing)}})
        except ValueError:
             bot.sendMessage(chat_id, "Error in params:\nParams must be name, height a number and wing ability a number")

        with open(json_file_path, 'w') as f:
            json.dump(data, f)

        bot.sendMessage(chat_id, "Pilot registered")

def modify(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "Modify pilot's profile\n\nParams:\n- pilot's surname\n- pilot's height\n- pilot's wing ability (optionally)\n\nExample: /newpilot Hamilton 175")
        return

    if(len(token) < 3):
        bot.sendMessage(chat_id, "Modify pilot's profile\n\nParams must be name, height and wing ability (optionally)")
        return
    else:
        my_dir = os.path.dirname(__file__)
        json_file_path = os.path.join(my_dir, 'pilots.json')

        with open(json_file_path) as f:
            data = json.load(f)

        key = "{}-{}".format(chat_id,token[1].lower())

        if(key in data):
            try:
                if(len(token) == 3):
                    wing = data[key]["wing"]
                else:
                    wing = token[3]
                data.update({key:{'height':int(token[2]), 'wing':int(wing)}})
            except ValueError:
                bot.sendMessage(chat_id, "Error in params:\nParams must be name, height a number and wing ability a number")
        else:
            bot.sendMessage(chat_id, "Pilot not registered\nView the list with /pilots")
            return

        with open(json_file_path, 'w') as f:
            json.dump(data, f)

        bot.sendMessage(chat_id, "Pilot's profile changed")


def pilots(chat_id, token):

    msg = "Pilots\n\n"
    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    cnt = 0
    for k in data.keys():
        tok = k.split("-")
        if(int(tok[0]) == int(chat_id)):
            cnt+=1
            msg += tok[1].capitalize()+"\n"
    if(cnt > 0):
        bot.sendMessage(chat_id, msg)
    else:
        bot.sendMessage(chat_id,"Insert a pilot with /newPilot");
        return

def pilot(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "View a pilot's profile\n\nParams:\n- pilot's surname (use /pilots)\n\nExample: /pilot Verstappen")
        return

    if(len(token) != 2):
        bot.sendMessage(chat_id, "View a pilot:\nParam must be name")
        return

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    key = "{}-{}".format(chat_id,token[1].lower())

    if(key in data):
        value = data[key]
        bot.sendMessage(chat_id, "Pilot {}\n\nHeight: {}\nWing ability: {}".format(token[1].lower().capitalize(),value["height"],value["wing"]))
        return

    bot.sendMessage(chat_id,"Pilot not registered: insert a pilot with /newPilot")

def delete(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "Delete a pilot's profile from your team\n\nParams:\n- pilot's surname (use /pilots)\n\nExample: /delete Massa")
        return

    if(len(token) != 2):
        bot.sendMessage(chat_id, "View a pilot:\nParam must be name")
        return

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    key = "{}-{}".format(chat_id,token[1].lower())

    if(key in data):
        del data[key]
    else:
        bot.sendMessage(chat_id, "Pilot not registered\nView the list with /pilots")
        return

    with open(json_file_path, 'w') as f:
            json.dump(data, f)

    bot.sendMessage(chat_id,"Pilot's profile deleted")

def setup(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "Calculate setup for a pilot and a track\n\nParams:\n- pilot's surname\n- track's name (use /list)\n- water level (optionally)\n\nExample: /setup Vettel Italy")
        return

    mm = 0
    delta = 0
    wetText = ""
    height = 0
    if(len(token) >= 3):
        pilot = token[1].lower()
        track = token[2].lower()
    else:
        bot.sendMessage(chat_id, "View circuit's setup for a pilot:\nParam must be a pilot's name, a circuit's name (View /list) and optionally, the water level")
        return

    if(len(token) == 4):
        try:
            mm = float(token[3])
            wetText = "with {}mm".format(mm)
        except ValueError:
            bot.sendMessage(chat_id, "View circuit's setup for a pilot:\nThe third param must be a floating number -> the water level")
            return

    if mm < 0:
        bot.sendMessage(chat_id, "View circuit's setup for a pilot:\nThe third param must be a positive number -> the water level")
        return
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

    key = "{}-{}".format(chat_id,pilot)
    if(key in data):
        value = data[key]
    else:
        bot.sendMessage(chat_id,"Pilot not registered: insert a pilot with /newPilot");
        return

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
        return

    if(track in file):
        info = file[track]
        msg = "Setup for {} in {} {}\n\nSuspension: {}\nRide height: {}\nWing level: {}\n".format(token[1].lower().capitalize(),token[2].lower().capitalize(),wetText, info["suspension"],info["rideHeight"]+delta+height,info["wingLevel"]+delta+int(value["wing"]))
    else:
        msg = "This circuit does not exist in the database use /list to check which ones are present"

    bot.sendMessage(chat_id, msg)

def circuits(chat_id, token):

    if(len(token)==1):
        bot.sendMessage(chat_id, "View circuit's setup and pit time:\n\nParams:\n- track's name\n- water level (optionally)\n\nExample: /circuits Monaco")
        return

    track = "ls"
    mm = 0
    delta = 0
    wetText = ""
    if(len(token) >= 2):
        track = token[1].lower()
    else:
        bot.sendMessage(chat_id, "View circuit's setup, pit time and weather:\nParam must be a circuit's name (View /list) and optionally, the water level")
        return

    if(len(token) == 3):
        try:
            mm = float(token[2])
            wetText = "with {}mm".format(mm)
        except ValueError:
            bot.sendMessage(chat_id, "View set-up for a circuit:\nThe second param must be a floating number -> the water level")
            return

    if mm < 0:
        bot.sendMessage(chat_id, "View set-up for a circuit:\nThe second param must be a positive number -> the water level")
        return
    elif mm >= 0.3 and mm <=3.2:
        delta = 12
    elif mm >3.2:
        delta = 25


    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'circuits.json')
    with open(json_file_path, 'r') as f:
        file = json.load(f)
    msg = ""

    if(track == "list" or track == "ls"):
        msg = "Supported tracks\n\n"
        for k in file.keys():
            msg += k.capitalize()+"\n"

    elif(track in file):
        info = file[track]
        msg = "{} {}\n\nSuspension: {}\nRide height: {}\nWing level: {}\nPit time: {}s\nWeather: [Dark Sky]({}) ".format(token[1].lower().capitalize(),wetText, info["suspension"],info["rideHeight"]+delta,info["wingLevel"]+delta,info["pit"],info["weather"])
    else:
        msg = "This circuit does not exist in the database use /list to check which ones are present"

    bot.sendMessage(chat_id, msg, parse_mode='Markdown')

def tyres(chat_id, token):

    if(len(token) == 1):
        bot.sendMessage(chat_id, "View tyres performance\n\nParam:\n- tyres % consumption (between 1 to 20)\n\nExample /tyres 8")
        return

    if(len(token) != 2):
        bot.sendMessage(chat_id, "View tyres performance:\nParam must be %")
        return

    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'tyres.json')

    with open(json_file_path) as f:
        data = json.load(f)

    if(token[1] in data):
        value = data[token[1]]
        bot.sendMessage(chat_id, "Tyres performance with {}%\n\nOptimal: max {} lap\nNon Optimal: max {} lap\nCritical: max {} lap".format(token[1],int(value["optimal"]),int(value["nonoptimal"])+int(value["optimal"]),int(value["critical"])+int(value["nonoptimal"])+int(value["optimal"])))
        return

    bot.sendMessage(chat_id,"The %: must be between 1 to 20");

def strategy(chat_id, token):

    if(len(token) == 1 or len(token) < 6):
        bot.sendMessage(chat_id, "Calculate possible strategies\n\nParam:\n- number of lap\n- super soft % consumption\n- soft % consumption\n- medium % consumption\n- hard % consumption\n- fuel consumption per lap (optionally)\n\nAll tyre consumption must be between 1 to 20\n\nExample: /strategy 42 16 7 4 3")
        return
    try:
        n = int(token[1])
    except ValueError:
        bot.sendMessage("First param must be a integer: number of lap")
        return

    fuel = 1
    if len(token) == 7:
        try:
            fuel = float(token[6])
        except ValueError:
            bot.sendMessage("Fuel consumption must be a number")
            return

    if fuel <= 0:
        bot.sendMessage("Fuel consumption must be a positive number")

    maxFuelLap = int(50/fuel)

    maxLap = [0,0,0,0]

    if n < 36:
        maxStint = 3
    elif n < 46:
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
            bot.sendMessage(chat_id,"The %: must be between 1 to 20")
            return

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


######################################################
# UTILITIES
######################################################


def info(chat_id):
    bot.sendMessage(chat_id, "Version: 2.7\nDeveloped by Giuseppe Bisicchia\nGithub: github.com/GBisi")

def help(chat_id):
    msg = "List of commands\n\n\
* newpilot - Add a pilot in your team\n\
* modify - Modify pilot's profile\n\
* delete - Delete a pilot's profile from your team\n\
* pilots - View your team\n\
* pilot - View a pilot's profile\n\
* setup - Calculate setup for a pilot and a track\n\
* list - View supported tracks\n\
* circuits - View circuit's setup and pit time\n\
* tyres - View tyres performance\n\
* strategy - Calculate possible strategies\n\
* info - Some info\n\
* help - /help\n\
    "

    bot.sendMessage(chat_id,msg)

def start(chat_id):
    bot.sendMessage(chat_id,"Unofficial iGP Manager Bot\n\n* Manage your team\n* Quick setup for all circuits\n* Calculate possible strategies and tyres performance\n* Get the perfect setup for your pilots on every track")
    help(chat_id)
    #info(chat_id)

def noCmd(chat_id):
    bot.sendMessage(chat_id,"Command not recognized")

######################################################
# ADMIN
######################################################

def allPilots(chat_id):
    if(not admin.checkAdmin(chat_id)):
        noCmd()
        return
    msg = "All Pilots\n\n"
    my_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(my_dir, 'pilots.json')

    with open(json_file_path) as f:
        data = json.load(f)

    cnt = 0
    for k in data.keys():
        tok = k.split("-")
        cnt+=1
        msg += tok[1].capitalize()+"\n"
    if(cnt > 0):
        bot.sendMessage(chat_id, msg)
        bot.sendMessage(chat_id, data)
    else:
        bot.sendMessage(chat_id,"No pilots in the database!")
        return

def test(chat_id, token):
    if(not admin.checkAdmin(chat_id)):
        noCmd()
        return
    bot.sendMessage(chat_id, "helo")
