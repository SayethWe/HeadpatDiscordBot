import os
import cv2
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import psycopg2 as db
import io
from urllib import request
from configparser import ConfigParser

def main() :
    targetHeight = 800
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
    print(res)

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


def createImage(baseDir,title,names,iconNums,roundSize,targetHeight,numCol,numRow,pad,offset,conn):
    assert(len(names)==roundSize)
    assert(len(iconNums)>=roundSize)
    assert(numCol*numRow>=roundSize)

    longestRow=1
    imgFull=np.full([1,longestRow,3],0,dtype=np.uint8)

    for j in range(numRow):
        imgRow=np.full([targetHeight,1,3],0,dtype=np.uint8)
        for k in range(numCol):
            i=j*numCol+k
            
            if i>=roundSize:
                break;
            
            iconName='%02.0f.png' %iconNums[i]
            name=names[i]
            #print(name)
            imgName=name+'.png'
            imgPath=os.path.join(baseDir,'img',imgName)
            iconPath=os.path.join(baseDir,'icon',iconName)
            url=getImageURL(conn,name);

            #read the image
            resp=request.urlopen(url)
            imgRaw=np.asarray(bytearray(resp.read()),dtype=np.uint8)
            imgRaw=cv2.imdecode(imgRaw,cv2.IMREAD_COLOR)
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

            #calculate the targetWidth
            targetWidth=int(targetHeight/imgRaw.shape[0]*imgRaw.shape[1])

            #resize image
            dsize=(targetWidth, targetHeight)
            imgResize=cv2.resize(imgRaw,dsize);

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

    return imgFull;

def calculateRound(votes,probOffset,immunityScale,selectivity,roundNum):
    arr=np.array(votes)
    X=arr[arr!=0]
    
    mean = np.mean(X)
    dev = np.std(X)

    
    ones=np.ones(len(votes))
    marr=mean*ones
    sarr=dev*ones
    
    prob=ones/(probOffset+arr)
    imm=np.floor(immunityScale*((arr-marr)/sarr-selectivity))

    #Eliminate zero votes
    imm[arr==0]=-1
    #set prob to 0 for all ejected
    prob[imm<0]=0

    #return future immunities
    imm[imm>0]=imm[imm>0]+roundNum+1

    return (imm,prob)

def generateRound(options,immunities,probabilities,roundNum,roundSize):
    imm=np.array(immunities)
    val=np.array(options)[imm<roundNum]
    valProb=np.array(probabilities)[imm<roundNum]
    imm=imm[imm<roundNum]

    print(val)
    print(imm)

    val=val[imm>=0]
    valProb=valProb[imm>=0]
    imm=imm[imm>=0]

    
    probSum=np.sum(valProb)*np.ones(len(val))
    probs=valProb/probSum

    

    currSize=min(len(val),roundSize)
    #print(val)
    #print(currSize)
    picks=np.random.choice(val,currSize,False,probs)

    return (currSize,picks)

def generatePlots(options, votes):
    votes=np.array(votes);
    cut=np.mean(votes[votes>0])-np.std(votes[votes>0])
    
    barFig=plt.figure()
    plt.bar(options,votes)
    plt.plot(np.array([options[0],options[len(options)-1]]),np.floor(np.array([cut,cut]))+0.5,'r-')
    barFig.autofmt_xdate()
    barFig.canvas.draw()
    #plt.show()

    distFig=plt.figure()
    plt.hist(votes,np.array(range(np.max(votes)+1))-0.5,None,True)
    plt.plot(np.array([cut,cut]),plt.gca().get_ylim(),'r-');
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
            name TEXT PRIMARY KEY,
            guild TEXT NOT NULL,
            immunity INTEGER NOT NULL,
            probability FLOAT NOT NULL,
            image TEXT NOT NULL
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS rounds (
            round_num SERIAL,
            guild TEXT NOT NULL,
            names TEXT[] NOT NULL,
            votes INTEGER[]
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS headpats (
            guild TEXT NOT NULL,
            url TEXT NOT NULL,
            PRIMARY KEY (guild, url)
            )
        """,
        "CREATE EXTENSION IF NOT EXISTS tsm_system_rows"
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
    command = "INSERT INTO headpats(guild, url) VALUES (%s,%s)"
    conn=db.connect(dbURL);
    cur = conn.cursor()
    try:
        cur.execute(command, (guildID,url))
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def getHeadpat(dbURL,guildID):
    commands=(f"CREATE temp TABLE temp_headpats AS SELECT * FROM headpats WHERE guild ='{guildID}'",
              "SELECT url FROM temp_headpats TABLESAMPLE SYSTEM_ROWS (1)",
             "DROP TABLE temp_headpats")
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

def addContestant(dbURL,title,name,imageURL):
    command = """
            INSERT INTO entrants(name, guild, immunity, probability, image)
            VALUES (%s,%s,0,1,%s)
            """
    conn=db.connect(dbURL);
    cur = conn.cursor()
    try:
        cur.execute(command, (name,title,imageURL))
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def updateContestant(dbURL,title,name,immunity,probability):
    command= """
        UPDATE entrants
        SET guild = %s
        SET immunity = %s
        SET probability = %s
        WHERE name = %s
        AND guild = %s
        """
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        cur.execute(command, (immunity, probability, name, title))
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def deleteContestant(dbURL,title,name):
    command="DELETE FROM entrants WHERE name = %s AND guild = %s"
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        cur.execute(command, (name,title))
        url=cur.fetchone()[0]
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def getImageURL(dbURL,title,name):
    command = "SELECT image FROM entrants WHERE name = %s AND guild = %s"

    url=""
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        cur.execute(command, (name,title))
        url=cur.fetchone()[0]
        conn.commit()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return url

def storeRoundStart(dbURL,title,names):
    command="INSERT INTO rounds(guild, names) VALUES(%s, %s) RETURNING round_num"
    conn=db.connect(dbURL);
    cur=conn.cursor()
    roundNum=-1;
    try:
        cur.execute(command, (title, list(names)))
        conn.commit()
        roundNum=cur.fetchone()[0]
    except(Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return roundNum


def storeRoundEnd(dbURL,title,votes,roundNum):
    command="UPDATE rounds SET votes = %s WHERE round_num = %s AND guild = %s"
    conn=db.connect(dbURL);
    cur=conn.cursor()
    try:
        cur.execute(command, (list(votes), roundNum, title))
        conn.commit()
    except(Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()

def getRound(dbURL,title,roundNum):
    command="SELECT * FROM rounds WHERE round_num = %f AND guild = %s"
    conn=db.connect(dbURL);
    cur=conn.cursor()
    res=""
    try:
        cur.execute(command, (roundNum, title))
        conn.commit()
        res=cur.fetchall()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def getRoundNum(dbURL,title):
    command="SELECT round_num FROM rounds WHERE guild = %s ORDER BY round_num DESC LIMIT 1"
    conn=db.connect(dbURL);
    cur=conn.cursor()
    res=0
    try:
        cur.execute(command, (title))
        conn.commit()
        res=cur.fetchone()[1]
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res

def getOptions(dbURL,title):
    command="SELECT * from rounds WHERE guild = %s"
    conn=db.connect(dbURL);
    cur=conn.cursor()
    res=[-1,-1,-1]
    try:
        cur.execute(command, (title))
        conn.commit()
        res=cur.fetchall()
    except (Exception, db.DatabaseError) as error:
        print(error)
    finally:
        cur.close()
        conn.close()
    return res;

#main()
