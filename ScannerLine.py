import pytesseract
from wand.image import Image
from wand.color import Color
import cv2
import pandas as pd
import os


#######################################################################################
# NEED TO CHANGE THIS TWO LINE TO MAKE IT WORK
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files (x86)/Tesseract-OCR/tesseract'
#points to the dr where tesseract locates
os.chdir(r'C:\Users\Inhen\Desktop\statements')#Go to the directory where the pdf locates
#######################################################################################

# is the sum of a row pixel list is very small which means it is a black line
def is_line(rowsum):
    if rowsum < 200000:
        return True
    else:
        return False

# Get a list of blocks ========= like this, [upper,lower]
def block_location(row_list):
    block = []
    block_list = []
    continuous_flag = 0
    block_start = 0
    for i in range(len(row_list)):
        if continuous_flag == 0 and is_line(row_list[i]):#skip the width of a dark line
            continuous_flag = 1
        if continuous_flag == 1 and is_line(row_list[i]) == False and block_start == 0:
            block_start = 1
            block += [i]
        if block_start == 1 and is_line(row_list[i]):
            block_start = 0
            block += [i - 1]
            block_list += [block]
            block = []
            continuous_flag = 0
    return block_list



# input is the result from img_to_data and get useful text from this input
def clean_text(text):
    mytext = text.split('\t')
    useful_text = []
    for i in range(11, len(mytext), 11):
        useful_text += [mytext[i]]
    useful_text = useful_text[1:]

    for i in range(len(useful_text)):
        try:
            useful_text[i] = useful_text[i].replace('\n1', '')
        except:
            pass
        try:
            useful_text[i] = useful_text[i].replace('\n2', '')
        except:
            pass
        try:
            useful_text[i] = useful_text[i].replace('\n3', '')
        except:
            pass
        try:
            useful_text[i] = useful_text[i].replace('\n4', '')
        except:
            pass
        try:
            useful_text[i] = useful_text[i].replace('\n5', '')
        except:
            pass

    useful_text = [x for x in useful_text if x != '']
    return useful_text


pdf_list=[x for x in os.listdir() if x[-3:]=='pdf']
# get pdf names

for pdf in pdf_list:#convert pdf to pngs
    with Image(filename=pdf, resolution=300) as img:
        img.background_color = Color("white")
        img.alpha_channel = False
        img.save(filename='image'+pdf+'.png')

# get png names
img_list=[x for x in os.listdir() if x[-3:]=='png']
description_list=[]
date_list=[]
balance_list=[]
amount_list=[]

for img_name in img_list:
    img = cv2.imread(img_name,0)
    img_line=[sum(x) for x in img]
    y,x=img.shape
    block_list=block_location(img_line)



    for i in range(len(block_list)):#for each block,get date/description/amount/balance
        description_string=''
        y1,y2=block_list[i]
        block=img[y1:y2,:]
        description=block[:,:int(x*65/100)]#description is around here
        amount=block[:,int(x*65/100):]#amount and balance is around here



        text = pytesseract.image_to_data(description,lang='eng')
        useful_text=clean_text(text)
        text_a=pytesseract.image_to_data(amount,lang='eng')
        useful_text_a=clean_text(text_a)


        if len(useful_text)<=1 or len(useful_text_a)<=1:
            continue
        # if it is empty ignore this block
        if len(useful_text_a)!=2:# if the balance and amount is not like this [amount,balance] we need to review
            print('need to review')
            continue

        # print(useful_text)
        date_list+=[useful_text[0]]
        for words in useful_text[1:]:
            description_string+=words
            description_string+=' '
        description_list+=[description_string]
        amount_list+=[useful_text_a[0]]
        balance_list+=[useful_text_a[1]]

    print(date_list)
    print(description_list)
    print(amount_list)
    print(balance_list)


# do some adjustment on the list, replace the common mistakes 1 {;7 /;so on and so forth
for i in range(len(date_list)):
    if len(date_list[i])==5:
        if date_list[i][0].isdigit()==False:
            date_list[i] = '1' + str(date_list[i][1:])
        else:
            if int(date_list[i][0])>=1:
                date_list[i]='1'+str(date_list[i][1:])

for i in range(len(amount_list)):
    try:
        amount_list[i]=amount_list[i].replace('/','7')
    except:
        pass

for i in range(len(balance_list)):
    try:
        balance_list[i]=balance_list[i].replace('/','7')
    except:
        pass

df = pd.DataFrame({'date': date_list, 'description': description_list, 'amount': amount_list, 'balance': balance_list})
print(df.head(5), len(df))
df.to_csv('combined.csv')


