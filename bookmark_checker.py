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
    for i in links:
        try:
            r=requests.get(i,timeout=10)
            if(r.status_code==200):
                print("{}:OK".format(i))
        #        links.pop(i)
        # except requests.exceptions.ConnectionError:
        #     print('ConnectionError')
        # except requests.exceptions.ChunkedEncodingError:
        #     print('ChunkedEncodingError')   
        # except:
        #     print('Unfortunitely -- An Unknow Error Happened')
        #     break
        except requests.exceptions.ConnectionError:
            print("{}:连接错误".format(i))
        except:
            print("{}:其他错误".format(i))
    print(links)


if __name__ == "__main__":
    p=getUrls(localPath)
    verifyUrl(p)
