from bs4 import BeautifulSoup as bs
import requests
from multiprocessing.dummy import Pool

localPath="C:\\Users\\young\\Desktop\\bookmarks_2018_12_20.html"#修改路径

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
    print("以下是所有坏链，请手动验证：")
    print(badLinks)
