import os
import cv2
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import psycopg2 as db
import psycopg2.errorcodes as errorcodes
import io
from urllib import request
from configparser import ConfigParser
import traceback

import gacha

DEFAULTPAD = 5
DEFAULTOFFSET = 20
DEFAULTTARGETHEIGHT = 800
DEFAULTCOLS = 5
DEFAULTROWS = 2
DEFAULTSELECTIVITY = -1
DEFAULTIMMUNITYSCALE = 1
DEFAULTPROBABILITY = 1

IMAGEFAILURL = "https://i.imgur.com/lW0Yvgl.jpg"

def createImageDefault(contestants,contestantUrls):
    '''
    Creates a 5 x 2 poll image with default settings for contestants given
        DEFAULTPAD = 5
        DEFAULTOFFSET = 20
        DEFAULTTARGETHEIGHT = 800px
        DEFAULTCOLS = 5
        DEFAULTROWS = 2
        DEFAULTIMAGENAME = 'poll.jpg' (in current directory)
    '''
    baseDir = os.path.dirname(__file__)
    imgPath = os.path.join(baseDir, 'poll.jpg')
    cv2.imwrite(imgPath, createImage(
        baseDir,
        contestants,
        contestantUrls,
        range(len(contestants)),
        DEFAULTTARGETHEIGHT,
        DEFAULTCOLS,
        DEFAULTPAD,
        DEFAULTOFFSET
    ))

def startRound(dbURL, guild, message):
    '''
        Starts a new round for the guild given
        effects: creates a poll image called 'poll.jpg'
        returns: round_num
    '''
    roundNum = getRoundNum(dbURL, guild)
    roundValues = getRound(dbURL, guild, roundNum)
    if roundNum != 0 and not roundValues[1]:
        print('UNFINISHED ROUND')
        return -1

    contestants = getContestants(dbURL, guild)
   #print(contestants)
    #print(roundValues)
    names = [row[0] for row in contestants]
    immunities = [row[1] for row in contestants]
    probabilities = [row[2] for row in contestants]
    urls = [row[3] for row in contestants]

    roundNum = roundNum  + 1
   #print(roundNum)

    picks = generateRound(immunities, probabilities, roundNum, 10)
    if picks == []:
        print('NO VALID PICKS')
        return -2
    chosenContestants = [names[i] for i in picks]

    createImageDefault(chosenContestants, [urls[i] for i in picks])

    storeRoundStart(dbURL, guild, chosenContestants, roundNum, message)

    return roundNum, len(picks)

def calculateRoundDefault(contestants,votes, roundNum):
    return calculateRound(contestants, votes,
                    DEFAULTPROBABILITY,
                    DEFAULTIMMUNITYSCALE,
                    DEFAULTSELECTIVITY,
                    roundNum)

def getRoundMessage(dbURL, guild):
    roundNum = getRoundNum(dbURL, guild)
    if roundNum == 0:
        print('NO ROUND')
        return -2
    roundValues = getRound(dbURL, guild, roundNum)

    if roundNum != 0 and roundValues[1]:
        print('ALREADY ENDED ROUND')
        return -1
    return roundValues, roundNum

def updateMessageID(dbURL, guild, message, roundID):
    command=f"UPDATE rounds SET message = '{message}' WHERE round_num = {roundID} AND guild = '{guild}'"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
    except(Exception, db.DatabaseError) as error:
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

def endRound(dbURL, guild, votes, contestants, roundNum):
    '''
        Ends a round and displays results
    '''
    (immunities, probabilities)=getRoundResults(votes, contestants, roundNum)

    oldCR=[]
    for contestant in contestants:
        oldCR.append(getChallenge(dbURL, guild, contestant)[0][0])
    CRs = gacha.updateCRs(votes,oldCR)

    for i in range(len(contestants)):
        updateContestant(dbURL, guild, contestants[i], immunities[i], probabilities[i], CRs[i])

    storeRoundEnd(dbURL, guild, votes, roundNum)
    return roundNum

def getRoundResults(votes, contestants, roundNum):
    immprob = calculateRoundDefault(contestants,votes, roundNum)
    immunities = immprob[0]
    probabilities = immprob[1]
    barFig,distFig = generatePlots(contestants, votes)
    baseDir = os.path.dirname(__file__)
    imgPath1 = os.path.join(baseDir, 'plot1.jpg')
    imgPath2 = os.path.join(baseDir, 'plot2.jpg')
    barFig.savefig(imgPath1)
    distFig.savefig(imgPath2)

    return (immunities, probabilities)

def createImage(baseDir,names, urls, iconNums,targetHeight,numCol,pad,offset):
    roundSize = len(names)

    assert(roundSize != 0)
    assert(len(iconNums)>=roundSize)
    assert(numCol != 0)
    numRow=int(np.ceil(float(roundSize)/numCol))

    longestRow=1
    imgFull=np.full([1,longestRow,3],0,dtype=np.uint8)

    for j in range(numRow):
        imgRow=np.full([targetHeight,1,3],0,dtype=np.uint8)
        for k in range(numCol):
            i=j*numCol+k

            if i>=roundSize:
                break

            iconName='%02.0f.png' %iconNums[i]
            name=names[i]

            imgName=name+'.png'
            #imgPath=os.path.join(baseDir,'img',imgName)
            iconPath=os.path.join(baseDir,'icon',iconName)
            url=urls[i]

            try:
                #read the image
                print(f"Fetching image for {name} from {url}")
                resp=request.urlopen(url)
                imgRaw=np.asarray(bytearray(resp.read()),dtype=np.uint8)
                imgRaw=cv2.imdecode(imgRaw,cv2.IMREAD_UNCHANGED)

                #account for transparency
                if(imgRaw.shape[2]==4):
                    alpha=imgRaw[:,:,3]
                    rgb=imgRaw[:,:,:3]

                    whitebg=np.ones_like(rgb,dtype=np.uint8)*255

                    alpha_factor = alpha[:,:,np.newaxis].astype(np.float32) / 255.0
                    alpha_factor = np.concatenate((alpha_factor,alpha_factor,alpha_factor), axis=2)

                    base = rgb.astype(np.float32) * alpha_factor
                    white = whitebg.astype(np.float32) * (1 - alpha_factor)
                    imgRaw = base + white

            except (Exception) as error:
                #Load default failure image
                #stopgap for now, but it'll do
                print(error)
                print("Image failed, swapping to default")
                resp=request.urlopen(IMAGEFAILURL)
                imgRaw=np.asarray(bytearray(resp.read()),dtype=np.uint8)
                imgRaw=cv2.imdecode(imgRaw,cv2.IMREAD_UNCHANGED)

            #calculate the targetWidth
            targetWidth=int(targetHeight/imgRaw.shape[0]*imgRaw.shape[1])

            #resize image
            dsize=(targetWidth, targetHeight)
            imgResize=cv2.resize(imgRaw,dsize)

            #read and resize the icon
            iconRaw=cv2.imread(iconPath)
            iconPad=cv2.copyMakeBorder(iconRaw, 0, targetHeight-iconRaw.shape[0],
                                       0, 0, cv2.BORDER_CONSTANT, None,
                                       [255, 255, 255])

            #concatenate images
            imgcat = np.concatenate((iconPad,imgResize),1)

            #create text overlay
            bg=np.full((imgcat.shape),(0,0,0),dtype=np.uint8)
            cv2.putText(bg, name, (offset, imgcat.shape[0]-offset), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            x,y,w,h = cv2.boundingRect(bg[:,:,2])
            imgRes=imgcat.copy();
            imgRes[y-pad:y+h+pad,x-pad:x+w+pad]=bg[y-pad:y+h+pad,x-pad:x+w+pad]

            #concatenate Row
            imgRow=np.concatenate((imgRow,imgRes),1)

        rowLen = imgRow.shape[1]

        if rowLen<longestRow:
            #pad row
            imgRow=cv2.copyMakeBorder(imgRow, 0, 0, 0, longestRow-rowLen,
                                      cv2.BORDER_CONSTANT, None, [255, 255, 255])
        else:
            #pad existing
            imgFull=cv2.copyMakeBorder(imgFull, 0, 0, 0, rowLen-longestRow,
                                       cv2.BORDER_CONSTANT, None, [255, 255, 255])
            longestRow=rowLen

        #concatenate Image
        imgFull = np.concatenate((imgFull,imgRow),0)

    return imgFull

def calculateRound(contestants,votes,probOffset,immunityScale,selectivity,roundNum):
    '''
        Calculates immunities and probabilities for a round
    '''
    #print(contestants)
    #print(votes)
    ones=np.ones(len(votes))
    arr=np.array(votes)
    con=np.array(contestants)
    #print(arr)
    X=arr[arr!=0]
    #print(X)
    if len(X)==0:
        #print('ZERO')
        imm=-1*np.ones(len(arr))
        prob=np.zeros(len(arr))
        elim=con
        return (imm,prob,elim)

    mean = np.mean(X)
    dev = np.std(X)
    marr=mean*ones
    sarr=dev*ones

    elim=con[votes<marr+selectivity*sarr]

    if dev == 0:
        imm = np.zeros(len(votes))
    else:
        imm=np.floor(immunityScale*((arr-marr)/sarr-selectivity))

    prob=ones/(1+probOffset+arr)

    #Eliminate zero votes
    imm[arr==0]=-1
    #set prob to 0 for all ejected
    prob[imm<0]=0

    #return future immunities
    imm[imm>=0]=imm[imm>=0]+roundNum+1

    return (imm,prob,elim)

def generateRound(immunities,probabilities,roundNum,roundSize):
    imm=np.array(immunities)
    val=np.array(range(len(immunities)))[imm<roundNum]
    valProb=np.array(probabilities)[imm<roundNum]
    imm=imm[imm<roundNum]

    #print(val)
    #print(imm)

    val=val[imm>=0]
    valProb=valProb[imm>=0]
    imm=imm[imm>=0]
    if(len(val) == 0):
        return []

    probSum=np.sum(valProb)*np.ones(len(val))
    probs=valProb/probSum
   #print(probs)

    currSize=min(len(val),roundSize)
    picks=np.random.choice(val,currSize,False,probs)
    return picks

def generatePlots(options, votes):
    votes=np.array(votes)
    cut = 0
    if len(votes[votes>0]) != 0:
        cut=np.mean(votes[votes>0])-np.std(votes[votes>0])

    barFig=plt.figure()
    plt.bar(options,votes)
    plt.plot(np.array([options[0],options[len(options)-1]]),np.floor(np.array([cut,cut]))+0.5,'r-')
    barFig.autofmt_xdate()
    barFig.canvas.draw()

    distFig=plt.figure()
    plt.hist(votes,np.array(range(np.max(votes)+1))-0.5,None,True)
    plt.plot(np.array([cut,cut]),plt.gca().get_ylim(),'r-')
    plt.xlabel('Votes')
    plt.ylabel('Count')
    plt.title('Distribution of Votes')
    distFig.canvas.draw()

    return (barFig,distFig)

def createTables(dbURL):
    commands = (
        """
        CREATE TABLE IF NOT EXISTS entrants (
            name TEXT,
            guild TEXT NOT NULL,
            immunity INTEGER NOT NULL,
            probability FLOAT NOT NULL,
            challenge INTEGER NOT NULL,
            image TEXT NOT NULL,
            claimant TEXT,
            PRIMARY KEY (name, guild)
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS rounds (
            round_num INTEGER,
            guild TEXT,
            names TEXT[] NOT NULL,
            votes INTEGER[],
            message TEXT NOT NULL,
            PRIMARY KEY (guild, round_num)
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS headpats (
            guild TEXT NOT NULL,
            url TEXT NOT NULL,
            PRIMARY KEY (guild, url)
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS options (
            guild TEXT PRIMARY KEY,
            prefix TEXT,
            edit_roles TEXT,
            call_roles TEXT,
            image_options FLOAT[],
            vote_options FLOAT[]
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS gacha (
        guild TEXT NOT NULL,
        userid TEXT NOT NULL,
        tickets INTEGER NOT NULL,
        score INTEGER,
        challenge TEXT,
        team TEXT [],
        PRIMARY KEY (guild, userid)
        )
        """
    )
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        for command in commands :
            cur.execute(command)
        conn.commit()
    except (Exception, db.DatabaseError) as error:
       print(error)
    finally:
        cur.close()
        conn.close()

def addHeadpat(dbURL,guildID,url):
    '''
        Adds a URL to the database given in a headpats(guild, url) table
        dbURL: database URL
        guildID: guild ID
        url: Image of the headpat
    '''
    command = f"INSERT INTO headpats(guild, url) VALUES ('{guildID}','{url}')"
    res = -2
    try:
        conn=db.connect(dbURL)
        cur = conn.cursor()
        cur.execute(command)
        conn.commit()
        res = 0
    except db.DatabaseError as error:
        traceback.print_exc()
        print(errorcodes.lookup(error.pgcode))
        print(errorcodes.UNIQUE_VIOLATION)
        if error.pgcode == errorcodes.UNIQUE_VIOLATION:
            res = -1
        else:
            res = -2
    except Exception as error:
        res = -2
    finally:
        cur.close()
        conn.close()
    return res

def getHeadpat(dbURL,guildID):
    commands = [f"SELECT url, guild FROM headpats WHERE guild ='{guildID}' OFFSET floor(random() * (SELECT COUNT(*) FROM headpats WHERE guild = '{guildID}')) LIMIT 1"]
    conn=db.connect(dbURL);
    cur = conn.cursor()
    output = ""
    try:
        for command in commands:
            cur.execute(command)
        conn.commit()
        output = cur.fetchone()[0]
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return output

def removeHeadpat(dbURL,guildID,url):
    command=f"DELETE FROM headpats WHERE guild='{guildID}' AND url = '{url}'"
    conn=db.connect(dbURL)
    cur = conn.cursor()
    res = False
    try:
        cur.execute(command)
        conn.commit()
        res = True
    except (Exception, db.DatabaseError) as error:
        print(error)
        res = False
    finally:
        cur.close()
        conn.close()
    return res

def addContestant(dbURL,guild,name,imageURL, immunity = 0, probability = 1, challenge = 1):
    command = f"""
            INSERT INTO entrants(name, guild, immunity, probability, image, challenge)
            VALUES ('{name}','{guild}',{immunity},{probability},'{imageURL}',{challenge})
            """
    conn=db.connect(dbURL)
    cur = conn.cursor()
    res = False
    try:
        cur.execute(command)
        conn.commit()
        res = True
    except (Exception, db.DatabaseError) as error:
        print(error)
        res = False
    finally:
        cur.close()
        conn.close()
    return res

def updateContestant(dbURL,guild,name,immunity,probability,challenge):
    command= f"""
        UPDATE entrants
        SET (immunity,probability,challenge) = (%s,%s,%s)
        WHERE name = %s
        AND guild = '{guild}'
        """
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        cur.execute(command, (immunity, probability, challenge, name))
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def deleteContestant(dbURL,guild,name):
    command=f"DELETE FROM entrants WHERE name = '{name}' AND guild = '{guild}' RETURNING image"
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
        url=cur.fetchone()[0]
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def getImageURL(dbURL,guild,name):
    command = f"SELECT image FROM entrants WHERE name = '{name}' AND guild = '{guild}'"

    url=""
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
        url=cur.fetchone()[0]
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return url

def storeRoundStart(dbURL,guild,names, roundNum, message):
    command=f"INSERT INTO rounds(guild, names, round_num, message) VALUES('{guild}', %s, %s, '{message}')"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command, (list(names), roundNum))
        conn.commit()
    except(Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def storeRoundEnd(dbURL,guild,votes,roundNum):
    command=f"UPDATE rounds SET votes = %s WHERE round_num = %s AND guild = '{guild}'"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command, (list(votes), roundNum))
        conn.commit()
    except(Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def getRound(dbURL,guild,roundNum):
    command= f"SELECT names, votes, message FROM rounds WHERE round_num = {roundNum} AND guild = '{guild}'"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    res=-2
    try:
        cur.execute(command)
        conn.commit()
        res=cur.fetchone()
    except db.DatabaseError as error:
        print(error.pgcode)
        res = -1
    finally:
        cur.close()
        conn.close()
    return res

def getRoundNum(dbURL,guild):
    '''
    gets the latest round number for the guild
    '''
    command=f"SELECT MAX(round_num) FROM rounds WHERE guild = '{guild}'"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    res=0
    try:
        cur.execute(command)
        conn.commit()
        res=cur.fetchone()
        if len(res) == 0 or not res[0]:
            res = 0
        else:
            res = res[0]
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def getChallenge(dbURL,guildID,name):
    command=f"SELECT challenge FROM entrants WHERE guild = '{guildID}' AND name = '{name}'"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    res=[-1]
    try:
        cur.execute(command)
        conn.commit()
        res=cur.fetchall()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def getContestants(dbURL,guildID):
    command= f"SELECT name, immunity, probability, image, challenge from entrants WHERE guild = '{guildID}'"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    res=[-1,-1,-1,-1,-1]
    try:
        cur.execute(command)
        conn.commit()
        res=cur.fetchall()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def getOptions(dbURL, guildID) :
    command = f"SELECT * FROM options WHERE guild = '{guildID}''"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    defaults=("!",[],[],[800,5,20,5,2],[10 -1, 1, 2])
    res=defaults
    try:
        cur.execute(command)
        conn.commit()
        res=cur.fetchall()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def claimableWaifus(dbURL, guildID):
    command=(f"SELECT name, challenge FROM entrants WHERE guild = '{guildID}' AND claimant IS NULL AND NOT immunity = -1")
    conn=db.connect(dbURL)
    cur=conn.cursor()
    res=[None,None]
    try:
        cur.execute(command)
        conn.commit()
        res=cur.fetchall()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def claimWaifu(dbURL, guildID, user, name):
    command=(f"UPDATE entrants SET claimant = {user} WHERE guild = '{guildID}' AND name = '{name}'")
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def whoClaimed(dbURL, guildID, name):
    command=(f"SELECT claimant FROM entrants WHERE name = '{name}'")
    conn=db.connect(dbURL)
    cur=conn.cursor()
    res='0'
    try:
        cur.execute(command)
        conn.commit()
        res=cur.fetchone()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def getClaims(dbURL, guildID, claimant):
    command=f"SELECT name FROM entrants WHERE claimant = '{claimant}'"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    res='0'
    try:
        cur.execute(command)
        conn.commit()
        res=cur.fetchall()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def fetchUserInfo(dbURL, guildID, userId):
    command = f"""
    INSERT INTO gacha (guild, userid, tickets, score) VALUES('{guildID}','{userId}',0,0)
    ON CONFLICT (guild, userid)
    DO
    UPDATE SET tickets = gacha.tickets
    RETURNING tickets, score
    """
    res=([0,0])
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
        res=cur.fetchall()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def updateTickets(dbURL, guildID, userId, tickets):
    command=f"""
        UPDATE gacha SET tickets={tickets}
        WHERE guild = '{guildID}' AND userid = '{userId}'
        """
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def updateScore(dbURL, guildID, userId, score):
    command=f"""
        INSERT INTO gacha (userid, score) VALUES ('{userId}',{score})
        ON CONFLICT (userid)
        DO
        UPDATE gacha SET score={score} WHERE guild = '{guildID}' AND userid = '{userId}'
    """
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def issueChallenge(dbURL, guildID, challengerID, chalengeeID):
    commands=(f"""
        UPDATE gacha SET challenge='{challengeeID}' WHERE guild = '{guildID}' AND userid = '{challengerID}'
    """,
    """
        UPDATE gacha SET challenge='{challengerID}' WHERE guild = '{guildID}' AND userid = '{challengeeID}'
    """)
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(commands)
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    pass

def getChallengeParties(dbURL, guildID, userID):
    command=f"""
        SELECT userid, challenge FROM gacha WHERE guild = '{guildID}' AND userid = '{userID}'
    """
    pass

def clearChallenge(dbURL, guildID, userID):
    command=f"""
        UPDATE gacha SET challenge = NULL WHERE guild = '{guildID}' AND userid = '{userID}'
    """
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def setTeam(dbURL, guildID, userID, team):
    command = f"""
        UPDATE gacha SET team = ARRAY{team} WHERE guild = '{guildID}' AND userid = '{userID}'
    """
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def getTeam(dbURL, guildID, userID):
    command = f"""
        SELECT team FROM gacha WHERE guild = '{guildID}' AND userid = '{userID}'
    """
    res=(None,None,None,None)
    conn=db.connect(dbURL)
    cur=conn.cursor()
    try:
        cur.execute(command)
        conn.commit()
        res=list(cur.fetchall()[0][0])
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res
