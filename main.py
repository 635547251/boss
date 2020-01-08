# coding=utf-8

import asyncio
import json
import time
import re
from datetime import datetime, timedelta

import js2py
import requests
from pyppeteer import launch

from conf import buytime, cart_id, item_id, pw, seller_id, sku_id, user, cookies_duration

buytime = datetime.strptime(buytime, "%Y-%m-%d %H:%M:%S.%f")


s = requests.Session()


# TODO cookies检测失效后再次获取，自动获取cart_id，多收货地址，多订单
async def get_cookies():
    with open("./cookies.json", "r") as f:
        obj = json.load(f)
        ct = datetime.strptime(obj["create_time"], "%Y-%m-%d %H:%M:%S.%f")
    if datetime.now() - ct < timedelta(minutes=cookies_duration) and user == obj["cookies"]["tracknick"]:
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
        # # 忽略安全警告
        # requests.packages.urllib3.disable_warnings()
        # # 添加cookies等配置
        # cj = requests.utils.cookiejar_from_dict(
        #     cookies, cookiejar=None, overwrite=True)
        # s.cookies = cj
        # s.headers = {
        #     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
        #     "Content-Type": "application/x-www-form-urlencoded"
        # }
        # s.verify = False

        # token = cookies["_m_h5_tk"].split("_")[0]
        # with open('./s.js') as f:
        #     js = f.read()
        #     context = js2py.EvalJs()
        #     context.execute(js)
        # # 还剩30秒时，获取一些参数
        # query_bag_data, order_build_data = None, None
        # while True:
        #     now = datetime.now()
        #     if now - buytime >= timedelta(seconds=30):
        #         try:
        #             source_time = str(int(round(time.time(), 3) * 1000))
        #             data = '{"isPage":True,"extStatus":0,"netType":0,"exParams":"{\\"mergeCombo\\":\\"True\\",\\"version\\":\\"1.1.1\\",\\"globalSell\\":\\"1\\",\\"cartFrom\\":\\"taobao_client\\",\\"spm\\":\\"a2141.7756461.toolbar.i1\\",\\"dataformat\\":\\"dataformat_ultron_h5\\"}","cartFrom":"taobao_client","spm":"a2141.7756461.toolbar.i1","dataformat":"dataformat_ultron_h5","ttid":"h5"}'
        #             req = s.get("https://h5api.m.taobao.com/h5/mtop.trade.query.bag/5.0/?jsv=2.5.6&appKey=12574478&t=%s&sign=%s&api=mtop.trade.query.bag&v=5.0&type=jsonp&ttid=h5&isSec=0&ecode=1&AntiFlood=True&AntiCreep=True&H5Request=True&dataType=jsonp&callback=mtopjsonp2&data=%s" %
        #                         (source_time, context.s(token + "&" + source_time + "&12574478&" + data), data))
        #             query_bag_data = json.loads(
        #                 re.match(".*?({.*}).*", req.text, re.S).group(1))["data"]

        #             source_time = str(int(round(time.time(), 3) * 1000))
        #             data = '{"buyNow":"false","buyParam":"%s","spm":"a21202.12579950.settlement-bar.0","exParams":"{\\"tradeProtocolFeatures\\":\\"5\\",\\"userAgent\\":\\"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36\\"}"}' % query_bag_data[
        #                 "data"]["item_" + cart_id]["fields"]["settlement"]
        #             req = s.post("https://h5api.m.taobao.com/h5/mtop.trade.order.build.h5/4.0/?jsv=2.5.7&appKey=12574478&t=%s&sign=%s&api=mtop.trade.order.build.h5&v=4.0&type=originaljson&ttid=%s&isSec=1&ecode=1&AntiFlood=True&AntiCreep=True&H5Request=True&dataType=jsonp" %
        #                          (source_time, context.s(token + "&" + source_time + "&12574478&" + data), "%23t%23ip%23%23_h5_2019"), data={"data": data})
        #             order_build_data = req.json()["data"]
        #             break
        #         except Exception:
        #             raise

        with open("/Users/phil/Desktop/data.json", "r") as f:
            order_build_data = json.load(f)["data"]
        # 抢单
        submitref = order_build_data["global"]["secretValue"]

        # 这些参数都是根据order_build_data顺序排序的
        # address = order_build_data["data"]["address_1"]
        # address.update({"id": "1", "tag": "address"})
        # print(json.dumps(address, ensure_ascii=False, separators=(
        #     ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"'))

        for k in order_build_data["data"]:
            if "itemInfo_" in k:
                item_info = order_build_data["data"][k]
                item_info.update({"id": k.split("_")[1], "tag": "itemInfo"})
                item_info_dict = json.dumps(item_info, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "item_" in k:
                item = order_build_data["data"][k]
                item.update({"id": k.split("_")[1], "tag": "item"})
                item_dict = json.dumps(item, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "invoice_" in k:
                invoice = order_build_data["data"][k]
                invoice.update({"id": k.split("_")[1], "tag": "invoice"})
                invoice_dict = json.dumps(invoice, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            # 有多个
            elif "promotion_" in k:
                promotion = order_build_data["data"][k]
                promotion.update({"id": k.split("_")[1], "tag": "promotion"})
                promotion_dict = json.dumps(promotion, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "deliveryMethod_" in k:
                delivery_method = order_build_data["data"][k]
                delivery_method.update(
                    {"id": k.split("_")[1], "tag": "deliveryMethod"})
                delivery_method_dict = json.dumps(delivery_method, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "anonymous_" in k:
                anonymous = order_build_data["data"][k]
                anonymous.update({"id": k.split("_")[1], "tag": "anonymous"})
                anonymous_dict = json.dumps(anonymous, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "voucher_" in k:
                voucher = order_build_data["data"][k]
                voucher.update({"id": k.split("_")[1], "tag": "voucher"})
                voucher["fields"]["cornerType"] = "both"
                voucher_dict = json.dumps(voucher, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "confirmOrder_" in k:
                confirm_order = order_build_data["data"][k]
                confirm_order.update(
                    {"id": k.split("_")[1], "tag": "confirmOrder"})
                confirm_order_dict = json.dumps(confirm_order, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "service_yfx_" in k:
                service_yfx = order_build_data["data"][k]
                service_yfx.update(
                    {"id": k.split("service_")[1], "tag": "service"})
                service_yfx_dict = json.dumps(service_yfx, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "ncCheckCode_" in k:
                check_code = order_build_data["data"][k]
                check_code.update(
                    {"id": k.split("_")[1], "tag": "ncCheckCode"})
                check_code_dict = json.dumps(check_code, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "submitOrder_1" in k:
                submit_order = order_build_data["data"][k]
                submit_order.update({"id": "1", "tag": "submitOrder"})
                submit_order_dict = json.dumps(submit_order, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
            elif "memo_" in k:
                memo = order_build_data["data"][k]
                memo.update({"id": k.split("_")[1], "tag": "memo"})
                memo_dict = json.dumps(memo, ensure_ascii=False, separators=(
                    ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')


        hierarchy_structure_dict = json.dumps(order_build_data["hierarchy"]["structure"], ensure_ascii=False, separators=(
            ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
        endpoint_dict = json.dumps(order_build_data["endpoint"], ensure_ascii=False, separators=(
            ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')
        print(endpoint_dict)

        # while True:
        #     now = datetime.now()
        #     if now >= buytime:
        #         try:
        #             bt = time.time()

        #             source_time = str(int(round(time.time(), 3) * 1000))
        #             data = '{"isPage":True,"extStatus":0,"netType":0,"exParams":"{\\"mergeCombo\\":\\"True\\",\\"version\\":\\"1.1.1\\",\\"globalSell\\":\\"1\\",\\"cartFrom\\":\\"taobao_client\\",\\"spm\\":\\"a2141.7756461.toolbar.i1\\",\\"dataformat\\":\\"dataformat_ultron_h5\\"}","cartFrom":"taobao_client","spm":"a2141.7756461.toolbar.i1","dataformat":"dataformat_ultron_h5","ttid":"h5"}'
        #             req = s.post("https://h5api.m.taobao.com/h5/mtop.trade.order.create.h5/4.0/?jsv=2.5.7&appKey=12574478&t=%s&sign=%s&v=4.0&post=1&type=originaljson&timeout=15000&dataType=json&isSec=1&ecode=1&api=mtop.trade.order.create.h5&ttid=%s&H5Request=True&submitref=%s" %
        #                          (source_time, context.s(token + "&" + source_time + "&12574478&" + data), "%23t%23ip%23%23_h5_2019", submitref))
        #             b = req.json()
        #             print(b)
        #             print(type(b))
        #             print(time.time() - bt)
        #             time.sleep(2)
        #             break
        #         except Exception:
        #             raise
    except Exception as e:
        print(e)
        raise


if __name__ == "__main__":
    # loop = asyncio.get_event_loop()
    # task = asyncio.ensure_future(get_cookies())
    # loop.run_until_complete(task)
    # cookies = task.result()
    main({})
    '''
    {"params":"{\"data\":\"{\\\"itemInfo_ab96af10ec01db7dfd2b9fbefe406c91\\\":"%s",\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\":"%s",\\\"address_1\\\":{\\\"ref\\\":\\\"f83ecc7\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"useMDZT\\\":\\\"false\\\",\\\"useStation\\\":\\\"false\\\",\\\"lng\\\":\\\"121.35150025\\\",\\\"selectedId\\\":\\\"1247011080\\\",\\\"linkAddressId\\\":\\\"0\\\",\\\"options\\\":\\\"[{\\\\\\\"addressDetail\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"addressIconUrl\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"agencyReceiveDesc\\\\\\\":\\\\\\\"收货不便时,可选择免费暂存服务\\\\\\\",\\\\\\\"areaName\\\\\\\":\\\\\\\"普陀区\\\\\\\",\\\\\\\"attributes\\\\\\\":[],\\\\\\\"baseDeliverAddressDO\\\\\\\":{\\\\\\\"address\\\\\\\":\\\\\\\"310107^^^上海^^^上海市^^^普陀区^^^桃浦镇 红棉路310弄8号401室^^^ ^^^桃浦镇^^^310107103^^^31.2832337507^^^121.35150025\\\\\\\",\\\\\\\"addressDetail\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"addressDetailWithoutTown\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"algorithmFrom\\\\\\\":\\\\\\\"cainiao#Mon Oct 28 22:38:33 CST 2019\\\\\\\",\\\\\\\"area\\\\\\\":\\\\\\\"普陀区\\\\\\\",\\\\\\\"chinaAddress\\\\\\\":true,\\\\\\\"city\\\\\\\":\\\\\\\"上海市\\\\\\\",\\\\\\\"confidence\\\\\\\":96,\\\\\\\"country\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"cuntaoAddress\\\\\\\":false,\\\\\\\"devisionCode\\\\\\\":\\\\\\\"310107\\\\\\\",\\\\\\\"eleAddress\\\\\\\":false,\\\\\\\"extraInfo\\\\\\\":\\\\\\\"{\\\\\\\\\\\\\\\"checkInf\\\\\\\\\\\\\\\":\\\\\\\\\\\\\\\"cainiao#Mon Oct 28 22:38:33 CST 2019\\\\\\\\\\\\\\\"}\\\\\\\",\\\\\\\"fullMobile\\\\\\\":\\\\\\\"86-17621951401\\\\\\\",\\\\\\\"fullName\\\\\\\":\\\\\\\"杜鹏飞\\\\\\\",\\\\\\\"gmtCreate\\\\\\\":1375542543000,\\\\\\\"gmtModified\\\\\\\":1556008689000,\\\\\\\"guoguoAddress\\\\\\\":false,\\\\\\\"helpBuyAddress\\\\\\\":false,\\\\\\\"id\\\\\\\":1247011080,\\\\\\\"illegalCunTaoAddress\\\\\\\":false,\\\\\\\"minDivisonCode\\\\\\\":\\\\\\\"310107103\\\\\\\",\\\\\\\"mobile\\\\\\\":\\\\\\\"17621951401\\\\\\\",\\\\\\\"mobileInternationalCode\\\\\\\":\\\\\\\"86\\\\\\\",\\\\\\\"needToUpgrade\\\\\\\":false,\\\\\\\"pOIAddress\\\\\\\":false,\\\\\\\"postCode\\\\\\\":\\\\\\\"200331\\\\\\\",\\\\\\\"province\\\\\\\":\\\\\\\"上海\\\\\\\",\\\\\\\"qinQingAddress\\\\\\\":false,\\\\\\\"status\\\\\\\":0,\\\\\\\"tag\\\\\\\":0,\\\\\\\"town\\\\\\\":\\\\\\\"桃浦镇\\\\\\\",\\\\\\\"townDivisionCode\\\\\\\":\\\\\\\"310107103\\\\\\\",\\\\\\\"userId\\\\\\\":1774425903,\\\\\\\"versionObject\\\\\\\":7,\\\\\\\"x\\\\\\\":\\\\\\\"31.2832337507\\\\\\\",\\\\\\\"y\\\\\\\":\\\\\\\"121.35150025\\\\\\\"},\\\\\\\"checked\\\\\\\":false,\\\\\\\"cityName\\\\\\\":\\\\\\\"上海市\\\\\\\",\\\\\\\"consolidationGuide\\\\\\\":false,\\\\\\\"countryName\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"defaultAddress\\\\\\\":false,\\\\\\\"deliveryAddressId\\\\\\\":1247011080,\\\\\\\"disable\\\\\\\":false,\\\\\\\"divisionCode\\\\\\\":\\\\\\\"310107\\\\\\\",\\\\\\\"enableMDZT\\\\\\\":false,\\\\\\\"enableStation\\\\\\\":false,\\\\\\\"enforceUpdate4Address\\\\\\\":true,\\\\\\\"fullName\\\\\\\":\\\\\\\"杜鹏飞\\\\\\\",\\\\\\\"hidden\\\\\\\":false,\\\\\\\"id\\\\\\\":\\\\\\\"1872428\\\\\\\",\\\\\\\"lat\\\\\\\":\\\\\\\"31.2832337507\\\\\\\",\\\\\\\"lgShopId\\\\\\\":0,\\\\\\\"lng\\\\\\\":\\\\\\\"121.35150025\\\\\\\",\\\\\\\"mainland\\\\\\\":true,\\\\\\\"mobile\\\\\\\":\\\\\\\"17621951401\\\\\\\",\\\\\\\"name\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"needUpdate4Address\\\\\\\":false,\\\\\\\"needUpgradeAddress\\\\\\\":false,\\\\\\\"platformType\\\\\\\":\\\\\\\"H5\\\\\\\",\\\\\\\"postCode\\\\\\\":\\\\\\\"200331\\\\\\\",\\\\\\\"provinceName\\\\\\\":\\\\\\\"上海\\\\\\\",\\\\\\\"stationId\\\\\\\":0,\\\\\\\"status\\\\\\\":\\\\\\\"normal\\\\\\\",\\\\\\\"storeAddress\\\\\\\":true,\\\\\\\"townDivisionId\\\\\\\":310107103,\\\\\\\"townName\\\\\\\":\\\\\\\"桃浦镇\\\\\\\",\\\\\\\"updateAddressTip\\\\\\\":\\\\\\\"\\\\\\\"}]\\\",\\\"sites\\\":\\\"[]\\\",\\\"lat\\\":\\\"31.2832337507\\\"}},\\\"type\\\":\\\"dinamicx$461$buyaddress\\\",\\\"fields\\\":{\\\"mobilephone\\\":\\\"17621951401\\\",\\\"name\\\":\\\"杜鹏飞\\\",\\\"iconUrl\\\":\\\"https://gw.alicdn.com/tfs/TB17gX2wYvpK1RjSZPiXXbmwXXa-128-128.png\\\",\\\"value\\\":\\\"上海上海市普陀区桃浦镇红棉路310弄8号401室\\\",\\\"desc\\\":\\\"收货不便时,可选择免费暂存服务\\\",\\\"cornerType\\\":\\\"both\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{\\\"fields\\\":{\\\"info\\\":{\\\"value\\\":\\\"1247011080\\\"}}},\\\"url\\\":\\\"//buy.m.tmall.com/order/addressList.htm?enableStation=true&requestStationUrl=%2F%2Fstationpicker-i56.m.taobao.com%2Finland%2FshowStationInPhone.htm&_input_charset=utf8&hidetoolbar=true&bridgeMessage=true\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"address\\\"},\\\"invoice_2f426b0c3ea8b56f75ad8354ad85afd7\\\":"%s",\\\"promotion_2f426b0c3ea8b56f75ad8354ad85afd7\\\":"%s",\\\"deliveryMethod_2f426b0c3ea8b56f75ad8354ad85afd7\\\":"%s",\\\"anonymous_1\\\":"%s",\\\"voucher_1\\\":"%s",\\\"confirmOrder_1\\\":"%s",\\\"service_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\":"%s",\\\"ncCheckCode_ncCheckCode1\\\":"%s",\\\"submitOrder_1\\\":"%s",\\\"promotion_ab96af10ec01db7dfd2b9fbefe406c91\\\":"%s",\\\"memo_2f426b0c3ea8b56f75ad8354ad85afd7\\\":"%s"}\",\"linkage\":\"{\\\"common\\\":{\\\"compress\\\":true,\\\"submitParams\\\":\\\"^^$$Z2df6357cdbb668d73d1aa79bbd13ac29b|null{$_$}H4sIAAAAAAAAAM1X227cyBH9lQENLHYBLdW8D7UwAnkkrxVbl0gjbxZBQDTJpqYjks10NyWPDBv7vtm85S1AXgLkF4zkd2zkN3K6ybnIhr1GLkBgQOYUq6uqT1WdKr50Kkkbdivk9RnFkzpqutrZe+l0NdWVkM182THzu6ipUidQdfacQjQurXlOc+pqSUvmFjVnrXYbUbLaVaKXBXPPtiw8950dpx1OP4nwLGTJWwpP5NWO09Er9jE/moqcChcuO9EaH+USdnjhNkzTLbFRqNkL99Hl9757tjI42EbIV6xlEv52nJKpAoJ//uMvb9/88PbNj+9++hOkDZXXTEO+ifPbw5PD8/1nEKyDTRFsLQpaGxTuFtnsxIGkV0zuK8Wv2s8GCiduODAqJKOat1ensmTSlez3PVPanW1LzwfhEAaTB/NT5ez95qXD1X4r2mUjevyuaK0YImm5aK2tAc6vPRs8k894yzYnNWuOShPrGMYjfjfokx2Hjy9j4idBFKU+8eIdR1335kQYeqHnR3FKwhS6BZXaiL0kIlOSTP0wTtItj/ZdTKJ4CgvDjS8GQy9fATfR29MOzdOYVh5hBfHKPCmr0s/TKmcVC0lcpB6unvfLX/W01Vwv4Q5Rtjeb38RFLDm/m6H6kBdUplssUF2ubmhdu7Trak7bghk7ha1yaMEikzPRllwDs9fk9euyyy+7K1PO5pe5m80Dm/OGvfaiZBrggtOYEAJDnRSNMCeBqkGSq8eQ/HKhDlCWHHU9ZkTnM9HkwiCBIG1Aa4FjDG1Ep52xZ/U2oSBSYmoMF0bxC7kc/d1SyRZIvcmqrbrh7sdH2ZMDWB1b7d1Pf3z75s/v/vq3d3/4u/Fle9kjBnzbtxdDUmzFDIbwBkjuay153muG0kLrAwqOCzj38myigurhC81atQYCwqHVNMOJEQSuTk2qj9rTunwMTqFoNPvq1W83VeBXoR/npAgYneZRXCURLadBFOJvRKsyQfw2Z8dMKbQ3woEEdMNv2BoVWpYSr1c5GUCveXu9P7wY01DyG25CHgoGyRsURV1aBQMPeyauuNK8GE/+F0y2jJVqZVZZzNcISVYwXOSY6YUoh150WoNUbWD+eK4WVD3nUve0PkLfrs3RD/Jnsge8QBCmg/AMsx9Ni+nWumbSoOElpuWnXjA1ybIZGMRJGPpRSgJDDryz1zlsaQ60r9ZxrN9c0Jt78oXoOgjO6LJBWY/gIquthmhVHLBsJ4mpwZZpM6PwiMBLZshzhOnw+Gz+Pa62PbAwbvYcO2c2o8XZ8LlaKqD13vm8VyBJpUaxWqDDYFYYZja9baLQaKBxBj4+Pz3OZvvn8+zy4vAcihV0HvXLE3G7id/IbEMXoq24bCxKF9a7pbF79L+Sg5atxujolnawjsna1yvfpiFNAhuRczOKENjQoA/0A949eJAtogy8neIcyO85k6bYgchaxkfbjRbdOMHtPd2853XpLsyEph3/4GRPYeVY3PG6pruRSyZfYrD0L76Z7LelFLychG7o+t9Mfj0HX5LJI2Nt9+npPEyffDXZBw+z71j+lOvdKEjcIJ58+fTJ/PjZzqTm12zyLSuuxVeT0eluCPOzBQBkuwEY3vybHNsLTy5oRSUfjSBUru4BP0zk96uUqxN2u77RyEyq7zoh9TnDroL+u5Qb5h6HsUn9MWDaJFVhRA4F4WD+m1HAhURbrQb1SG1AECRdzuyMBI8auoJqMTI20vchezpsxabHyDrymmXZ7wRvM17iCTa82Pcxf/3pNAzSzHQ05KCHghmVGow16JEcXUtoYsZWGJEkjNMgNYcZhndgjzU6o+VNxkzPssG4kUvWouAzjaFnHa4MJIRYCuZ38IQ+HXjkU7O26JUWTWa2o0xpusyozsY+yGy1ZaY5zaV8zFQ7VdtitkAVGF7OWnb7uKbgEktc22+0uGamnPO4YnGeVGYrSf24ZIR6aZLQhBQRictpPA2KNPYNShLLhJRM4tRC607t7e42lLdu4272y10b1C7H/V+4C93UvwDboZ0f2lr5Aj/s7vBwezPKvOzeTpS1fV1nZPjPPt+bmVvybUWY/rd3ETjbdmfNfvLPF6prHlIfoPsudrkkTSPiKqZ1zQwXf51T6ZrFRDIsOIyjDB3PS1wv8FzPc9OpfWVq5LC94VK05hB0Lg6e+m6Il4pjajgBtsE4p5QWmOE09oK4IgVLU5RhmhJiCKZvrObtcy++i5gX+uW0DChLqE8pIZ5XsYBFZWUcGtX5mPV5RKKI0TgsCAn8fJqURexHU+bl4dSv4qIw+qg5O00Qyf8bXZntAt9S+gJbqbYD4ai0a9bPLkDvtT/umZZxFGJA+yEe4siP47CcJmHlF3kQEp+Y3N1jDPMZ9rPr9vuH7LLQdyXVzMa7+jxZEx6+Fs3a1Us2x+fLevqvd+Thy3KY3VzNRI9PuUuF1l+xsGbdibCDcn3mgKtC9K1+zKBn9nvTI4bT8fwfrQVnM2Dwv10L8A16cvod3GzvBFr2DKn/5EqAu33OSgAsYPzeSgBRi80DDj5zPJkyHMPDsmSD+xddNjizDBAAAA==\\\",\\\"validateParams\\\":\\\"^^$$3830b7703307690f7108dc0cf329632c{$_$}H4sIAAAAAAAAAIWRzUrDQBSF32XWYUijTUh3SRp/QErxp+BKbmdu09DJTJiZorUU3ItL176G4OtUfA1vLGo34u7O4c45Z75Zs5mFBm+NXYyBJnfatIoN1qxV4GfGNperFruzUODciFbZgAnTcFD1FKbAvQWJXKgateeNkai4M0srkI/3HCYRC5je3T7p02ysrDVQUrgJWAsV/pXjwUzBcIpsje4y5Ip8asEb9LAndwsK73h+dR3x8bfhzpsqV6jRUl7AJDpBwsfby/b1Yfv6+P70TGoDdoGe9N+ex+WoPM/OSPgpm1JZZQSojsL9/KYYMVKWDm3mXF3p/0G5OViUvLXo6DHga6N524HnQ/AwIary6x92wBBlMUexKIgrG8xAOQwYamFXrb/wttYV9ciHWT+MkijtxVF5WIZxr8yjKD46KPMkS6KyyNM4jpNeHGZ5mOYZ22w+ASTVTzT2AQAA\\\"},\\\"signature\\\":\\\"6960a65f38e64305dfac5d8fa113bca0\\\"}\",\"hierarchy\":\"{\\\"structure\\\":"%s"}\",\"endpoint\":\"{\\\"mode\\\":\\\"\\\",\\\"features\\\":\\\"5\\\",\\\"osVersion\\\":\\\"H5\\\",\\\"protocolVersion\\\":\\\"3.0\\\",\\\"ultronage\\\":\\\"true\\\"}\"}"}
    '''

    '''
    {"params":"{\"data\":\"{\\\"itemInfo_ab96af10ec01db7dfd2b9fbefe406c91\\\":{\\\"ref\\\":\\\"f36c1fb\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"bizCode\\\":\\\"ali.china.tmall.appliance\\\"}},\\\"type\\\":\\\"dinamicx$546$buyitem\\\",\\\"fields\\\":{\\\"skuLevel\\\":[],\\\"timeLimit\\\":\\\"\\\",\\\"subtitles\\\":\\\"表壳尺寸:其他;表带尺寸:适合 150-200 毫米腕围;表系列:黑色;\\\",\\\"price\\\":\\\"￥1299.00\\\",\\\"icon\\\":\\\"//gw.alicdn.com/imgextra/i4/1714128138/O1CN01L0m7Pt29zFlBi3yBH_!!1714128138.jpg\\\",\\\"count\\\":\\\"x1\\\",\\\"weight\\\":\\\"\\\",\\\"disabled\\\":\\\"false\\\",\\\"services\\\":[{\\\"value\\\":\\\"天猫无忧购\\\"},{\\\"value\\\":\\\"15天价保\\\"},{\\\"value\\\":\\\"七天无理由退换\\\"}],\\\"title\\\":\\\"【年货价】【天猫V榜推荐】小米手表运动跑步NFC男女款学生多功能小型智能手机手环支付宝付款wifi手表小爱同学支持eSIM\\\",\\\"icons\\\":[{\\\"value\\\":\\\"//gw.alicdn.com/tfs/TB15VswpYr1gK0jSZFDXXb9yVXa-84-36.png\\\"}]},\\\"id\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"tag\\\":\\\"itemInfo\\\"},\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\":{\\\"ref\\\":\\\"360f46f\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"valid\\\":\\\"true\\\",\\\"itemId\\\":\\\"602735592016\\\",\\\"bizCode\\\":\\\"ali.china.tmall.appliance\\\",\\\"cartId\\\":\\\"1750807824679\\\",\\\"shoppingOrderId\\\":\\\"0\\\",\\\"villagerId\\\":\\\"0\\\",\\\"skuId\\\":\\\"4414125690490\\\"}},\\\"type\\\":\\\"block$null$emptyBlock\\\",\\\"fields\\\":{},\\\"id\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"tag\\\":\\\"item\\\"},\\\"address_1\\\":{\\\"ref\\\":\\\"f83ecc7\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"useMDZT\\\":\\\"false\\\",\\\"useStation\\\":\\\"false\\\",\\\"lng\\\":\\\"121.35150025\\\",\\\"selectedId\\\":\\\"1247011080\\\",\\\"linkAddressId\\\":\\\"0\\\",\\\"options\\\":\\\"[{\\\\\\\"addressDetail\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"addressIconUrl\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"agencyReceiveDesc\\\\\\\":\\\\\\\"收货不便时,可选择免费暂存服务\\\\\\\",\\\\\\\"areaName\\\\\\\":\\\\\\\"普陀区\\\\\\\",\\\\\\\"attributes\\\\\\\":[],\\\\\\\"baseDeliverAddressDO\\\\\\\":{\\\\\\\"address\\\\\\\":\\\\\\\"310107^^^上海^^^上海市^^^普陀区^^^桃浦镇 红棉路310弄8号401室^^^ ^^^桃浦镇^^^310107103^^^31.2832337507^^^121.35150025\\\\\\\",\\\\\\\"addressDetail\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"addressDetailWithoutTown\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"algorithmFrom\\\\\\\":\\\\\\\"cainiao#Mon Oct 28 22:38:33 CST 2019\\\\\\\",\\\\\\\"area\\\\\\\":\\\\\\\"普陀区\\\\\\\",\\\\\\\"chinaAddress\\\\\\\":true,\\\\\\\"city\\\\\\\":\\\\\\\"上海市\\\\\\\",\\\\\\\"confidence\\\\\\\":96,\\\\\\\"country\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"cuntaoAddress\\\\\\\":false,\\\\\\\"devisionCode\\\\\\\":\\\\\\\"310107\\\\\\\",\\\\\\\"eleAddress\\\\\\\":false,\\\\\\\"extraInfo\\\\\\\":\\\\\\\"{\\\\\\\\\\\\\\\"checkInf\\\\\\\\\\\\\\\":\\\\\\\\\\\\\\\"cainiao#Mon Oct 28 22:38:33 CST 2019\\\\\\\\\\\\\\\"}\\\\\\\",\\\\\\\"fullMobile\\\\\\\":\\\\\\\"86-17621951401\\\\\\\",\\\\\\\"fullName\\\\\\\":\\\\\\\"杜鹏飞\\\\\\\",\\\\\\\"gmtCreate\\\\\\\":1375542543000,\\\\\\\"gmtModified\\\\\\\":1556008689000,\\\\\\\"guoguoAddress\\\\\\\":false,\\\\\\\"helpBuyAddress\\\\\\\":false,\\\\\\\"id\\\\\\\":1247011080,\\\\\\\"illegalCunTaoAddress\\\\\\\":false,\\\\\\\"minDivisonCode\\\\\\\":\\\\\\\"310107103\\\\\\\",\\\\\\\"mobile\\\\\\\":\\\\\\\"17621951401\\\\\\\",\\\\\\\"mobileInternationalCode\\\\\\\":\\\\\\\"86\\\\\\\",\\\\\\\"needToUpgrade\\\\\\\":false,\\\\\\\"pOIAddress\\\\\\\":false,\\\\\\\"postCode\\\\\\\":\\\\\\\"200331\\\\\\\",\\\\\\\"province\\\\\\\":\\\\\\\"上海\\\\\\\",\\\\\\\"qinQingAddress\\\\\\\":false,\\\\\\\"status\\\\\\\":0,\\\\\\\"tag\\\\\\\":0,\\\\\\\"town\\\\\\\":\\\\\\\"桃浦镇\\\\\\\",\\\\\\\"townDivisionCode\\\\\\\":\\\\\\\"310107103\\\\\\\",\\\\\\\"userId\\\\\\\":1774425903,\\\\\\\"versionObject\\\\\\\":7,\\\\\\\"x\\\\\\\":\\\\\\\"31.2832337507\\\\\\\",\\\\\\\"y\\\\\\\":\\\\\\\"121.35150025\\\\\\\"},\\\\\\\"checked\\\\\\\":false,\\\\\\\"cityName\\\\\\\":\\\\\\\"上海市\\\\\\\",\\\\\\\"consolidationGuide\\\\\\\":false,\\\\\\\"countryName\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"defaultAddress\\\\\\\":false,\\\\\\\"deliveryAddressId\\\\\\\":1247011080,\\\\\\\"disable\\\\\\\":false,\\\\\\\"divisionCode\\\\\\\":\\\\\\\"310107\\\\\\\",\\\\\\\"enableMDZT\\\\\\\":false,\\\\\\\"enableStation\\\\\\\":false,\\\\\\\"enforceUpdate4Address\\\\\\\":true,\\\\\\\"fullName\\\\\\\":\\\\\\\"杜鹏飞\\\\\\\",\\\\\\\"hidden\\\\\\\":false,\\\\\\\"id\\\\\\\":\\\\\\\"1872428\\\\\\\",\\\\\\\"lat\\\\\\\":\\\\\\\"31.2832337507\\\\\\\",\\\\\\\"lgShopId\\\\\\\":0,\\\\\\\"lng\\\\\\\":\\\\\\\"121.35150025\\\\\\\",\\\\\\\"mainland\\\\\\\":true,\\\\\\\"mobile\\\\\\\":\\\\\\\"17621951401\\\\\\\",\\\\\\\"name\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"needUpdate4Address\\\\\\\":false,\\\\\\\"needUpgradeAddress\\\\\\\":false,\\\\\\\"platformType\\\\\\\":\\\\\\\"H5\\\\\\\",\\\\\\\"postCode\\\\\\\":\\\\\\\"200331\\\\\\\",\\\\\\\"provinceName\\\\\\\":\\\\\\\"上海\\\\\\\",\\\\\\\"stationId\\\\\\\":0,\\\\\\\"status\\\\\\\":\\\\\\\"normal\\\\\\\",\\\\\\\"storeAddress\\\\\\\":true,\\\\\\\"townDivisionId\\\\\\\":310107103,\\\\\\\"townName\\\\\\\":\\\\\\\"桃浦镇\\\\\\\",\\\\\\\"updateAddressTip\\\\\\\":\\\\\\\"\\\\\\\"}]\\\",\\\"sites\\\":\\\"[]\\\",\\\"lat\\\":\\\"31.2832337507\\\"}},\\\"type\\\":\\\"dinamicx$461$buyaddress\\\",\\\"fields\\\":{\\\"mobilephone\\\":\\\"17621951401\\\",\\\"name\\\":\\\"杜鹏飞\\\",\\\"iconUrl\\\":\\\"https://gw.alicdn.com/tfs/TB17gX2wYvpK1RjSZPiXXbmwXXa-128-128.png\\\",\\\"value\\\":\\\"上海上海市普陀区桃浦镇红棉路310弄8号401室\\\",\\\"desc\\\":\\\"收货不便时,可选择免费暂存服务\\\",\\\"cornerType\\\":\\\"both\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{\\\"fields\\\":{\\\"info\\\":{\\\"value\\\":\\\"1247011080\\\"}}},\\\"url\\\":\\\"//buy.m.tmall.com/order/addressList.htm?enableStation=true&requestStationUrl=%2F%2Fstationpicker-i56.m.taobao.com%2Finland%2FshowStationInPhone.htm&_input_charset=utf8&hidetoolbar=true&bridgeMessage=true\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"address\\\"},\\\"invoice_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"29bfffb\\\",\\\"submit\\\":true,\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"descCss\\\":{\\\"color\\\":\\\"#FFFFFF\\\"},\\\"title\\\":\\\"开具发票\\\",\\\"value\\\":\\\"电子发票-明细-个人-个人\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{\\\"__oldComponent\\\":\\\"{\\\\\\\"tag\\\\\\\":\\\\\\\"invoice\\\\\\\",\\\\\\\"id\\\\\\\":\\\\\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\\\\\",\\\\\\\"type\\\\\\\":\\\\\\\"biz\\\\\\\",\\\\\\\"fields\\\\\\\":{\\\\\\\"method\\\\\\\":\\\\\\\"post\\\\\\\",\\\\\\\"title\\\\\\\":\\\\\\\"发票\\\\\\\",\\\\\\\"url\\\\\\\":\\\\\\\"https://invoice-ua.taobao.com/e-invoice/invoice-apply-tm.html?source=order&sellerId=1714128138\\\\\\\",\\\\\\\"desc\\\\\\\":\\\\\\\"电子发票-明细-个人-个人\\\\\\\",\\\\\\\"info\\\\\\\":{\\\\\\\"payerBank\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"payerAddress\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"invoiceKinds\\\\\\\":\\\\\\\"0\\\\\\\",\\\\\\\"payerName\\\\\\\":\\\\\\\"个人\\\\\\\",\\\\\\\"payerRegisterNo\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"payerPhone\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"invoiceKind\\\\\\\":\\\\\\\"0\\\\\\\",\\\\\\\"businessType\\\\\\\":\\\\\\\"0\\\\\\\",\\\\\\\"payerBankAccount\\\\\\\":\\\\\\\"\\\\\\\"}}}\\\"},\\\"url\\\":\\\"https://invoice-ua.taobao.com/e-invoice/invoice-apply-tm.html?source=order&sellerId=1714128138\\\"}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"invoice\\\"},\\\"promotion_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"7cb7749\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"promotionType\\\":\\\"shop\\\",\\\"outId\\\":\\\"s_1714128138\\\",\\\"orderOutId\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"valueCss\\\":{},\\\"confirm\\\":\\\"完成\\\",\\\"components\\\":[{\\\"id\\\":\\\"Tmall$shopPromotionAll-5899957898_110307136347\\\",\\\"price\\\":\\\"\\\",\\\"title\\\":\\\"店铺满99包邮\\\"},{\\\"id\\\":\\\"0\\\",\\\"price\\\":\\\"\\\",\\\"title\\\":\\\"不使用优惠\\\"}],\\\"title\\\":\\\"店铺优惠\\\",\\\"asSelect\\\":{\\\"selectedIds\\\":[\\\"Tmall$shopPromotionAll-5899957898_110307136347\\\"]},\\\"desc\\\":\\\"店铺满99包邮\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimplePopup\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"promotion\\\"},\\\"deliveryMethod_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"003192e\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"deliveryId\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"confirm\\\":\\\"完成\\\",\\\"components\\\":[{\\\"ext\\\":\\\"{\\\\\\\"fareCent\\\\\\\":0,\\\\\\\"id\\\\\\\":\\\\\\\"2\\\\\\\",\\\\\\\"serviceType\\\\\\\":\\\\\\\"-4\\\\\\\"}\\\",\\\"id\\\":\\\"2\\\",\\\"price\\\":\\\"快递 免邮\\\",\\\"title\\\":\\\"普通配送\\\"}],\\\"price\\\":\\\"快递 免邮\\\",\\\"title\\\":\\\"配送方式\\\",\\\"asSelect\\\":{\\\"selectedIds\\\":[\\\"2\\\"]},\\\"value\\\":\\\"快递 免邮\\\",\\\"desc\\\":\\\"普通配送\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimplePopup\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"deliveryMethod\\\"},\\\"anonymous_1\\\":{\\\"ref\\\":\\\"c1973e0\\\",\\\"submit\\\":true,\\\"type\\\":\\\"dinamicx$561$buyprotocolcheckbox\\\",\\\"fields\\\":{\\\"title\\\":\\\"匿名购买\\\",\\\"isChecked\\\":true},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"select\\\",\\\"fields\\\":{\\\"isChecked\\\":\\\"true\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"anonymous\\\"},\\\"voucher_1\\\":{\\\"ref\\\":\\\"ae969fe\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"selectedId\\\":\\\"no_use_platformChangeCoupon\\\"}},\\\"type\\\":\\\"dinamicx$550$buyimageselect\\\",\\\"fields\\\":{\\\"price\\\":\\\"不使用\\\",\\\"extraLink\\\":\\\"true\\\",\\\"iconUrl\\\":\\\"//gw.alicdn.com/tfs/TB1caHmXL5G3KVjSZPxXXbI3XXa-120-36.png\\\",\\\"cornerType\\\":\\\"both\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openPopupWindow\\\",\\\"fields\\\":{\\\"css\\\":{\\\"height\\\":\\\"0.6\\\"},\\\"options\\\":{\\\"needCloseButton\\\":\\\"true\\\"},\\\"nextRenderRoot\\\":\\\"voucherOptions_1\\\",\\\"params\\\":{}}}],\\\"detailClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{},\\\"url\\\":\\\"//pages.tmall.com/wow/member-club/act/xiadanyeguiz?wh_biz=tm\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"voucher\\\"},\\\"confirmOrder_1\\\":{\\\"ref\\\":\\\"8318d7a\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"pageType\\\":\\\"GENERAL\\\",\\\"umid\\\":\\\"\\\",\\\"__ex_params__\\\":\\\"{\\\\\\\"ovspayrendercnaddresskey\\\\\\\":true,\\\\\\\"userAgent\\\\\\\":\\\\\\\"Mozilla/5.0 (Linux; Android 4.4.2; XT1570 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36\\\\\\\",\\\\\\\"ovspayrenderkey\\\\\\\":false,\\\\\\\"tradeProtocolFeatures\\\\\\\":\\\\\\\"5\\\\\\\"}\\\",\\\"joinId\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\"}},\\\"type\\\":\\\"block$null$emptyBlock\\\",\\\"fields\\\":{},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"confirmOrder\\\"},\\\"service_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"166250e\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"serviceType\\\":\\\"1\\\",\\\"outId\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"confirm\\\":\\\"完成\\\",\\\"componentGroups\\\":[{\\\"asSelect\\\":{\\\"optional\\\":\\\"false\\\",\\\"selectedIds\\\":[\\\"{'bizType':1,'optionId':'checkBoxOptionId','serviceId':'1065','storeId':0}\\\"]},\\\"components\\\":[{\\\"ext\\\":\\\"0.00\\\",\\\"id\\\":\\\"{'bizType':1,'optionId':'checkBoxOptionId','serviceId':'1065','storeId':0}\\\",\\\"title\\\":\\\"聚划算卖家赠送，若确认收货前退货，可获保险赔付\\\"}]}],\\\"extraLink\\\":\\\"true\\\",\\\"title\\\":\\\"运费险\\\",\\\"desc\\\":\\\"聚划算卖家赠送，若确认收货前退货，可获保险赔付 \\\"},\\\"events\\\":{\\\"detailClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"method\\\":\\\"GET\\\",\\\"params\\\":{\\\"target\\\":\\\"_self\\\"},\\\"url\\\":\\\"https://render.alipay.com/p/h5/insscene/www/insureProtocol.html?1=1&buyerId=1774425903&sellerId=1714128138&serviceId=1065\\\"}}],\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimpleGroupPopup\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"service\\\"},\\\"ncCheckCode_ncCheckCode1\\\":{\\\"ref\\\":\\\"fc57d42\\\",\\\"submit\\\":true,\\\"type\\\":\\\"native$null$ncCheckCode\\\",\\\"fields\\\":{\\\"nc\\\":\\\"1\\\",\\\"token\\\":\\\"b6fe6b7f4414926de0a1977a70c506d8683c9621\\\"},\\\"id\\\":\\\"ncCheckCode1\\\",\\\"tag\\\":\\\"ncCheckCode\\\"},\\\"submitOrder_1\\\":{\\\"ref\\\":\\\"40aa9e9\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"showPrice\\\":\\\"1299.00\\\",\\\"submitOrderType\\\":\\\"UNITY\\\"}},\\\"type\\\":\\\"dinamicx$475$buysubmit\\\",\\\"fields\\\":{\\\"isShowFamilyPayBtn\\\":\\\"false\\\",\\\"price\\\":\\\"￥1299.00\\\",\\\"priceTitle\\\":\\\"合计:\\\",\\\"count\\\":\\\"共1件，\\\",\\\"payBtn\\\":{\\\"enable\\\":true,\\\"title\\\":\\\"提交订单\\\"},\\\"descCss\\\":{},\\\"desc\\\":\\\"\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"submit\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"submitOrder\\\"},\\\"promotion_ab96af10ec01db7dfd2b9fbefe406c91\\\":{\\\"ref\\\":\\\"7cb7749\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"promotionType\\\":\\\"item\\\",\\\"outId\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"orderOutId\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"valueCss\\\":{},\\\"confirm\\\":\\\"完成\\\",\\\"components\\\":[{\\\"id\\\":\\\"Tmall$bigMarkdown-10392680933_109327432388\\\",\\\"price\\\":\\\"\\\",\\\"title\\\":\\\"年货价\\\"}],\\\"title\\\":\\\"商品优惠\\\",\\\"asSelect\\\":{\\\"selectedIds\\\":[\\\"Tmall$bigMarkdown-10392680933_109327432388\\\"]},\\\"desc\\\":\\\"年货价\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimplePopup\\\",\\\"fields\\\":{}}]},\\\"status\\\":\\\"hidden\\\",\\\"id\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"tag\\\":\\\"promotion\\\"},\\\"memo_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"b642b1e\\\",\\\"submit\\\":true,\\\"type\\\":\\\"dinamicx$554$buyinput\\\",\\\"fields\\\":{\\\"placeholder\\\":\\\"选填,请先和商家协商一致\\\",\\\"title\\\":\\\"订单备注\\\",\\\"value\\\":\\\"\\\"},\\\"events\\\":{\\\"onFinish\\\":[{\\\"type\\\":\\\"input\\\",\\\"fields\\\":{\\\"value\\\":\\\"\\\"}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"memo\\\"}}\",\"linkage\":\"{\\\"common\\\":{\\\"compress\\\":true,\\\"submitParams\\\":\\\"^^$$Z2df6357cdbb668d73d1aa79bbd13ac29b|null{$_$}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\\\",\\\"validateParams\\\":\\\"^^$$3830b7703307690f7108dc0cf329632c{$_$}H4sIAAAAAAAAAIWRzUrDQBSF32XWYUijTUh3SRp/QErxp+BKbmdu09DJTJiZorUU3ItL176G4OtUfA1vLGo34u7O4c45Z75Zs5mFBm+NXYyBJnfatIoN1qxV4GfGNperFruzUODciFbZgAnTcFD1FKbAvQWJXKgateeNkai4M0srkI/3HCYRC5je3T7p02ysrDVQUrgJWAsV/pXjwUzBcIpsje4y5Ip8asEb9LAndwsK73h+dR3x8bfhzpsqV6jRUl7AJDpBwsfby/b1Yfv6+P70TGoDdoGe9N+ex+WoPM/OSPgpm1JZZQSojsL9/KYYMVKWDm3mXF3p/0G5OViUvLXo6DHga6N524HnQ/AwIary6x92wBBlMUexKIgrG8xAOQwYamFXrb/wttYV9ciHWT+MkijtxVF5WIZxr8yjKD46KPMkS6KyyNM4jpNeHGZ5mOYZ22w+ASTVTzT2AQAA\\\"},\\\"signature\\\":\\\"6960a65f38e64305dfac5d8fa113bca0\\\"}\",\"hierarchy\":\"{\\\"structure\\\":{\\\"voucherOptionsHeader_1\\\":[\\\"voucherPopupTitle_1\\\"],\\\"voucherOptions_1\\\":[\\\"voucherOptionsHeader_1\\\",\\\"voucherOption_1|no_use_platformChangeCoupon:0\\\",\\\"voucherOption_1|null:1\\\",\\\"voucherPopupConfirm_1\\\"],\\\"serviceCOBlock_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\":[\\\"service_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\"],\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\":[\\\"itemInfo_ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"alicomItemBlock_ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"promotion_ab96af10ec01db7dfd2b9fbefe406c91\\\"],\\\"confirmPromotionAndService_1\\\":[\\\"voucher_1\\\"],\\\"confirmOrder_1\\\":[\\\"topReminds_1\\\",\\\"addressBlock_1\\\",\\\"sesameBlock_1\\\",\\\"cuntaoBlock_1\\\",\\\"order_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"confirmPromotionAndService_1\\\",\\\"anonymous_1\\\",\\\"activityTips_1872541\\\",\\\"submitBlock_1\\\",\\\"ncCheckCode_ncCheckCode1\\\"],\\\"order_2f426b0c3ea8b56f75ad8354ad85afd7\\\":[\\\"orderInfo_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"deliveryMethod_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"serviceCOBlock_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"promotion_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"invoice_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"memo_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"orderPay_2f426b0c3ea8b56f75ad8354ad85afd7\\\"],\\\"submitBlock_1\\\":[\\\"submitOrder_1\\\"],\\\"addressBlock_1\\\":[\\\"address_1\\\"]}}\",\"endpoint\":\"{\\\"mode\\\":\\\"\\\",\\\"features\\\":\\\"5\\\",\\\"osVersion\\\":\\\"H5\\\",\\\"protocolVersion\\\":\\\"3.0\\\",\\\"ultronage\\\":\\\"true\\\"}\"}"}
    '''
