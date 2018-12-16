from bs4 import BeautifulSoup as bs
import requests

localPath="C:\\Users\\young\\Desktop\\bookmarks_2018_12_15.html"

def getUrls(path):
    urls=[]
    soup=bs(open(path,encoding='utf-8'))
    for link in soup.find_all('a'):
        urls.append(link.get('href'))
    return urls

def verifyUrl(links):
    badLinks=[]
    for i in links:
        try:
            r=requests.get(i,timeout=10)
            print("{}:OK".format(i))
        except requests.exceptions.ConnectionError:
            print("{}:连接错误".format(i))
            badLinks.append(i)
        except:
            print("{}:其他错误".format(i))
            badLinks.append(i)
    print("以下是所有坏链，请手动验证：")
    print(badLinks)


if __name__ == "__main__":
    p=getUrls(localPath)
    verifyUrl(p)
