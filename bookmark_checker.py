from bs4 import BeautifulSoup as bs
import requests
from multiprocessing.dummy import Pool
import os

localPath="C:\\Users\\young\\Desktop\\bookmarks_2019_5_19.html"#修改路径

def getUrls(path):
    urls=[]
    soup=bs(open(path,encoding='utf-8'))
    for link in soup.find_all('a'):
        urls.append(link.get('href'))
    return urls

badLinks=[]
def verifyUrl(links):
#    for i in links:
    try:
        requests.get(links,timeout=10)
        print("{}:OK".format(links))
    except requests.exceptions.ConnectionError:
        print("{}:连接错误".format(links))
        badLinks.append(links)
    except:
        print("{}:其他错误".format(links))
        badLinks.append(links)

if __name__ == "__main__":
    p=getUrls(localPath)
    pool=Pool(processes=20)
    pool.map(verifyUrl,p)
#    print("以下是所有坏链，请手动验证：")
#    print(badLinks)
    output = open('data.xls','w',encoding='gbk')#输出为excel格式，路径请自行替换
    output.write('Links\n')
    for i in range(len(badLinks)):
        output.write(badLinks[i])    
        output.write('\t')   #Tab一下，换一个单元格
        output.write('\n')
    output.close()


