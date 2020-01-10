# coding=utf-8

import asyncio
import json
import re
import time
from datetime import datetime, timedelta

import execjs
import requests
from pyppeteer import launch

from conf import buy_time, cart_id, cookies_duration, pw, user

buy_time = datetime.strptime(buy_time, "%Y-%m-%d %H:%M:%S.%f")


s = requests.Session()


# TODO cookies检测失效后再次获取，自动获取cart_id，多收货地址，多订单
async def get_cookies():
    with open("./cookies.json", "r") as f:
        obj = json.load(f)
        ct = datetime.strptime(obj["create_time"], "%Y-%m-%d %H:%M:%S.%f")
    if datetime.now() - ct < timedelta(minutes=cookies_duration) and user == obj["cookies"].get("tracknick"):
        return obj["cookies"]
    else:
        try:
            launch_args = {
                "headless": False,  # 无头
                "dumpio": True,  # 避免卡死
                # 浏览器窗口大小，禁用提示条
                "args": ["--windows-size=800,1280", "--disable-infobars"]
            }
            driver = await launch(launch_args)
            page = await driver.newPage()
            await page.setUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36")
            await page.setViewport(viewport={"width": 462, "height": 824})

            # 修改浏览器属性值，防止被检测是爬虫
            await page.evaluateOnNewDocument("() => { Object.defineProperties(navigator, { webdriver: { get: () => false }})}")
            await page.evaluateOnNewDocument("() => { Object.defineProperty(navigator, 'plugins', { get: () => []})}")
            await page.evaluateOnNewDocument("() => { Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh']})}")

            await page.goto("https://main.m.taobao.com/cart/index.html?")
            await page.waitFor("iframe")
            iframe = page.frames[1]
            await iframe.type("#username", user, {"delay": 100})
            await iframe.type("#password", pw, {"delay": 100})
            await iframe.click("#btn-submit")
            await iframe.waitFor(2000)

            # 判断是否出现验证
            # vs = await iframe.Jeval("div.km-dialog.km-dialog-ios7.km-dialog-alert", "node => node.style.visibility")
            # if vs == "visible":
            #     await iframe.click("div.km-dialog.km-dialog-ios7.km-dialog-alert > div.km-dialog-buttons > span")
            #     await iframe.click("#SM_BTN_1")
            #     await iframe.type("#password", pw, {"delay": 100})
            #     await iframe.click("#btn-submit")
            # 等待指定元素
            await page.waitFor("#cart_sticky_fixed_bar")
            cookies = await page.cookies()
            cookies = {c["name"]: c["value"] for c in cookies}
            await driver.close()
            with open("./cookies.json", "w") as f:
                obj = {"create_time": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S.%f"), "cookies": cookies}
                json.dump(obj, f, ensure_ascii=False, indent=4)
            return cookies
        except Exception as e:
            print(e)
            await driver.close()
            raise


def main(cookies):
    # 抢单
    try:
        # 忽略安全警告
        requests.packages.urllib3.disable_warnings()
        # 添加cookies等配置
        cj = requests.utils.cookiejar_from_dict(
            cookies, cookiejar=None, overwrite=True)
        s.cookies = cj
        s.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        s.verify = False

        token = cookies["_m_h5_tk"].split("_")[0]
        with open('./s.js') as f:
            js = f.read()
            context = execjs.compile(js)
        # 还剩30秒时，获取一些参数
        order_build_data = None
        while True:
            now = datetime.now()
            if now - buy_time >= timedelta(seconds=30):
                try:
                    source_time = str(int(round(time.time(), 3) * 1000))
                    data = '{"isPage":True,"extStatus":0,"netType":0,"exParams":"{\\"mergeCombo\\":\\"True\\",\\"version\\":\\"1.1.1\\",\\"globalSell\\":\\"1\\",\\"cartFrom\\":\\"taobao_client\\",\\"spm\\":\\"a2141.7756461.toolbar.i1\\",\\"dataformat\\":\\"dataformat_ultron_h5\\"}","cartFrom":"taobao_client","spm":"a2141.7756461.toolbar.i1","dataformat":"dataformat_ultron_h5","ttid":"h5"}'
                    req = s.get("https://h5api.m.taobao.com/h5/mtop.trade.query.bag/5.0/?jsv=2.5.6&appKey=12574478&t=%s&sign=%s&api=mtop.trade.query.bag&v=5.0&type=jsonp&ttid=h5&isSec=0&ecode=1&AntiFlood=True&AntiCreep=True&H5Request=True&dataType=jsonp&callback=mtopjsonp2&data=%s" %
                                (source_time, context.call("s", token + "&" + source_time + "&12574478&" + data), data))
                    query_bag_data = json.loads(
                        re.match(".*?({.*}).*", req.text, re.S).group(1))["data"]
                    # 防止请求过快
                    time.sleep(5)
                    source_time = str(int(round(time.time(), 3) * 1000))
                    data = '{"buyNow":"false","buyParam":"%s","spm":"a21202.12579950.settlement-bar.0","exParams":"{\\"tradeProtocolFeatures\\":\\"5\\",\\"userAgent\\":\\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36\\"}"}' % query_bag_data[
                        "data"]["item_" + cart_id]["fields"]["settlement"]
                    req = s.post("https://h5api.m.taobao.com/h5/mtop.trade.order.build.h5/4.0/?jsv=2.5.7&appKey=12574478&t=%s&sign=%s&api=mtop.trade.order.build.h5&v=4.0&type=originaljson&ttid=%s&isSec=1&ecode=1&AntiFlood=True&AntiCreep=True&H5Request=True&dataType=jsonp" %
                                 (source_time, context.call("s", token + "&" + source_time + "&12574478&" + data), "%23t%23ip%23%23_h5_2019"), data={"data": data})
                    order_build_data = req.json()["data"]
                    break
                except Exception:
                    raise
        # 抢单
        submitref = order_build_data["global"]["secretValue"]
        # 这些参数都是根据order_build_data顺序排序的
        data = '{"params":"{\\"data\\":\\"{'
        keys = ["itemInfo_", "item_", "invoice_", "promotion_", "deliveryMethod_", "anonymous_",
                "voucher_", "confirmOrder_", "service_yfx_", "ncCheckCode_", "memo_", "address_", "submitOrder_"]
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
                    if _k in ("address_", ):
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

        source_time = str(int(buy_time.timestamp()) * 1000)
        sign = context.call("s", token + "&" + source_time + "&12574478&" + data)
        while True:
            now = datetime.now()
            if now >= buy_time:
                try:
                    req = s.post("https://h5api.m.taobao.com/h5/mtop.trade.order.create.h5/4.0/?jsv=2.5.7&appKey=12574478&t=%s&sign=%s&v=4.0&post=1&type=originaljson&timeout=15000&dataType=json&isSec=1&ecode=1&api=mtop.trade.order.create.h5&ttid=%s&H5Request=true&submitref=%s" %
                                 (source_time, sign, "%23t%23ip%23%23_h5_2019", submitref), data={"data": data})
                    print("抢单成功，请去支付")
                    break
                except Exception:
                    raise
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(get_cookies())
    loop.run_until_complete(task)
    cookies = task.result()
    main(cookies)
