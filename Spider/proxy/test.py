import requests

from bs4 import BeautifulSoup

proxy_url = "http://www.xicidaili.com/nn/%s"
usr_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'

def getProxyList(url):
    global usr_agent
    text = requests.get(url, headers={"User-Agent":usr_agent}).text
    bs = BeautifulSoup(text,'lxml')
    table = bs.find('table')
    proxies = []
    for tr in table.find_all('tr')[1:]:
        tds = tr.find_all('td')
        proxy = {'http':tds[1].text+':'+tds[2].text}
        proxy['https'] = proxy['http']
        proxies.append(proxy)
    return proxies

def checkPorxy(proxy):
    check_url = "http://ip.chinaz.com/getip.aspx"
    print("Checking:",proxy)
    try:
        text = requests.get(check_url,proxies=proxy, headers = {"User-Agent":usr_agent}, timeout=3).text
        print(text)
    except:
        print('Not Valid')


if __name__ == '__main__':
    proxies = getProxyList(proxy_url%1)
    [checkPorxy(p) for p in proxies]
