# coding=utf-8
import contextlib
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta
from threading import Thread

import pymysql
import requests
import xlrd
from loguru import logger
from requests.adapters import HTTPAdapter

# 忽略安全警告
requests.packages.urllib3.disable_warnings()
requests.DEFAULT_RETRIES = 1


@contextlib.contextmanager
def get_connection():
    conn = pymysql.connect(host="10.21.200.38",
                           user="susi",
                           password="susi",
                           database="monitor")
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_sign(data):
    hl = hashlib.md5()
    hl.update(data.encode(encoding='utf-8'))
    return hl.hexdigest()


def get_proxy_by_cloud(s):
    while True:
        try:
            _proxy = s.get(
                "http://liner0123.user.xiecaiyun.com/api/proxies?action=getText&key=NP4BEC8C05&count=1&word=&rand=true&norepeat=false&detail=false&ltime=0", timeout=3).text.strip()
        except requests.exceptions.RequestException:
            time.sleep(3)
            continue

        proxies = {}
        proxies["http"] = proxies["https"] = "http://liner0123:a123456@%s" % _proxy
        return proxies


buy_time = "2023-05-05 20:00:00.000000"
buy_time = datetime.strptime(buy_time, "%Y-%m-%d %H:%M:%S.%f")
shop_name = "茅台"

server_ip = "http://127.0.0.1:5001/"
# server_ip = "http://203.156.218.106:5000/"
server_ip = "http://10.21.200.12:5000/"
_token = "gpL6vXwYRqYfJHg9Osl8EH3hDg1iy9pur4KOJveg83sBsLCRz%2FTWzdXQpODMMsx3C7rSUzqatLfxvUqoTfXP653ju63%2FBxKHMQ80D7RUEQrC3LtyNVQxTPlPiOYXYEHlBehK4cRdiS0xUXfclgwvbgHznndU3vYsmj9%2B760iNNo%3D"


def main(username, cookies):
    try:
        s = requests.Session()
        s.mount("http://", HTTPAdapter(max_retries=2))
        s.mount("https://", HTTPAdapter(max_retries=2))
        s.keep_alive = False
        s.verify = False

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        ua_name, ua_version = "Chrome", "110.0.0.0"
        s.headers = {
            'user-agent': ua,
            'content-type': 'application/x-www-form-urlencoded',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'referer': 'https://cart.taobao.com/',
            'accept-language': 'zh-CN,zh;q=0.9',
        }

        s.cookies = requests.utils.cookiejar_from_dict(
            cookies, cookiejar=None, overwrite=True)

        # 还剩60秒时，获取一些参数
        while True:
            now = datetime.now()
            if buy_time - now <= timedelta(seconds=60):
                logger.info(f"{username} 还剩60秒")

                proxies = {
                    "http": "http://10.21.60.102:8888",
                    "https": "http://10.21.60.102:8888",
                }
                proxies = get_proxy_by_cloud(s)
                logger.info(f"{username} 获取ip池 %s" % proxies)

                try:
                    tk_token = cookies["_m_h5_tk"].split("_")[0]

                    # 添加购物车
                    t = str(round(time.time() * 1000))
                    data = '{"itemId":"20739895092","skuId":"4227830352490","quantity":"2","exParams":"{\\"id\\":\\"20739895092\\",\\"locType\\":\\"B2C\\",\\"skuId\\":\\"4227830352490\\",\\"from\\":\\"cart\\",\\"spm\\":\\"a21202.12579950.item.0\\",\\"serviceId\\":\\"\\"}","serviceId":""}'
                    sign = get_sign(f"{tk_token}&{t}&12574478&{data}")
                    addbag_resp = s.post(
                        f'https://h5api.m.taobao.com/h5/mtop.trade.addbag/3.1/?jsv=2.7.0&appKey=12574478&t={t}&sign={sign}&api=mtop.trade.addBag&v=3.1&isSec=0&ecode=0&needEcodeSign=true&LoginRequest=true&ttid=h5&type=originaljson&dataType=jsonp&safariGoLogin=true&mainDomain=taobao.com&subDomain=m&prefix=h5api&H5Request=true&pageDomain=taobao.com&postJSON=true&token={tk_token}', data={'data': data}, proxies=proxies, timeout=3)
                    logger.info(f"{username} 添加购物车成功 {addbag_resp.text}")
                    if "令牌过期" in addbag_resp.text:
                        logger.info(f"{username} 令牌过期")
                        _m_h5_tk = requests.utils.dict_from_cookiejar(
                            addbag_resp.cookies)["_m_h5_tk"]
                        _m_h5_tk_enc = requests.utils.dict_from_cookiejar(
                            addbag_resp.cookies)["_m_h5_tk_enc"]
                        c = requests.cookies.RequestsCookieJar()
                        c.set("_m_h5_tk", _m_h5_tk)
                        c.set("_m_h5_tk_enc", _m_h5_tk_enc)
                        s.cookies.update(c)
                        tk_token = _m_h5_tk.split("_")[0]
                        continue
                    time.sleep(5)

                    t = str(round(time.time() * 1000))
                    data = '{"isPage":true,"extStatus":0,"netType":0,"exParams":"{\"mergeCombo\":\"true\",\"version\":\"1.1.1\",\"globalSell\":\"1\",\"cartFrom\":\"tsm_native_taobao\",\"dataformat\":\"dataformat_ultron_h5\"}","cartFrom":"tsm_native_taobao","dataformat":"dataformat_ultron_h5","ttid":"h5"}'
                    sign = get_sign(f"{tk_token}&{t}&12574478&{data}")
                    req = s.get(
                        f"https://h5api.m.taobao.com/h5/mtop.trade.query.bag/5.0/?jsv=2.5.6&appKey=12574478&t={t}&sign={sign}&api=mtop.trade.query.bag&v=5.0&type=jsonp&ttid=h5&isSec=0&ecode=1&AntiFlood=true&AntiCreep=true&H5Request=true&dataType=jsonp&callback=mtopjsonp2&data={data}", proxies=proxies, timeout=3)
                    query_bag_data = json.loads(
                        re.match(".*?({.*}).*", req.text, re.S).group(1))["data"]

                    # 防止请求过快
                    logger.info(f"{username} 创建订单")
                    time.sleep(5)

                    for k, v in query_bag_data["data"].items():
                        if "item_" in k and shop_name in v["fields"]["title"]:
                            settlement = v["fields"]["settlement"]
                            break
                    logger.info(f"{username} 获取{shop_name}settlement {settlement}")

                    while True:
                        sib_resp = s.post(
                            "https://h5api.m.taobao.com/h5/mtop.trade.order.create.h5/4.0", proxies=proxies, timeout=3)
                        punish = re.search('被挤爆啦', sib_resp.text)
                        if punish:
                            punish = re.search(r'url":.*?"(.*?)"', sib_resp.text).group(1)
                            sib_resp = s.get(punish, proxies=proxies, timeout=3)
                            app_key = re.search(
                                r'NCAPPKEY":.*?"(.*?)"', sib_resp.text)
                            token = re.search(
                                r'NCTOKENSTR":.*?"(.*?)"', sib_resp.text)
                            x5sec = re.search(
                                r'SECDATA":.*?"(.*?)"', sib_resp.text)
                            if app_key is None or token is None or x5sec is None:
                                logger.info(f"{username} {sib_resp.text}")
                                s.close()
                                break
                        else:
                            app_key = re.search(
                                r'NCAPPKEY":.*?"(.*?)"', sib_resp.text)
                            token = re.search(
                                r'NCTOKENSTR":.*?"(.*?)"', sib_resp.text)
                            x5sec = re.search(
                                r'SECDATA":.*?"(.*?)"', sib_resp.text)

                        app_key = app_key.group(1)
                        token = token.group(1)
                        x5sec = x5sec.group(1)
                        if re.search(r'NCAPPKEY', app_key) or re.search(r'NCTOKENSTR', token):
                            s.close()
                            logger.info(f"{username} {sib_resp.text}")
                            break

                        logger.info(f"{username} 获取app_key: %s" % app_key)
                        logger.info(f"{username} 获取token: %s" % token)
                        logger.info(f"{username} 验证url: {punish}")

                        while True:
                            try:
                                slider_data_resp = s.get(
                                    f"{server_ip}get_slider_data_225?ua_name={ua_name}&ua_version={ua_version}&token={_token}&url=https://detailskip.taobao.com/service/getData/1/p1/item/detail/sib.htm&is_pc=false", timeout=5)
                                slider_data_resp = slider_data_resp.json()
                                slide_data = {
                                    "a": app_key,
                                    "t": token,
                                    "p": "{\"nc_wvumidToken\":\"\",\"ncSessionID\":\"8b420e614c4\",\"umidToken\":\"\"}",
                                    "n": slider_data_resp["n"],
                                    "scene": slider_data_resp["scene"],
                                    "asyn": slider_data_resp["asyn"],
                                    "lang": slider_data_resp["lang"],
                                    "v": slider_data_resp["v"]
                                }
                                break
                            except Exception:
                                continue
                        param = {
                            "slidedata": json.dumps(slide_data).replace(" ", ""),
                            "x5secdata": x5sec,
                            "v": slider_data_resp["jsonp"]
                        }

                        # time.sleep(2)
                        slide_resp = requests.get(
                            "https://h5api.m.taobao.com:443//h5/mtop.trade.order.create.h5/4.0/_____tmd_____/slide", params=param, proxies=proxies, timeout=3, verify=False)
                        if (slide_resp.json().get("code") == 0):
                            if slide_resp.headers.get("Set-Cookie") is None:
                                break
                            elif requests.utils.dict_from_cookiejar(slide_resp.cookies).get("x5sec"):
                                _x5sec = requests.utils.dict_from_cookiejar(
                                    slide_resp.cookies)["x5sec"]
                                logger.info(f"{username} 获取x5sec " + _x5sec)
                                break
                        elif (slide_resp.json().get("code") == 300):
                            continue
                        else:
                            s.close()
                            logger.info(f"{username} {slide_resp.text}")
                            break
                    break
                except requests.exceptions.RequestException:
                    logger.info(f"{username} 代理超时")
                    s.close()
                except Exception as e:
                    logger.exception(e)
                    return
            logger.info(f"{username} 等待 {buy_time - now}")
            time.sleep(3)

        while True:
            now = datetime.now()
            if now >= buy_time:
                try:
                    t = str(round(time.time() * 1000))
                    data = '{"buyNow":"false","buyParam":"' + settlement + \
                        '","abtest_module":"dx2native","spm":"a21202.12579950.settlement-bar.0","exParams":"{\\"requestIdentity\\":\\"#t#ip##_h5_web_unknown\\",\\"tradeProtocolFeatures\\":\\"5\\",\\"userAgent\\":\\"' + ua + '\\"}"}'
                    sign = get_sign(f"{tk_token}&{t}&12574478&{data}")
                    req = s.post(
                        f"https://h5api.m.taobao.com/h5/mtop.trade.order.build.h5/4.0/?jsv=2.6.2&appKey=12574478&t={t}&sign={sign}&api=mtop.trade.order.build.h5&v=4.0&type=originaljson&ttid=%23t%23ip%23%23_h5_2019&isSec=1&ecode=1&AntiFlood=true&AntiCreep=true&H5Request=true&dataType=jsonp", data={"data": data}, proxies=proxies, timeout=3)
                    order_build_data = req.json()["data"]

                    # 抢单
                    submitref = order_build_data["global"]["secretValue"]
                    # 这些参数都是根据order_build_data顺序排序的
                    data = '{"params":"{\\"data\\":\\"{'
                    keys = ["itemInfo_", "item_", "invoice_", "promotion_", "deliveryDate_", "anonymous_",
                            "voucher_", "confirmOrder_", "service_yfx_", "ncCheckCode_", "memo_", "address_", "submitOrder_", "pocketMoney_"]
                    for k in order_build_data["data"]:
                        for _k in keys:
                            if _k in k:
                                item = order_build_data["data"][k]
                                if _k == "service_yfx_":
                                    item.update(
                                        {"id": k.split("service_")[1], "tag": "service"})
                                else:
                                    item.update(
                                        {"id": k.split("_")[1], "tag": k.split("_")[0]})
                                if _k in ("voucher_", "address_"):
                                    item["fields"]["cornerType"] = "both"
                                item_dict = json.dumps(item, ensure_ascii=False, separators=(
                                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
                                if _k in ("address_", "confirmOrder_", "deliveryDate_"):
                                    item_dict = item_dict.replace(
                                        r'\\\\\\\\\"', r'\\\\\\\\\\\\\\\"')
                                data += '\\\\\\"%s\\\\\\":%s,' % (k, item_dict)
                    data = data[:-1] + '}\\",'

                    linkage = {"common": {}, "signature": ""}
                    linkage["common"]["compress"] = order_build_data["linkage"]["common"]["compress"]
                    linkage["common"]["submitParams"] = order_build_data["linkage"]["common"]["submitParams"]
                    linkage["common"]["validateParams"] = order_build_data["linkage"]["common"]["validateParams"]
                    linkage["signature"] = order_build_data["linkage"]["signature"]
                    linkage_dict = json.dumps(linkage, ensure_ascii=False, separators=(
                        ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
                    hierarchy_structure_dict = json.dumps(order_build_data["hierarchy"]["structure"], ensure_ascii=False, separators=(
                        ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
                    endpoint_dict = json.dumps(order_build_data["endpoint"], ensure_ascii=False, separators=(
                        ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')

                    data += '\\"linkage\\":\\"%s\\",\\"hierarchy\\":\\"{\\\\\\"structure\\\\\\":%s}\\",\\"endpoint\\":\\"%s\\"}"}' % (
                        linkage_dict, hierarchy_structure_dict, endpoint_dict)

                    c = requests.cookies.RequestsCookieJar()
                    c.set("x5sec", _x5sec)
                    s.cookies.update(c)
                    source_time = str(int(buy_time.timestamp()) * 1000)
                    sign = get_sign(f"{tk_token}&{source_time}&12574478&{data}")
                    sib_resp = s.post("https://h5api.m.taobao.com/h5/mtop.trade.order.create.h5/4.0/?jsv=2.6.2&appKey=12574478&t=%s&sign=%s&v=4.0&post=1&type=originaljson&timeout=15000&dataType=json&isSec=1&ecode=1&api=mtop.trade.order.create.h5&ttid=%s&H5Request=true&submitref=%s" %
                                      (source_time, sign, "%23t%23ip%23%23_h5_2019", submitref), data={"data": data}, proxies=proxies, timeout=3)
                    logger.info(f"{username} 抢单成功，请去支付 {sib_resp.text}")
                except requests.exceptions.RequestException:
                    s.close()
                except Exception as e:
                    logger.exception(e)
                finally:
                    break
            time.sleep(0.1)
    except Exception as e:
        logger.exception(e)


if __name__ == "__main__":
    logger.add('log/boss_{time:YYYY-MM-DD}.log', rotation='00:00', retention='7 days')

    # excel_file = r".\ck.xls"
    # path = r"./"
    # files = os.listdir("./")
    # for file in files:
    #     if file.endswith(".xls") or file.endswith(".xlsx"):
    #         data = xlrd.open_workbook(os.path.join(path, file))
    #         sheet = data.sheet_by_index(0)
    #         with get_connection() as conn:
    #             with conn.cursor() as cursor:
    #                 for user, ck in zip(sheet.col_values(0), sheet.col_values(1)):
    #                     cursor.execute(
    #                         "insert ignore into o2o_test_xy_ck (username, ck) values (%s, %s)", [user, ck])
    #                     conn.commit()
    #                     logger.info(f"入库 {user}")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("select * from o2o_test_xy_ck")
            res = cursor.fetchall()
    for username, ck in res:
        ck = dict([c.strip().split("=", 1) for c in ck.strip().split(";") if c])
        t = Thread(target=main, args=(username, ck,))
        t.start()
        time.sleep(1)
