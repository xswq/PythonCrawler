import json, re, base64, random, requests, binascii, threading, time
from Crypto.Cipher import AES  # 新的加密模块只接受bytes数据，否者报错，密匙明文什么的要先转码
from concurrent.futures import ProcessPoolExecutor


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



class OnePageComment(threading.Thread):  # 下载一页评论的线程类
    def __init__(self, post_url, enc_data):
        threading.Thread.__init__(self)
        self.post_url = post_url
        self.enc_data = enc_data
        self.comment = ''  # 创建一个comment变量储存爬到的数据

    def run(self):
        semaphore.acquire()
        content = requests.post(self.post_url, headers=headers, data=self.enc_data).json()
        if 'hotComments' in content:
            if content['hotComments']:
                self.comment += '*************精彩评论\n\n'
                self.common(content, 'hotComments')

            self.comment += '\n\n*************最新评论\n\n'
            self.common(content, 'comments')
        else:
            self.common(content, 'comments')
        semaphore.release()

    def common(self, content, c_type):
        for each in content[c_type]:
            if each['beReplied']:
                if each['beReplied'][0]['content']:
                    self.comment += each['content'] + '\n\t回复：\n\t' + each['beReplied'][0][
                        'content'] + '\n' + '-' * 60 + '\n'
            else:
                self.comment += each['content'] + '\n' + '-' * 60 + '\n'

    def get_comment(self):  # 选择返回评论而不是直接写入文件，因为多个线程同时操作一个文件有风险，应先返回，后统一写入
        return self.comment


def get_enc_datas(pages, max_workers=4):  # 多进程加密
    raw_datas = []
    for i in range(pages):
        if i == 0:
            raw_datas.append({'rid': "", 'offset': '0', 'total': "true", 'limit': "20", 'csrf_token': ""})
        else:
            raw_datas.append({'rid': "", 'offset': str(i * 20), 'total': "false", 'limit': "20", 'csrf_token': ""})
    with ProcessPoolExecutor(max_workers) as pool:  # 多进程适合计算密集型任务，如加密算法得到请求参数
        result = pool.map(encrypt_data, raw_datas)
    return list(result)


def one_song_comment(id_):  # 爬取一首歌的评论并写入txt，网络I/O密集使用多线程
    post_url = 'http://music.163.com/weapi/v1/resource/comments/R_SO_4_' + str(id_) + '?csrf_token='
    ts = [OnePageComment(post_url, i) for i in enc_datas]
    [i.start() for i in ts]
    [i.join() for i in ts]
    comments = [i.get_comment() for i in ts]
    with open(id_ + '.txt', 'w', encoding='utf-8') as f:
        f.writelines(comments)


if __name__ == '__main__':
    start = time.time()
    semaphore = threading.Semaphore(4)  # 最大线程4
    enc_datas = get_enc_datas(1000)  # 获取加密后的数据,对所有歌曲都是通用的，这里有1000页的加密数据，对应爬1000页评论
    one_song_comment('29004400')  # 华晨宇，烟火里的尘埃
    print('[info]耗时：%s' % (time.time() - start))
