from bs4 import BeautifulSoup as bs
import requests
import socks
import socket
from multiprocessing.dummy import Pool
import os

localPath = "/home/ron/Documents/bookmarks_2019_11_15.html"  # 修改路径
socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 7891)
socket.socket = socks.socksocket


def getUrls(path):
    urls = []
    soup = bs(open(path, encoding='utf-8'))
    for link in soup.find_all('a'):
        urls.append(link.get('href'))
    return urls


badLinks = []


def verifyUrl(links):
    try:
        requests.get(links, timeout=10)
        print("{}:OK".format(links))
    except requests.exceptions.ConnectionError:
        print("{}:连接错误".format(links))
        badLinks.append(links)
    except:
        print("{}:其他错误".format(links))
        badLinks.append(links)


if __name__ == "__main__":
    p = getUrls(localPath)
    pool = Pool(processes=20)
    pool.map(verifyUrl, p)

    output = open('data.xlsx', 'w', encoding='gbk')  # 输出为excel格式，路径请自行替换
    output.write('Links\n')
    for i in range(len(badLinks)):
        output.write(badLinks[i])
        output.write('\t')  # Tab一下，换一个单元格
        output.write('\n')
    output.close()
