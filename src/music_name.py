import requests
from bs4 import BeautifulSoup
import re

# 针对反爬的身份伪装，添加user-agent，本次作业配上之后，所有的爬取都没有出现问题。
# 叨叨两句，如果长期长时间大规模的爬虫，要降低当前ip的一个访问频率（适当的休眠或者ip代理都可以）
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:62.0) Gecko/20100101 Firefox/62.0'}


# 波浪线提示python函数命名规则，小细节

def get_playlist_name(cats):
    num = 0
    for cat in cats:
        url = 'https://music.163.com/discover/playlist/?order=hot&cat=' + cat + '&limit=35&offset=0'
        with open('musicName.txt', 'a', encoding='utf-8') as f:
            while url:
                r = requests.get(url, headers=headers)
                # print(r.text)
                soup = BeautifulSoup(r.text, 'lxml')
                playlist_ids = []
                playlist_names = []
                # 正则匹配到id和name
                playlist_ids.extend(re.findall(r'playlist\?id=(\d+?)" class="msk"', r.text))
                playlist_names.extend(re.findall(r'class="tit f-thide s-fc0">(.+?)</a>', r.text))
                # print(playlist_ids)
                # print(playlist_names)

                for i, j in zip(playlist_names, playlist_ids):
                    f.write(i + 'http://music.163.com/playlist?id=' + j + '\n')
                    num += 1
                    print(num)

                f.write('\n\n\n')

                try:
                    url = 'http://music.163.com' + soup.find('a', class_='zbtn znxt')['href']  # 下一页的url
                except TypeError:
                    url = None  # 最后一页直接设置url为None，跳出while循环
        print(cat)
    print(num)


newCats = ['华语', '欧美', '日语', '韩语', '粤语', '小语种', '流行', '摇滚', '民谣', '电子', '舞曲', '说唱', '轻音乐', '爵士'
    , '乡村', 'R&B/Soul', '古典', '民族', '英伦', '金属', '古风', '翻唱']
get_playlist_name(newCats)
