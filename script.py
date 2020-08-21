import pandas as pd 
import os
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.chrome.options import Options
import os
import datetime
import unicodedata

USERNAME = "****" #Your Username
PASSWORD =  "****" #Your oddsmonkey username
path_to_chrome_driver=  "****" #Path to your chromedriver
smarkets_csv_location =  "****" #Path to the smarkets csv that you have donwloaded
new_csv_location = "***/updated_test.csv" #replace *** with the path to the folder that this script is contained in

def GetDfWithAllSmarketsLosses():
    with open(smarkets_csv_location,'r') as f:
        with open("updated_test.csv",'a') as f1:
            next(f) # skip header line
            for line in f:
                f1.write(line)
    new_smarkets_csv= pd.read_csv(new_csv_location)
    os.remove(new_csv_location)
    newInOut = []
    for box in new_smarkets_csv['In/Out (GBP)']:
        box = box.replace(",","")
        newInOut.append(box)
    new_smarkets_csv['In/Out (GBP)'] = newInOut
    new_smarkets_csv['In/Out (GBP)'] = new_smarkets_csv['In/Out (GBP)'].astype(float)
    losses_smarkets_csv = new_smarkets_csv[new_smarkets_csv['In/Out (GBP)']<0]
    smarketsdf = pd.DataFrame({
        "Details": losses_smarkets_csv['Details'],
        "Date": losses_smarkets_csv['Date'],
        "Loss": losses_smarkets_csv['In/Out (GBP)']
    })
    Day = []
    Month = []
    for box in smarketsdf['Date']:
        box = box.encode('ascii','ignore')
        Month.append((box.split(' '))[0])
        Day.append((((box.split(' '))[1]).split(','))[0])
    smarketsdf['Day'] = Day
    smarketsdf['Month']= Month
    smarketsdf = smarketsdf.drop(['Date'], axis=1)
    return smarketsdf


def GetintoOddsmonkeyandscrape():
    driver = webdriver.Chrome(executable_path= path_to_chrome_driver)
    driver.get('https://www.oddsmonkey.com/tools/profittracker.aspx')  
    driver.find_element_by_name("dnn$ctr433$Login$Login_DNN$txtUsername").send_keys(USERNAME)
    driver.find_element_by_name("dnn$ctr433$Login$Login_DNN$txtPassword").send_keys(PASSWORD)
    driver.find_element_by_name("dnn$ctr433$Login$Login_DNN$txtPassword").send_keys(Keys.ENTER) 
    driver.get('https://www.oddsmonkey.com/tools/profittracker.aspx') 
    (event, name, bookie) = ([],[],[])
    for tablenumber in range (1,7,1):
        time.sleep(4) 
        driver.find_element_by_xpath("/html/body/form/div[3]/div[1]/div[2]/div/div/div/div/div/div/div[4]/div/div[1]/div/div/div[3]/div/div/div/div/table/thead/tr[1]/td/div/div[2]/a[{}]".format(tablenumber)).click()
        for row in range(1,11,1):
            event.append(driver.find_element_by_xpath("/html/body/form/div[3]/div[1]/div[2]/div/div/div/div/div/div/div[4]/div/div[1]/div/div/div[3]/div/div/div/div/table/tbody/tr[{}]/td[2]/div".format(row)).text)
            name.append(driver.find_element_by_xpath("/html/body/form/div[3]/div[1]/div[2]/div/div/div/div/div/div/div[4]/div/div[1]/div/div/div[3]/div/div/div/div/table/tbody/tr[{}]/td[3]".format(row)).text)
        for picturenumber in range (4,24,2):
            if picturenumber < 10:
                strpicturenumber = "0"+str(picturenumber)
            else:
                strpicturenumber = str(picturenumber)
            try:
                stringtoparse = str('//*[@id="dnn_ctr1483_View_rgTransactions_ctl00_ctl{}_imgBookie1"]').format(strpicturenumber)
                bookie.append(driver.find_element_by_xpath(stringtoparse).get_attribute("src"))
            except:
                bookie.append("Na")
                Exception
    oddsmonkeydf = pd.DataFrame({
        'name' :name,
        'event': event,
        'bookie':bookie
        })
    (Day, Month) = ([],[])
    for box in oddsmonkeydf['event']:
        box = box.encode('ascii','ignore')
        Day.append((box.split(' '))[0])
        Month.append((box.split(' '))[1])
    oddsmonkeydf['Day'] = Day
    oddsmonkeydf['Month']= Month
    oddsmonkeydf = oddsmonkeydf.drop(['event'], axis=1)
    bookies=[]
    for box in oddsmonkeydf['bookie']:
        box = box.encode('ascii','ignore')
        try:
            box = box.split('_h.gif')[0]
            bookies.append((box.split('/desktopModules/arbmonitor/images/bookies/'))[1])
        except:
            bookies.append("Na")
            Exception
    oddsmonkeydf['bookie']=bookies
    return oddsmonkeydf

def findmatchwithtime(row, racetime):
    (bookie, name)= (row['bookie'], row['name'])
    found = None
    try:
        found = True if racetime == str(name).split(' ')[1] else False
    except:
        found = False
        Exception
    if found:
        return(bookie)
    else:
        return None
    

def findmatchwithsplitdetails(row, splitdetails):
    splitname = row['name'].split(' ')
    found = None
    for eachone in splitdetails:
        if eachone in row['name'].split(' '):
            found = True
            break
        else:
            found = False
    if found == True:
        return row['bookie']
    else:
        return None

def findmatch(row, oddsmonkeydf):
    potentialbookies= []
    (day, month, details)= (int(row['Day']), row['Month'], row['Details'])
    oddsmonkeydf['Day'].astype(int)
    newdf = oddsmonkeydf[oddsmonkeydf['Day']==day]
    if len(newdf) > 0:
        if details[0].isdigit() and details[2] == ':':
            racetime = details.split(' ')[0]
            #print(newdf, row, "new")
            newdf['Potential'] = newdf.apply(lambda row:findmatchwithtime(row, racetime), axis=1)
        else:
            try:
                splitdetails = (details.split(' '))
                newdf['Potential'] = newdf.apply(lambda row:findmatchwithsplitdetails(row, splitdetails), axis=1)
                #print("POTENTIALLLLLS", newdf['Potential'].tolist())
            except:
                print(details, "THIS WAS AN ERORR")
                Exception
        foundbookies=newdf['Potential'].tolist()
        foundbookies = [i for i in foundbookies if i]
        if foundbookies:
            foundbookies = list(dict.fromkeys(foundbookies))
            return foundbookies
        else:
            return False
    return False


smarketsdf= GetDfWithAllSmarketsLosses()

oddsmonkeydf = GetintoOddsmonkeyandscrape()
oddsmonkeydf.to_csv('oddsmonkeydf2.csv', index=False)
oddsmonkeydf = pd.read_csv('/Users/ianholdroyd/Documents/GitHub/Play/smarkets_oddsmonkey_csv/oddsmonkeydf2.csv')

smarketsdf['bookiesfound'] = smarketsdf.apply(lambda row: findmatch(row, oddsmonkeydf), axis=1)

foundbookiestotal = smarketsdf['bookiesfound'].tolist()


(returnedbookies, unfound) = ([],[])

dflistwhenlist =  smarketsdf['Details'].tolist()
dfhowmuchlist = smarketsdf['Loss'].tolist()
dfdatelist = smarketsdf['Day'].tolist()
dfmonthlist = smarketsdf['Month'].tolist()

for i in range (0, len(foundbookiestotal), 1):
    if foundbookiestotal[i] == False:
        (when, howmuch, day, month) = (dflistwhenlist[i], dfhowmuchlist[i], dfdatelist[i], dfmonthlist[i])
        unfound.append("{} at {},{},{} is unfound".format(howmuch, when, day, month))
    else:
        for j in foundbookiestotal[i]:
            if j not in returnedbookies:
                returnedbookies.append(j)

print(returnedbookies)
for i in unfound:
    print(i)