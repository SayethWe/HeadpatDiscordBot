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

def main() :
    '''targetHeight = 800
    pad=5
    offset=20
    numCol=5
    numRow=2

    roundSize=10
    selectivity=-1
    immunityScale=1
    probabilityScale=2


    title="discord"

    DATABASE_HOST=os.environ['DATABASE_URL']

    #createTables(conn,title)
    iconNums=range(roundSize)
    resName='RoundImg.png'
    res2Name='Round2Img.png'
    barGraphName='barGraph.png'
    distGraphName='histogram.png'
    dirPath=os.path.join(os.path.dirname(__file__),title)
    resPath=os.path.join(dirPath,resName);
    res2Path=os.path.join(dirPath,res2Name);
    barPath=os.path.join(dirPath,barGraphName);
    distPath=os.path.join(dirPath,distGraphName);

    res=getOptions(conn,title)
    options=res[1]
    immunities=res[2]
    probability=res[3]
    print(res)'''


    #names=["Kongou (AHnA)","Gawr Gura","Winry Rockbell",
    #       "Mikasa Ackerman","Asuna Yuuki","Kassandra",
    #       "Dunkerque","Speedwagon","Rias Gremory","Rem (Re Zero)"]
    #votes=[3,2,3,5,5,3,3,0,3,4]
    #names=["Midna","Tsuyu Asui","Kongou (Kancolle)","Satan(Helltaker)",
    #       "Yuno Gasai","2B","Makoto Niijima","Kyoko Kirigiri",
    #       "Makise Kurisu","Senjougahara Hitagi"]
    #votes=[5,1,2,2,2,6,3,3,5,1]

    #res=getRound(conn,1)
    #names=res[0][1];
    #votes=res[0][2];

    #round=storeRoundStart(conn,title,names)
    #print(round)
    #storeRoundEnd(conn,title,votes,1)

    #roundImg=createImage(dirPath,title,names,iconNums,roundSize,targetHeight,numCol,numRow,pad,offset,conn)
    #Save Results
    #cv2.imwrite(resPath,roundImg)

    #(barFig,distFig)=generatePlots(names,votes)
    #barFig.savefig(barPath)
    #distFig.savefig(distPath)

    #imm,prob=calculateRound(votes,probabilityScale,immunityScale,selectivity,1)

    #print(imm)
    #print(prob)

    #currSize,nextRound=generateRound(names,imm,prob,10,roundSize)

    #print(names)
    #print(nextRound)
    #print(currSize)

    #nextRoundImg=createImage(dirPath,title,nextRound,iconNums,currSize,targetHeight,numCol,numRow,pad,offset)
    #   cv2.imwrite(res2Path,nextRoundImg)

    conn.close()

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
    print(contestants)
    #print(roundValues)
    names = [row[0] for row in contestants]
    immunities = [row[1] for row in contestants]
    probabilities = [row[2] for row in contestants]
    urls = [row[3] for row in contestants]

    roundNum = roundNum  + 1
    print(roundNum)

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

    for i in range(len(contestants)):
        updateContestant(dbURL, guild, contestants[i], immunities[i], probabilities[i])

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

                #imgRaw=cv2.imread(imgPath,cv2.IMREAD_UNCHANGED)
                #img=Image.open(imgPath)
                #imgRaw=np.asarray(img)
                #print(imgRaw.shape)
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
            #print(iconPad.shape)
            #print(imgResize.shape)
            #imgcat = cv2.hconcat([iconPad,imgResize])
            imgcat = np.concatenate((iconPad,imgResize),1)

            #create text overlay
            bg=np.full((imgcat.shape),(0,0,0),dtype=np.uint8)
            cv2.putText(bg, name, (offset, imgcat.shape[0]-offset), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            x,y,w,h = cv2.boundingRect(bg[:,:,2])
            imgRes=imgcat.copy();
            imgRes[y-pad:y+h+pad,x-pad:x+w+pad]=bg[y-pad:y+h+pad,x-pad:x+w+pad]

            #concatenate Row
            #imgRow=cv2.hconcat([imgRow,imgRes])
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
        #imgFull = cv2.vconcat([imgFull,imgRow]);
        imgFull = np.concatenate((imgFull,imgRow),0)

    return imgFull

def calculateRound(contestants,votes,probOffset,immunityScale,selectivity,roundNum):
    '''
        Calculates immunities and probabilities for a round
    '''
    print(contestants)
    print(votes)
    ones=np.ones(len(votes))
    arr=np.array(votes)
    con=np.array(contestants)
    print(arr)
    X=arr[arr!=0]
    print(X)
    if len(X)==0:
        print('ZERO')
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

    print(val)
    print(imm)

    val=val[imm>=0]
    valProb=valProb[imm>=0]
    imm=imm[imm>=0]
    if(len(val) == 0):
        return []

    probSum=np.sum(valProb)*np.ones(len(val))
    probs=valProb/probSum
    print(probs)

    currSize=min(len(val),roundSize)
    #print(val)
    #print(currSize)
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
    #plt.show()

    distFig=plt.figure()
    plt.hist(votes,np.array(range(np.max(votes)+1))-0.5,None,True)
    plt.plot(np.array([cut,cut]),plt.gca().get_ylim(),'r-')
    plt.xlabel('Votes')
    plt.ylabel('Count')
    plt.title('Distribution of Votes')
    distFig.canvas.draw()
    #plt.show()

    return (barFig,distFig)

def createTables(dbURL):
    commands = (
        """
        CREATE TABLE IF NOT EXISTS entrants (
            name TEXT,
            guild TEXT NOT NULL,
            immunity INTEGER NOT NULL,
            probability FLOAT NOT NULL,
            image TEXT NOT NULL,
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
        """
        #,"CREATE EXTENSION IF NOT EXISTS tsm_system_rows"
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
#    commands=(f"CREATE temp TABLE temp_headpats AS SELECT * FROM headpats WHERE guild ='{guildID}'",
#              "SELECT url FROM temp_headpats TABLESAMPLE SYSTEM_ROWS (1)")
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
        #cur.execute('DROP TABLE temp_headpats')
        #conn.commit()
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

def addContestant(dbURL,guild,name, immunity, probability, imageURL):
    command = f"""
            INSERT INTO entrants(name, guild, immunity, probability, image)
            VALUES ('{name}','{guild}',{immunity},{probability},'{imageURL}')
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

def updateContestant(dbURL,guild,name,immunity,probability):
    command= f"""
        UPDATE entrants
        SET (immunity,probability) = (%s,%s)
        WHERE name = %s
        AND guild = '{guild}'
        """
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        cur.execute(command, (immunity, probability, name))
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
        url=cur.fetchone()[0]
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def getImageURL(dbURL,guild,name):
    command = f"SELECT image FROM entrants WHERE name = %s AND guild = '{guild}'"

    url=""
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        cur.execute(command, (name))
        url=cur.fetchone()[0]
        conn.commit()
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

def getContestants(dbURL,guildID):
    command= f"SELECT name, immunity, probability, image from entrants WHERE guild = '{guildID}'"
    conn=db.connect(dbURL)
    cur=conn.cursor()
    res=[-1,-1,-1]
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
    defaults=("!headpat",[],[],[800,5,20,5,2],[10 -1, 1, 2])
    res=defaults
    try:
        cur.execute(command, (title))
        conn.commit()
        res=cur.fetchall()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res
#main()
