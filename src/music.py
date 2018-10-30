import json
import re
import base64
import binascii
import random
import time

import requests
from math import ceil
from Crypto.Cipher import AES

# 新的加密模块只接受bytes数据，如果是字符数据-->字节数据，需要编码code，如果是字节数据-->字符数据，则需要解码decode

# 这里就是window.asrsea(q,w,e,r)，w，e，r参数不变直接使用

pub_key = "010001"  # 第二参数，rsa公匙组成，也就是w参数
modulus = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee" \
          "341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e" \
          "82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"  # 第三参数，rsa公匙组成，也就是e参数
secret_key = b'0CoJUm6Qyw8W8jud'  # 第四参数，aes密匙，也就是r参数

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:62.0) Gecko/20100101 Firefox/62.0'}


# 首先是加密算法，与js文件中相应函数一一对应

# 生成随机长度为16的字符串---函数a()
def random_16():
    return bytes(''.join(random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 16)), 'utf-8')


# aes加密---函数b()
def aes_encrypt(text, key):
    pad = 16 - len(text) % 16  # 对长度不是16倍数的字符串进行补全，然后在转为bytes数据(字节)
    try:  # 如果接到bytes数据（如第一次aes加密得到的密文）要解码再进行补全
        text = text.decode()
    except:
        pass
    text = text + pad * chr(pad)  # 补全字符串
    try:
        text = text.encode()  # 字符转到字节，加密仅支持字节数据
    except:
        pass
    encryptor = AES.new(key, AES.MODE_CBC, b'0102030405060708')  # 包括提到的偏移量
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext)  # 得到的密文还要进行base64编码
    return ciphertext


# rsa加密---函数c()
def rsa_encrypt(ran_16, pub_key, modulus):
    text = ran_16[::-1]  # 明文处理，反序并hex编码
    rsa = int(binascii.hexlify(text), 16) ** int(pub_key, 16) % int(modulus, 16)
    return format(rsa, 'x').zfill(256)


# 返回加密后内容---函数d()
def encrypt_data(data):
    ran_16 = random_16()
    text = json.dumps(data)
    params = aes_encrypt(text, secret_key)  # params两次aes加密
    params = aes_encrypt(params, ran_16)
    encSecKey = rsa_encrypt(ran_16, pub_key, modulus)
    return {'params': params.decode(),
            'encSecKey': encSecKey}


# 获取歌单id
def get_playlist(pages, order, cat):
    playlist_ids = []
    for page in range(pages):
        url = 'http://music.163.com/discover/playlist/?order={}&cat={}&limit=35&offset={}'.format(order, cat,
                                                                                                  str(page * 35))
        r = requests.get(url, headers=headers)
        playlist_ids.extend(re.findall(r'playlist\?id=(\d+?)" class="msk"', r.text))  # 正则去匹配
        return playlist_ids


# 获取歌曲id
def get_songs(playlist_id):
    r = requests.get('http://music.163.com/playlist?id={}'.format(playlist_id), headers=headers)
    song_ids = re.findall(r'song\?id=(\d+?)".+?</a>', r.text)
    song_titles = re.findall(r'song\?id=\d+?">(.+?)</a>', r.text)
    list_title = re.search(r'>(.+?) - 歌单 - 网易云音乐', r.text).group(1)
    list_url = 'http://music.163.com/playlist?id=' + playlist_id
    return [song_ids, song_titles, list_title, list_url]  # 返回歌单下全部歌曲的id号，名字，歌单的名字，歌单的url


# 写入文件txt来保存评论
def save_comments(some, pages, f):
    f.write('\n\n\n歌单**《{}》**\t\t链接{}'.format(some[2], some[3]).center(200) + '\n\n\n')
    post_urls = ['http://music.163.com/weapi/v1/resource/comments/R_SO_4_' + deep + '?csrf_token=' for deep in some[0]]
    song_urls = ['http://music.163.com/song?id=' + dark for dark in some[0]]
    num = 0
    for i in range(len(post_urls)):
        f.write('\n\n歌曲**「{}」**\t\t链接{}\n\n'.format(some[1][i], song_urls[i]))
        for j in range(pages):
            if j == 0:  # 第一页会包括精彩评论和最新评论
                if len(enc_data_list) == 0:
                    data = {'rid': "", 'offset': '0', 'total': "true", 'limit': "20", 'csrf_token': ""}
                    start = time.time()
                    enc_data_list.append(encrypt_data(data))
                    print('[info]第%s次加密耗时：%s' % (j + 1, time.time() - start))  # 测试每次加密耗时
                enc_data = enc_data_list[j]
                r = requests.post(post_urls[i], headers=headers, data=enc_data)
                content = r.json()
                if content['hotComments']:  # 判断第一页有没有精彩评论
                    f.write('\n\n********' + '精彩评论\n\n')
                    comment(content, 'hotComments', f)

                f.write('\n\n********' + '最新评论\n\n')
                comment(content, 'comments', f)

            else:  # 非第一页只有普通评论
                if len(enc_data_list) != j + 1:
                    data = {'rid': "", 'offset': str(j * 20), 'total': "false", 'limit': "20", 'csrf_token': ""}
                    start = time.time()
                    enc_data_list.append(encrypt_data(data))
                    print('[info]第%s次加密耗时：%s' % (j + 1, time.time() - start))
                enc_data = enc_data_list[j]
                r = requests.post(post_urls[i], headers=headers, data=enc_data)
                content = r.json()
                comment(content, 'comments', f)

        num = num + 1
        print(num)


# 提取json数据中的评论，因为评论分两种，所以设一个参数接收种类,有些返回评论是对其他人评论的一个回复
def comment(content, c_type, f):
    for each in content[c_type]:
        if each['beReplied']:  # 判断有没有回复内容
            if each['beReplied'][0]['content']:  # 有时回复内容会被删掉，也判断一下
                f.write('' + each['content'] + '\n')
                f.write('\t回复:\n' + each['beReplied'][0]['content'] + '\n' + '-' * 50 + '\n')
        else:
            f.write('' + each['content'] + '\n' + '-' * 60 + '\n')


# multiple_crawl接收四个参数，nums是int，是爬几个歌单；order，cat是可选参数，分别是排序和分类，排序有new和hot。默认排序hot，默认分类华语
def multiple_crawl(nums, order='hot', cat='华语', pages=1):
    with open('{}_{}_{}lists.txt'.format(order, cat, nums), 'w', encoding='utf-8') as m:
        playlist_ids = get_playlist(ceil(nums / 35), order, cat)
        print(playlist_ids)
        for i in range(nums):
            save_comments(get_songs(playlist_ids[i]), pages, m)


# 长时间爬取会被服务器踢出，适当时候可以休眠一段时间，或者尝试ip代理
enc_data_list = []  # 加密得到的请求参数列表，来存储每页的参数，避免重复计算
start = time.time()
multiple_crawl(1, pages=1)
print('[info]总耗时：%s' % (time.time() - start))  # 测试总耗时
