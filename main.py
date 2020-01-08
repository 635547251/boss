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

        order_build_data = {
            "data": {
                "deliveryMethod_b7f7570d9c2dbede6da184ed62f6e36e": {
                    "ref": "003192e",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "deliveryId": "b7f7570d9c2dbede6da184ed62f6e36e"
                        }
                    },
                    "type": "dinamicx$498$buyselect",
                    "fields": {
                        "confirm": "完成",
                        "components": [{
                            "ext": "{\"fareCent\":0,\"id\":\"2\",\"serviceType\":\"-4\"}",
                            "id": "2",
                            "price": "快递 免邮",
                            "title": "普通配送"
                        }],
                        "price": "快递 免邮",
                        "title": "配送方式",
                        "asSelect": {
                            "selectedIds": ["2"]
                        },
                        "value": "快递 免邮",
                        "desc": "普通配送"
                    },
                    "events": {
                        "itemClick": [{
                            "type": "openSimplePopup",
                            "fields": {}
                        }]
                    }
                },
                "serviceGroupRoot_shfw_ec763ed3de6e76ce77d6df945ef4f4f5": {
                    "ref": "4fa1c27",
                    "type": "block$null$emptyBlock",
                    "fields": {}
                },
                "address_1": {
                    "ref": "f83ecc7",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "useMDZT": "false",
                            "useStation": "false",
                            "lng": "121.35150025",
                            "selectedId": "1247011080",
                            "linkAddressId": "0",
                            "options": "[{\"addressDetail\":\"红棉路310弄8号401室\",\"addressIconUrl\":\"\",\"agencyReceiveDesc\":\"收货不便时,可选择免费暂存服务\",\"areaName\":\"普陀区\",\"attributes\":[],\"baseDeliverAddressDO\":{\"address\":\"310107^^^上海^^^上海市^^^普陀区^^^桃浦镇 红棉路310弄8号401室^^^ ^^^桃浦镇^^^310107103^^^31.2832337507^^^121.35150025\",\"addressDetail\":\"红棉路310弄8号401室\",\"addressDetailWithoutTown\":\"红棉路310弄8号401室\",\"algorithmFrom\":\"cainiao#Mon Oct 28 22:38:33 CST 2019\",\"area\":\"普陀区\",\"chinaAddress\":True,\"city\":\"上海市\",\"confidence\":96,\"country\":\"\",\"cuntaoAddress\":false,\"devisionCode\":\"310107\",\"eleAddress\":false,\"extraInfo\":\"{\\\"checkInf\\\":\\\"cainiao#Mon Oct 28 22:38:33 CST 2019\\\"}\",\"fullMobile\":\"86-17621951401\",\"fullName\":\"杜鹏飞\",\"gmtCreate\":1375542543000,\"gmtModified\":1556008689000,\"guoguoAddress\":false,\"helpBuyAddress\":false,\"id\":1247011080,\"illegalCunTaoAddress\":false,\"minDivisonCode\":\"310107103\",\"mobile\":\"17621951401\",\"mobileInternationalCode\":\"86\",\"needToUpgrade\":false,\"pOIAddress\":false,\"postCode\":\"200331\",\"province\":\"上海\",\"qinQingAddress\":false,\"status\":0,\"tag\":0,\"town\":\"桃浦镇\",\"townDivisionCode\":\"310107103\",\"userId\":1774425903,\"versionObject\":7,\"x\":\"31.2832337507\",\"y\":\"121.35150025\"},\"checked\":false,\"cityName\":\"上海市\",\"consolidationGuide\":false,\"countryName\":\"\",\"defaultAddress\":false,\"deliveryAddressId\":1247011080,\"disable\":false,\"divisionCode\":\"310107\",\"enableMDZT\":false,\"enableStation\":false,\"enforceUpdate4Address\":True,\"fullName\":\"杜鹏飞\",\"hidden\":false,\"id\":\"3072602\",\"lat\":\"31.2832337507\",\"lgShopId\":0,\"lng\":\"121.35150025\",\"mainland\":True,\"mobile\":\"17621951401\",\"name\":\"\",\"needUpdate4Address\":false,\"needUpgradeAddress\":false,\"platformType\":\"H5\",\"postCode\":\"200331\",\"provinceName\":\"上海\",\"stationId\":0,\"status\":\"normal\",\"storeAddress\":True,\"townDivisionId\":310107103,\"townName\":\"桃浦镇\",\"updateAddressTip\":\"\"}]",
                            "sites": "[]",
                            "lat": "31.2832337507"
                        }
                    },
                    "type": "dinamicx$461$buyaddress",
                    "fields": {
                        "mobilephone": "17621951401",
                        "name": "杜鹏飞",
                        "iconUrl": "https://gw.alicdn.com/tfs/TB17gX2wYvpK1RjSZPiXXbmwXXa-128-128.png",
                        "value": "上海上海市普陀区桃浦镇红棉路310弄8号401室",
                        "desc": "收货不便时,可选择免费暂存服务"
                    },
                    "events": {
                        "itemClick": [{
                            "type": "openUrl",
                            "fields": {
                                "pageType": "H5",
                                "params": {
                                    "fields": {
                                        "info": {
                                            "value": "1247011080"
                                        }
                                    }
                                },
                                "url": "//buy.m.tmall.com/order/addressList.htm?enableStation=True&requestStationUrl=%2F%2Fstationpicker-i56.m.taobao.com%2Finland%2FshowStationInPhone.htm&_input_charset=utf8&hidetoolbar=True&bridgeMessage=True"
                            }
                        }]
                    }
                },
                "orderInfo_b7f7570d9c2dbede6da184ed62f6e36e": {
                    "ref": "2c311f0",
                    "type": "dinamicx$473$buyimagetext",
                    "fields": {
                        "iconUrl": "//gw.alicdn.com/tfs/TB1CzD7SXXXXXXJaXXXXXXXXXXX-32-32.png",
                        "title": "瑞达中腾数码专营店"
                    }
                },
                "serviceCOBlock_shfw_ec763ed3de6e76ce77d6df945ef4f4f5": {
                    "ref": "26c61ea",
                    "type": "block$null$emptyBlock",
                    "fields": {}
                },
                "voucherPopupConfirm_1": {
                    "ref": "54d778d",
                    "position": "footer",
                    "type": "dinamicx$500$buydialogsinglebutton",
                    "fields": {
                        "title": "完成"
                    },
                    "events": {
                        "itemClick": [{
                            "type": "confirmPopupWindow",
                            "fields": {}
                        }]
                    }
                },
                "serviceCOBlock_yfx_b7f7570d9c2dbede6da184ed62f6e36e": {
                    "ref": "26c61ea",
                    "type": "block$null$emptyBlock",
                    "fields": {}
                },
                "sesameBlock_1": {
                    "ref": "f813053",
                    "type": "block$null$emptyBlock",
                    "fields": {},
                    "cardGroup": "True"
                },
                "orderPay_b7f7570d9c2dbede6da184ed62f6e36e": {
                    "ref": "c99100a",
                    "type": "dinamicx$560$buysubtotal",
                    "fields": {
                        "price": "￥135.00",
                        "title": "小计: ",
                        "desc": "共1件"
                    }
                },
                "alicomItemBlock_ec763ed3de6e76ce77d6df945ef4f4f5": {
                    "ref": "dab643e",
                    "type": "block$null$emptyBlock",
                    "fields": {}
                },
                "voucherOption_1|no_use_platformChangeCoupon:0": {
                    "ref": "e0a3392",
                    "type": "dinamicx$689$buydialogshoppromotions",
                    "fields": {
                        "titleCss": {
                            "color": "#ff5500"
                        },
                        "subTitle": "",
                        "disable": "false",
                        "subTitleCss": {
                            "textColor": "#999999"
                        },
                        "title": "不使用",
                        "isChecked": "True"
                    },
                    "events": {
                        "itemClick": [{
                            "type": "select",
                            "fields": {
                                "isChecked": "false"
                            }
                        }]
                    }
                },
                "cuntaoBlock_1": {
                    "ref": "6c30eea",
                    "type": "block$null$emptyBlock",
                    "fields": {},
                    "cardGroup": "True"
                },
                "anonymous_1": {
                    "ref": "c1973e0",
                    "submit": True,
                    "type": "dinamicx$561$buyprotocolcheckbox",
                    "fields": {
                        "title": "匿名购买",
                        "isChecked": True
                    },
                    "events": {
                        "itemClick": [{
                            "type": "select",
                            "fields": {
                                "isChecked": "True"
                            }
                        }]
                    }
                },
                "topReminds_1": {
                    "ref": "d15acbf",
                    "type": "block$null$emptyBlock",
                    "fields": {},
                    "cardGroup": "True"
                },
                "itemInfo_ec763ed3de6e76ce77d6df945ef4f4f5": {
                    "ref": "f36c1fb",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "bizCode": "ali.china.tmall.appliance"
                        }
                    },
                    "type": "dinamicx$546$buyitem",
                    "fields": {
                        "skuLevel": [],
                        "timeLimit": "",
                        "subtitles": "颜色分类:SP580 120G 固态硬盘;",
                        "price": "￥135.00",
                        "icon": "//gw.alicdn.com/imgextra/i4/2133729733/O1CN0178r0Ph2LllSYXjgot_!!2133729733.jpg",
                        "count": "x1",
                        "weight": "",
                        "disabled": "false",
                        "services": [{
                            "value": "七天无理由退换"
                        }],
                        "title": "威刚SP580 120G/240G/480G SSD固态硬盘台式机电脑笔记本硬盘SATA"
                    }
                },
                "voucher_1": {
                    "ref": "ae969fe",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "selectedId": "no_use_platformChangeCoupon"
                        }
                    },
                    "type": "dinamicx$550$buyimageselect",
                    "fields": {
                        "price": "不使用",
                        "extraLink": "True",
                        "iconUrl": "//gw.alicdn.com/tfs/TB1caHmXL5G3KVjSZPxXXbI3XXa-120-36.png"
                    },
                    "events": {
                        "itemClick": [{
                            "type": "openPopupWindow",
                            "fields": {
                                "css": {
                                    "height": "0.6"
                                },
                                "options": {
                                    "needCloseButton": "True"
                                },
                                "nextRenderRoot": "voucherOptions_1",
                                "params": {}
                            }
                        }],
                        "detailClick": [{
                            "type": "openUrl",
                            "fields": {
                                "pageType": "H5",
                                "params": {},
                                "url": "//pages.tmall.com/wow/member-club/act/xiadanyeguiz?wh_biz=tm"
                            }
                        }]
                    }
                },
                "promotion_ec763ed3de6e76ce77d6df945ef4f4f5": {
                    "ref": "7cb7749",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "promotionType": "item",
                            "outId": "ec763ed3de6e76ce77d6df945ef4f4f5",
                            "orderOutId": "ec763ed3de6e76ce77d6df945ef4f4f5"
                        }
                    },
                    "type": "dinamicx$498$buyselect",
                    "fields": {
                        "valueCss": {},
                        "confirm": "完成",
                        "components": [{
                            "id": "Tmall$commonItemPromotion-10032208888_97401800453",
                            "price": "￥14.00",
                            "title": "省14:抢购价"
                        }],
                        "title": "商品优惠",
                        "asSelect": {
                            "selectedIds": ["Tmall$commonItemPromotion-10032208888_97401800453"]
                        },
                        "value": "-￥14.00",
                        "desc": "已省14元:抢购价"
                    },
                    "events": {
                        "itemClick": [{
                            "type": "openSimplePopup",
                            "fields": {}
                        }]
                    },
                    "status": "hidden"
                },
                "memo_b7f7570d9c2dbede6da184ed62f6e36e": {
                    "ref": "b642b1e",
                    "submit": True,
                    "type": "dinamicx$554$buyinput",
                    "fields": {
                        "placeholder": "选填,请先和商家协商一致",
                        "title": "订单备注",
                        "value": ""
                    },
                    "events": {
                        "onFinish": [{
                            "type": "input",
                            "fields": {
                                "value": ""
                            }
                        }]
                    }
                },
                "service_yfx_b7f7570d9c2dbede6da184ed62f6e36e": {
                    "ref": "166250e",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "serviceType": "1",
                            "outId": "b7f7570d9c2dbede6da184ed62f6e36e"
                        }
                    },
                    "type": "dinamicx$498$buyselect",
                    "fields": {
                        "confirm": "完成",
                        "componentGroups": [{
                            "asSelect": {
                                "optional": "false",
                                "selectedIds": ["{'bizType':1,'optionId':'checkBoxOptionId','serviceId':'1065','storeId':0}"]
                            },
                            "components": [{
                                "ext": "0.00",
                                "id": "{'bizType':1,'optionId':'checkBoxOptionId','serviceId':'1065','storeId':0}",
                                "title": "卖家赠送，退换货可赔"
                            }]
                        }],
                        "extraLink": "True",
                        "title": "运费险",
                        "desc": "卖家赠送，退换货可赔 "
                    },
                    "events": {
                        "detailClick": [{
                            "type": "openUrl",
                            "fields": {
                                "pageType": "H5",
                                "method": "GET",
                                "params": {
                                    "target": "_self"
                                },
                                "url": "https://render.alipay.com/p/h5/insscene/www/insureProtocol.html?1=1&buyerId=1774425903&sellerId=2133729733&serviceId=1065"
                            }
                        }],
                        "itemClick": [{
                            "type": "openSimpleGroupPopup",
                            "fields": {}
                        }]
                    }
                },
                "confirmOrder_1": {
                    "ref": "8318d7a",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "pageType": "GENERAL",
                            "umid": "",
                            "__ex_params__": "{\"ovspayrendercnaddresskey\":True,\"userAgent\":\"Mozilla/5.0 (Linux; Android 4.4.2; XT1570 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36\",\"ovspayrenderkey\":false,\"tradeProtocolFeatures\":\"5\"}",
                            "joinId": "ec763ed3de6e76ce77d6df945ef4f4f5"
                        }
                    },
                    "type": "block$null$emptyBlock",
                    "fields": {}
                },
                "item_ec763ed3de6e76ce77d6df945ef4f4f5": {
                    "ref": "360f46f",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "valid": "True",
                            "itemId": "540346037673",
                            "bizCode": "ali.china.tmall.appliance",
                            "cartId": "1734085872589",
                            "shoppingOrderId": "0",
                            "villagerId": "0",
                            "skuId": "4197478600222"
                        }
                    },
                    "type": "block$null$emptyBlock",
                    "fields": {}
                },
                "submitBlock_1": {
                    "ref": "0bb8011",
                    "position": "footer",
                    "type": "block$null$emptyBlock",
                    "fields": {}
                },
                "addressBlock_1": {
                    "ref": "2e04132",
                    "type": "block$null$emptyBlock",
                    "fields": {},
                    "cardGroup": "True"
                },
                "invoice_b7f7570d9c2dbede6da184ed62f6e36e": {
                    "ref": "29bfffb",
                    "submit": True,
                    "type": "dinamicx$498$buyselect",
                    "fields": {
                        "descCss": {
                            "color": "#FFFFFF"
                        },
                        "title": "开具发票",
                        "value": "本次不开具发票"
                    },
                    "events": {
                        "itemClick": [{
                            "type": "openUrl",
                            "fields": {
                                "pageType": "H5",
                                "params": {
                                    "__oldComponent": "{\"tag\":\"invoice\",\"id\":\"b7f7570d9c2dbede6da184ed62f6e36e\",\"type\":\"biz\",\"fields\":{\"method\":\"post\",\"title\":\"发票\",\"url\":\"https://invoice-ua.taobao.com/e-invoice/invoice-apply-tm.html?source=order&sellerId=2133729733\",\"desc\":\"本次不开具发票\",\"info\":{}}}"
                                },
                                "url": "https://invoice-ua.taobao.com/e-invoice/invoice-apply-tm.html?source=order&sellerId=2133729733"
                            }
                        }]
                    }
                },
                "voucherOptionsHeader_1": {
                    "ref": "a89b40c",
                    "position": "header",
                    "type": "block$null$emptyBlock",
                    "fields": {}
                },
                "voucherOptions_1": {
                    "ref": "195dae0",
                    "type": "block$null$selectorBlock",
                    "fields": {
                        "groupType": "singleSelect"
                    }
                },
                "confirmPromotionAndService_1": {
                    "ref": "73cfc13",
                    "type": "block$null$emptyBlock",
                    "fields": {},
                    "cardGroup": "True"
                },
                "voucherPopupTitle_1": {
                    "ref": "d1cdfd3",
                    "type": "dinamicx$499$buydialogtitle",
                    "fields": {
                        "title": "优惠详情"
                    }
                },
                "ncCheckCode_ncCheckCode1": {
                    "ref": "fc57d42",
                    "submit": True,
                    "type": "native$null$ncCheckCode",
                    "fields": {
                        "nc": "1",
                        "token": "c0bcac197f71343b42974a940243a7bef14bcbf1"
                    }
                },
                "submitOrder_1": {
                    "ref": "40aa9e9",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "showPrice": "135.00",
                            "submitOrderType": "UNITY"
                        }
                    },
                    "type": "dinamicx$475$buysubmit",
                    "fields": {
                        "isShowFamilyPayBtn": "false",
                        "price": "￥135.00",
                        "priceTitle": "合计:",
                        "count": "共1件，",
                        "payBtn": {
                            "enable": True,
                            "title": "提交订单"
                        },
                        "descCss": {},
                        "desc": ""
                    },
                    "events": {
                        "itemClick": [{
                            "type": "submit",
                            "fields": {}
                        }]
                    }
                },
                "activityTips_3072623": {
                    "ref": "42effdc",
                    "type": "dinamicx$460$buylabel",
                    "fields": {
                        "textSize": "13",
                        "richText": [{
                            "text": "年货节期间（1月6日-1月10日）支付成功的订单，72小时内发货，天猫国际、定制、预售、预约配送、家具类等特殊情况除外。"
                        }],
                        "textColor": "#999999"
                    }
                },
                "service_shfw_ec763ed3de6e76ce77d6df945ef4f4f5": {
                    "ref": "166250e",
                    "submit": True,
                    "hidden": {
                        "extensionMap": {
                            "serviceType": "2",
                            "outId": "ec763ed3de6e76ce77d6df945ef4f4f5"
                        }
                    },
                    "type": "dinamicx$498$buyselect",
                    "fields": {
                        "confirm": "完成",
                        "componentGroups": [{
                            "asSelect": {
                                "optional": "True",
                                "selectedIds": []
                            },
                            "components": [{
                                "ext": "50.80",
                                "id": "{'bizType':3,'optionId':'4073473605018','serviceId':'tmallservice_591698996012'}",
                                "title": "延长保修 三年 50.80元"
                            }, {
                                "ext": "28.80",
                                "id": "{'bizType':3,'optionId':'4073473605016','serviceId':'tmallservice_591698996012'}",
                                "title": "延长保修 一年 28.80元"
                            }, {
                                "ext": "38.79",
                                "id": "{'bizType':3,'optionId':'4073473605017','serviceId':'tmallservice_591698996012'}",
                                "title": "延长保修 二年 38.79元"
                            }]
                        }],
                        "extraLink": "false",
                        "title": "售后服务",
                        "desc": "未选择 "
                    },
                    "events": {
                        "itemClick": [{
                            "type": "openSimpleGroupPopup",
                            "fields": {}
                        }]
                    }
                },
                "voucherOption_1|null:1": {
                    "ref": "e0a3392",
                    "type": "dinamicx$689$buydialogshoppromotions",
                    "fields": {
                        "titleCss": {
                            "color": "#ff5500"
                        },
                        "subTitle": "有效期至2020.01.10\n订单中的商品均不支持此优惠",
                        "disable": "True",
                        "subTitleCss": {
                            "textColor": "#999999"
                        },
                        "title": "30元年货节购物津贴",
                        "isChecked": "false"
                    },
                    "events": {
                        "itemClick": [{
                            "type": "select",
                            "fields": {
                                "isChecked": "false"
                            }
                        }]
                    },
                    "status": "disable"
                },
                "serviceGroupRoot_yfx_b7f7570d9c2dbede6da184ed62f6e36e": {
                    "ref": "4fa1c27",
                    "type": "block$null$emptyBlock",
                    "fields": {}
                },
                "order_b7f7570d9c2dbede6da184ed62f6e36e": {
                    "ref": "a9dc6bd",
                    "type": "block$null$emptyBlock",
                    "fields": {},
                    "cardGroup": "True"
                }
            },
            "endpoint": {
                "mode": "",
                "features": "5",
                "osVersion": "H5",
                "protocolVersion": "3.0",
                "ultronage": "True"
            },
            "global": {
                "secretKey": "submitref",
                "secretValue": "e14eb48deba9d04f81b653239a301e16"
            },
            "hierarchy": {
                "component": ["submitBlock", "deliveryMethod", "voucher", "serviceCOBlock", "memo", "itemInfo", "sesameBlock", "voucherPopupConfirm", "voucherPopupTitle", "voucherOptions", "submitOrder", "serviceGroupRoot", "addressBlock", "alicomItemBlock", "order", "item", "address", "cuntaoBlock", "orderPay", "confirmPromotionAndService", "confirmOrder", "activityTips", "voucherOption", "voucherOptionsHeader", "service", "ncCheckCode", "orderInfo", "topReminds", "anonymous", "invoice", "promotion"],
                "root": "confirmOrder_1",
                "structure": {
                    "voucherOptionsHeader_1": ["voucherPopupTitle_1"],
                    "voucherOptions_1": ["voucherOptionsHeader_1", "voucherOption_1|no_use_platformChangeCoupon:0", "voucherOption_1|null:1", "voucherPopupConfirm_1"],
                    "confirmPromotionAndService_1": ["voucher_1"],
                    "confirmOrder_1": ["topReminds_1", "addressBlock_1", "sesameBlock_1", "cuntaoBlock_1", "order_b7f7570d9c2dbede6da184ed62f6e36e", "confirmPromotionAndService_1", "anonymous_1", "activityTips_3072623", "submitBlock_1", "ncCheckCode_ncCheckCode1"],
                    "item_ec763ed3de6e76ce77d6df945ef4f4f5": ["itemInfo_ec763ed3de6e76ce77d6df945ef4f4f5", "serviceCOBlock_shfw_ec763ed3de6e76ce77d6df945ef4f4f5", "alicomItemBlock_ec763ed3de6e76ce77d6df945ef4f4f5", "promotion_ec763ed3de6e76ce77d6df945ef4f4f5"],
                    "serviceCOBlock_shfw_ec763ed3de6e76ce77d6df945ef4f4f5": ["service_shfw_ec763ed3de6e76ce77d6df945ef4f4f5"],
                    "serviceCOBlock_yfx_b7f7570d9c2dbede6da184ed62f6e36e": ["service_yfx_b7f7570d9c2dbede6da184ed62f6e36e"],
                    "order_b7f7570d9c2dbede6da184ed62f6e36e": ["orderInfo_b7f7570d9c2dbede6da184ed62f6e36e", "item_ec763ed3de6e76ce77d6df945ef4f4f5", "deliveryMethod_b7f7570d9c2dbede6da184ed62f6e36e", "serviceCOBlock_yfx_b7f7570d9c2dbede6da184ed62f6e36e", "invoice_b7f7570d9c2dbede6da184ed62f6e36e", "memo_b7f7570d9c2dbede6da184ed62f6e36e", "orderPay_b7f7570d9c2dbede6da184ed62f6e36e"],
                    "submitBlock_1": ["submitOrder_1"],
                    "addressBlock_1": ["address_1"]
                },
                "baseType": ["dinamicx$500$buydialogsinglebutton", "dinamicx$554$buyinput", "dinamicx$689$buydialogshoppromotions", "dinamicx$461$buyaddress", "dinamicx$561$buyprotocolcheckbox", "block$null$emptyBlock", "dinamicx$473$buyimagetext", "dinamicx$498$buyselect", "native$null$ncCheckCode", "dinamicx$550$buyimageselect", "dinamicx$560$buysubtotal", "dinamicx$499$buydialogtitle", "dinamicx$546$buyitem", "block$null$selectorBlock", "dinamicx$475$buysubmit", "dinamicx$460$buylabel"]
            },
            "linkage": {
                "input": ["deliveryMethod_b7f7570d9c2dbede6da184ed62f6e36e", "memo_b7f7570d9c2dbede6da184ed62f6e36e", "service_yfx_b7f7570d9c2dbede6da184ed62f6e36e", "service_shfw_ec763ed3de6e76ce77d6df945ef4f4f5"],
                "request": ["invoice_b7f7570d9c2dbede6da184ed62f6e36e", "deliveryMethod_b7f7570d9c2dbede6da184ed62f6e36e", "promotion_ec763ed3de6e76ce77d6df945ef4f4f5", "service_yfx_b7f7570d9c2dbede6da184ed62f6e36e", "address_1", "service_shfw_ec763ed3de6e76ce77d6df945ef4f4f5", "voucher_1"],
                "common": {
                    "queryParams": "^^$$Z28d756c5446b060d085e3b0f68b8a65df|null{$_$}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",
                    "compress": True,
                    "validateParams": "^^$$d61b53f02956b16fbdb03dcfa5ffc8ae{$_$}H4sIAAAAAAAAAIWRzUrDQBSF32XWYUhDf0x3ySRVQUrxp+BKbie3aehkJsxM0VoK7sWla19D8HUqvoY3FrUbcXfncOecM99s2NxCjbfGLidAkzutG8WGG9Yo8HNj68t1g+1ZKnBuTKtsyKSpOahqBjPg3kKBXKoKtee1KVBxZ1ZWIp8cOEwjFjC9v33So9nYotJASeE2YA2U+FeOBzMDwymyMbrNKNbkU0leo4cDuV1QeMfTq+uIT74N995UuUSNlvICVqCTJHy8vexeH3avj+9Pz6TWYJfoSf/teZyP8/PkjISfsjGVVUaCaincL27EmJGycmgT56pS/w/KLcBiwRuLjh4DvjKaNy14noGHKVEtvv5hDwyxEAuUS0Fc2XAOymHAUEu7bvyFt5UuqUeaJb0wGkRxpx/l3TxM+mGWx3E6OIrzrsizkRjFHdETopsOorCbsu32E/wTMd32AQAA",
                    "structures": "H4sIAAAAAAAAAI1UTVODMBD9L5w5tKUF7U252IPTjvbmOJk02UhGkmVIQBn1v5sAtR/qNMOFDW/f231h9yOinNdgzG2J7JVMo+XT/sQFz3HEUAtZq3XNoR4+W6weQEnNjYvjPXqfH0cGDFVwiFmjLcVDjD3VLhPZIpvwazbjO+CQcjq9mgNPZyKFJAXHPEpvalRoJeobzR+hbiWDQVij7hQ2YxnMylbabisrQ5JJNktnieMwzU5JexDXLC+AvebIgRy9H7f6t57zpcWGFb0LzhdpQRFgWZoAT1z5kKUMsoynXFzPFyDm7ll4Nz1wpQVeBnvr+vby9VCwKcRbSBotJUO1ckJD3sWy4qjam3qZ3zUbeGWu2x7ZtxtwwWEexhGHUrZQd/dgC+QkgPnMyE68h2RJ3aL/uwIEFCgMwfV+bGh3GetsPqs67Pqd6WMeCUv4LRRkz5FOEN7LnAyfJ+gP1uMucYhxpNaVn29zB/Rny4xfNlg11Vba0s/8r4RhIf1DcsZOpp8aSWOAVCW1AmuVF1S/QI5NhXo5ccvihMjjm7Jc+h13XEw+LERfztc37yONCD4FAAA=",
                    "submitParams": "^^$$Z2d231473989c91b4a77196d2adf966e00|null{$_$}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"
                },
                "signature": "b2de621bec4a8c3c78abc5cdc466be36"
            },
            "reload": True
        }
        # 抢单
        submitref = order_build_data["global"]["secretValue"]

        delivery_method_key = list(filter(
            lambda x: "deliveryMethod" in x, order_build_data["linkage"]["input"]))[0]
        delivery_method = order_build_data["data"][delivery_method_key]
        delivery_method.update(
            {"id": delivery_method_key.split("_")[1], "tag": "deliveryMethod"})
        delivery_method_dict = json.dumps(delivery_method, ensure_ascii=False, separators=(
            ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"')

        address_key = list(
            filter(lambda x: "address_" in x, order_build_data["data"]))
        for k in address_key:
            address = order_build_data["data"][k]
            address.update({"id": k.split("_")[1], "tag": "address"})
            print(json.dumps(address, ensure_ascii=False, separators=(
                ',', ':')).replace('"', r'\\\"').replace(r'\\\\"', r'\\\\\\\"'))

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
    {"params":"{\"data\":\"{\\\"itemInfo_ab96af10ec01db7dfd2b9fbefe406c91\\\":{\\\"ref\\\":\\\"f36c1fb\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"bizCode\\\":\\\"ali.china.tmall.appliance\\\"}},\\\"type\\\":\\\"dinamicx$546$buyitem\\\",\\\"fields\\\":{\\\"skuLevel\\\":[],\\\"timeLimit\\\":\\\"\\\",\\\"subtitles\\\":\\\"表壳尺寸:其他;表带尺寸:适合 150-200 毫米腕围;表系列:黑色;\\\",\\\"price\\\":\\\"￥1299.00\\\",\\\"icon\\\":\\\"//gw.alicdn.com/imgextra/i4/1714128138/O1CN01L0m7Pt29zFlBi3yBH_!!1714128138.jpg\\\",\\\"count\\\":\\\"x1\\\",\\\"weight\\\":\\\"\\\",\\\"disabled\\\":\\\"false\\\",\\\"services\\\":[{\\\"value\\\":\\\"天猫无忧购\\\"},{\\\"value\\\":\\\"15天价保\\\"},{\\\"value\\\":\\\"七天无理由退换\\\"}],\\\"title\\\":\\\"【年货价】【天猫V榜推荐】小米手表运动跑步NFC男女款学生多功能小型智能手机手环支付宝付款wifi手表小爱同学支持eSIM\\\",\\\"icons\\\":[{\\\"value\\\":\\\"//gw.alicdn.com/tfs/TB15VswpYr1gK0jSZFDXXb9yVXa-84-36.png\\\"}]},\\\"id\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"tag\\\":\\\"itemInfo\\\"},\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\":{\\\"ref\\\":\\\"360f46f\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"valid\\\":\\\"true\\\",\\\"itemId\\\":\\\"602735592016\\\",\\\"bizCode\\\":\\\"ali.china.tmall.appliance\\\",\\\"cartId\\\":\\\"1750807824679\\\",\\\"shoppingOrderId\\\":\\\"0\\\",\\\"villagerId\\\":\\\"0\\\",\\\"skuId\\\":\\\"4414125690490\\\"}},\\\"type\\\":\\\"block$null$emptyBlock\\\",\\\"fields\\\":{},\\\"id\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"tag\\\":\\\"item\\\"},\\\"address_1\\\":{\\\"ref\\\":\\\"f83ecc7\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"useMDZT\\\":\\\"false\\\",\\\"useStation\\\":\\\"false\\\",\\\"lng\\\":\\\"121.35150025\\\",\\\"selectedId\\\":\\\"1247011080\\\",\\\"linkAddressId\\\":\\\"0\\\",\\\"options\\\":\\\"[{\\\\\\\"addressDetail\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"addressIconUrl\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"agencyReceiveDesc\\\\\\\":\\\\\\\"收货不便时,可选择免费暂存服务\\\\\\\",\\\\\\\"areaName\\\\\\\":\\\\\\\"普陀区\\\\\\\",\\\\\\\"attributes\\\\\\\":[],\\\\\\\"baseDeliverAddressDO\\\\\\\":{\\\\\\\"address\\\\\\\":\\\\\\\"310107^^^上海^^^上海市^^^普陀区^^^桃浦镇 红棉路310弄8号401室^^^ ^^^桃浦镇^^^310107103^^^31.2832337507^^^121.35150025\\\\\\\",\\\\\\\"addressDetail\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"addressDetailWithoutTown\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"algorithmFrom\\\\\\\":\\\\\\\"cainiao#Mon Oct 28 22:38:33 CST 2019\\\\\\\",\\\\\\\"area\\\\\\\":\\\\\\\"普陀区\\\\\\\",\\\\\\\"chinaAddress\\\\\\\":true,\\\\\\\"city\\\\\\\":\\\\\\\"上海市\\\\\\\",\\\\\\\"confidence\\\\\\\":96,\\\\\\\"country\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"cuntaoAddress\\\\\\\":false,\\\\\\\"devisionCode\\\\\\\":\\\\\\\"310107\\\\\\\",\\\\\\\"eleAddress\\\\\\\":false,\\\\\\\"extraInfo\\\\\\\":\\\\\\\"{\\\\\\\\\\\\\\\"checkInf\\\\\\\\\\\\\\\":\\\\\\\\\\\\\\\"cainiao#Mon Oct 28 22:38:33 CST 2019\\\\\\\\\\\\\\\"}\\\\\\\",\\\\\\\"fullMobile\\\\\\\":\\\\\\\"86-17621951401\\\\\\\",\\\\\\\"fullName\\\\\\\":\\\\\\\"杜鹏飞\\\\\\\",\\\\\\\"gmtCreate\\\\\\\":1375542543000,\\\\\\\"gmtModified\\\\\\\":1556008689000,\\\\\\\"guoguoAddress\\\\\\\":false,\\\\\\\"helpBuyAddress\\\\\\\":false,\\\\\\\"id\\\\\\\":1247011080,\\\\\\\"illegalCunTaoAddress\\\\\\\":false,\\\\\\\"minDivisonCode\\\\\\\":\\\\\\\"310107103\\\\\\\",\\\\\\\"mobile\\\\\\\":\\\\\\\"17621951401\\\\\\\",\\\\\\\"mobileInternationalCode\\\\\\\":\\\\\\\"86\\\\\\\",\\\\\\\"needToUpgrade\\\\\\\":false,\\\\\\\"pOIAddress\\\\\\\":false,\\\\\\\"postCode\\\\\\\":\\\\\\\"200331\\\\\\\",\\\\\\\"province\\\\\\\":\\\\\\\"上海\\\\\\\",\\\\\\\"qinQingAddress\\\\\\\":false,\\\\\\\"status\\\\\\\":0,\\\\\\\"tag\\\\\\\":0,\\\\\\\"town\\\\\\\":\\\\\\\"桃浦镇\\\\\\\",\\\\\\\"townDivisionCode\\\\\\\":\\\\\\\"310107103\\\\\\\",\\\\\\\"userId\\\\\\\":1774425903,\\\\\\\"versionObject\\\\\\\":7,\\\\\\\"x\\\\\\\":\\\\\\\"31.2832337507\\\\\\\",\\\\\\\"y\\\\\\\":\\\\\\\"121.35150025\\\\\\\"},\\\\\\\"checked\\\\\\\":false,\\\\\\\"cityName\\\\\\\":\\\\\\\"上海市\\\\\\\",\\\\\\\"consolidationGuide\\\\\\\":false,\\\\\\\"countryName\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"defaultAddress\\\\\\\":false,\\\\\\\"deliveryAddressId\\\\\\\":1247011080,\\\\\\\"disable\\\\\\\":false,\\\\\\\"divisionCode\\\\\\\":\\\\\\\"310107\\\\\\\",\\\\\\\"enableMDZT\\\\\\\":false,\\\\\\\"enableStation\\\\\\\":false,\\\\\\\"enforceUpdate4Address\\\\\\\":true,\\\\\\\"fullName\\\\\\\":\\\\\\\"杜鹏飞\\\\\\\",\\\\\\\"hidden\\\\\\\":false,\\\\\\\"id\\\\\\\":\\\\\\\"1872428\\\\\\\",\\\\\\\"lat\\\\\\\":\\\\\\\"31.2832337507\\\\\\\",\\\\\\\"lgShopId\\\\\\\":0,\\\\\\\"lng\\\\\\\":\\\\\\\"121.35150025\\\\\\\",\\\\\\\"mainland\\\\\\\":true,\\\\\\\"mobile\\\\\\\":\\\\\\\"17621951401\\\\\\\",\\\\\\\"name\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"needUpdate4Address\\\\\\\":false,\\\\\\\"needUpgradeAddress\\\\\\\":false,\\\\\\\"platformType\\\\\\\":\\\\\\\"H5\\\\\\\",\\\\\\\"postCode\\\\\\\":\\\\\\\"200331\\\\\\\",\\\\\\\"provinceName\\\\\\\":\\\\\\\"上海\\\\\\\",\\\\\\\"stationId\\\\\\\":0,\\\\\\\"status\\\\\\\":\\\\\\\"normal\\\\\\\",\\\\\\\"storeAddress\\\\\\\":true,\\\\\\\"townDivisionId\\\\\\\":310107103,\\\\\\\"townName\\\\\\\":\\\\\\\"桃浦镇\\\\\\\",\\\\\\\"updateAddressTip\\\\\\\":\\\\\\\"\\\\\\\"}]\\\",\\\"sites\\\":\\\"[]\\\",\\\"lat\\\":\\\"31.2832337507\\\"}},\\\"type\\\":\\\"dinamicx$461$buyaddress\\\",\\\"fields\\\":{\\\"mobilephone\\\":\\\"17621951401\\\",\\\"name\\\":\\\"杜鹏飞\\\",\\\"iconUrl\\\":\\\"https://gw.alicdn.com/tfs/TB17gX2wYvpK1RjSZPiXXbmwXXa-128-128.png\\\",\\\"value\\\":\\\"上海上海市普陀区桃浦镇红棉路310弄8号401室\\\",\\\"desc\\\":\\\"收货不便时,可选择免费暂存服务\\\",\\\"cornerType\\\":\\\"both\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{\\\"fields\\\":{\\\"info\\\":{\\\"value\\\":\\\"1247011080\\\"}}},\\\"url\\\":\\\"//buy.m.tmall.com/order/addressList.htm?enableStation=true&requestStationUrl=%2F%2Fstationpicker-i56.m.taobao.com%2Finland%2FshowStationInPhone.htm&_input_charset=utf8&hidetoolbar=true&bridgeMessage=true\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"address\\\"},\\\"invoice_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"29bfffb\\\",\\\"submit\\\":true,\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"descCss\\\":{\\\"color\\\":\\\"#FFFFFF\\\"},\\\"title\\\":\\\"开具发票\\\",\\\"value\\\":\\\"电子发票-明细-个人-个人\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{\\\"__oldComponent\\\":\\\"{\\\\\\\"tag\\\\\\\":\\\\\\\"invoice\\\\\\\",\\\\\\\"id\\\\\\\":\\\\\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\\\\\",\\\\\\\"type\\\\\\\":\\\\\\\"biz\\\\\\\",\\\\\\\"fields\\\\\\\":{\\\\\\\"method\\\\\\\":\\\\\\\"post\\\\\\\",\\\\\\\"title\\\\\\\":\\\\\\\"发票\\\\\\\",\\\\\\\"url\\\\\\\":\\\\\\\"https://invoice-ua.taobao.com/e-invoice/invoice-apply-tm.html?source=order&sellerId=1714128138\\\\\\\",\\\\\\\"desc\\\\\\\":\\\\\\\"电子发票-明细-个人-个人\\\\\\\",\\\\\\\"info\\\\\\\":{\\\\\\\"payerBank\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"payerAddress\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"invoiceKinds\\\\\\\":\\\\\\\"0\\\\\\\",\\\\\\\"payerName\\\\\\\":\\\\\\\"个人\\\\\\\",\\\\\\\"payerRegisterNo\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"payerPhone\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"invoiceKind\\\\\\\":\\\\\\\"0\\\\\\\",\\\\\\\"businessType\\\\\\\":\\\\\\\"0\\\\\\\",\\\\\\\"payerBankAccount\\\\\\\":\\\\\\\"\\\\\\\"}}}\\\"},\\\"url\\\":\\\"https://invoice-ua.taobao.com/e-invoice/invoice-apply-tm.html?source=order&sellerId=1714128138\\\"}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"invoice\\\"},\\\"promotion_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"7cb7749\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"promotionType\\\":\\\"shop\\\",\\\"outId\\\":\\\"s_1714128138\\\",\\\"orderOutId\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"valueCss\\\":{},\\\"confirm\\\":\\\"完成\\\",\\\"components\\\":[{\\\"id\\\":\\\"Tmall$shopPromotionAll-5899957898_110307136347\\\",\\\"price\\\":\\\"\\\",\\\"title\\\":\\\"店铺满99包邮\\\"},{\\\"id\\\":\\\"0\\\",\\\"price\\\":\\\"\\\",\\\"title\\\":\\\"不使用优惠\\\"}],\\\"title\\\":\\\"店铺优惠\\\",\\\"asSelect\\\":{\\\"selectedIds\\\":[\\\"Tmall$shopPromotionAll-5899957898_110307136347\\\"]},\\\"desc\\\":\\\"店铺满99包邮\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimplePopup\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"promotion\\\"},\\\"deliveryMethod_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"003192e\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"deliveryId\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"confirm\\\":\\\"完成\\\",\\\"components\\\":[{\\\"ext\\\":\\\"{\\\\\\\"fareCent\\\\\\\":0,\\\\\\\"id\\\\\\\":\\\\\\\"2\\\\\\\",\\\\\\\"serviceType\\\\\\\":\\\\\\\"-4\\\\\\\"}\\\",\\\"id\\\":\\\"2\\\",\\\"price\\\":\\\"快递 免邮\\\",\\\"title\\\":\\\"普通配送\\\"}],\\\"price\\\":\\\"快递 免邮\\\",\\\"title\\\":\\\"配送方式\\\",\\\"asSelect\\\":{\\\"selectedIds\\\":[\\\"2\\\"]},\\\"value\\\":\\\"快递 免邮\\\",\\\"desc\\\":\\\"普通配送\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimplePopup\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"deliveryMethod\\\"},\\\"anonymous_1\\\":{\\\"ref\\\":\\\"c1973e0\\\",\\\"submit\\\":true,\\\"type\\\":\\\"dinamicx$561$buyprotocolcheckbox\\\",\\\"fields\\\":{\\\"title\\\":\\\"匿名购买\\\",\\\"isChecked\\\":true},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"select\\\",\\\"fields\\\":{\\\"isChecked\\\":\\\"true\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"anonymous\\\"},\\\"voucher_1\\\":{\\\"ref\\\":\\\"ae969fe\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"selectedId\\\":\\\"no_use_platformChangeCoupon\\\"}},\\\"type\\\":\\\"dinamicx$550$buyimageselect\\\",\\\"fields\\\":{\\\"price\\\":\\\"不使用\\\",\\\"extraLink\\\":\\\"true\\\",\\\"iconUrl\\\":\\\"//gw.alicdn.com/tfs/TB1caHmXL5G3KVjSZPxXXbI3XXa-120-36.png\\\",\\\"cornerType\\\":\\\"both\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openPopupWindow\\\",\\\"fields\\\":{\\\"css\\\":{\\\"height\\\":\\\"0.6\\\"},\\\"options\\\":{\\\"needCloseButton\\\":\\\"true\\\"},\\\"nextRenderRoot\\\":\\\"voucherOptions_1\\\",\\\"params\\\":{}}}],\\\"detailClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{},\\\"url\\\":\\\"//pages.tmall.com/wow/member-club/act/xiadanyeguiz?wh_biz=tm\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"voucher\\\"},\\\"confirmOrder_1\\\":{\\\"ref\\\":\\\"8318d7a\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"pageType\\\":\\\"GENERAL\\\",\\\"umid\\\":\\\"\\\",\\\"__ex_params__\\\":\\\"{\\\\\\\"ovspayrendercnaddresskey\\\\\\\":true,\\\\\\\"userAgent\\\\\\\":\\\\\\\"Mozilla/5.0 (Linux; Android 4.4.2; XT1570 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36\\\\\\\",\\\\\\\"ovspayrenderkey\\\\\\\":false,\\\\\\\"tradeProtocolFeatures\\\\\\\":\\\\\\\"5\\\\\\\"}\\\",\\\"joinId\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\"}},\\\"type\\\":\\\"block$null$emptyBlock\\\",\\\"fields\\\":{},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"confirmOrder\\\"},\\\"service_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"166250e\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"serviceType\\\":\\\"1\\\",\\\"outId\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"confirm\\\":\\\"完成\\\",\\\"componentGroups\\\":[{\\\"asSelect\\\":{\\\"optional\\\":\\\"false\\\",\\\"selectedIds\\\":[\\\"{'bizType':1,'optionId':'checkBoxOptionId','serviceId':'1065','storeId':0}\\\"]},\\\"components\\\":[{\\\"ext\\\":\\\"0.00\\\",\\\"id\\\":\\\"{'bizType':1,'optionId':'checkBoxOptionId','serviceId':'1065','storeId':0}\\\",\\\"title\\\":\\\"聚划算卖家赠送，若确认收货前退货，可获保险赔付\\\"}]}],\\\"extraLink\\\":\\\"true\\\",\\\"title\\\":\\\"运费险\\\",\\\"desc\\\":\\\"聚划算卖家赠送，若确认收货前退货，可获保险赔付 \\\"},\\\"events\\\":{\\\"detailClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"method\\\":\\\"GET\\\",\\\"params\\\":{\\\"target\\\":\\\"_self\\\"},\\\"url\\\":\\\"https://render.alipay.com/p/h5/insscene/www/insureProtocol.html?1=1&buyerId=1774425903&sellerId=1714128138&serviceId=1065\\\"}}],\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimpleGroupPopup\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"service\\\"},\\\"ncCheckCode_ncCheckCode1\\\":{\\\"ref\\\":\\\"fc57d42\\\",\\\"submit\\\":true,\\\"type\\\":\\\"native$null$ncCheckCode\\\",\\\"fields\\\":{\\\"nc\\\":\\\"1\\\",\\\"token\\\":\\\"b6fe6b7f4414926de0a1977a70c506d8683c9621\\\"},\\\"id\\\":\\\"ncCheckCode1\\\",\\\"tag\\\":\\\"ncCheckCode\\\"},\\\"submitOrder_1\\\":{\\\"ref\\\":\\\"40aa9e9\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"showPrice\\\":\\\"1299.00\\\",\\\"submitOrderType\\\":\\\"UNITY\\\"}},\\\"type\\\":\\\"dinamicx$475$buysubmit\\\",\\\"fields\\\":{\\\"isShowFamilyPayBtn\\\":\\\"false\\\",\\\"price\\\":\\\"￥1299.00\\\",\\\"priceTitle\\\":\\\"合计:\\\",\\\"count\\\":\\\"共1件，\\\",\\\"payBtn\\\":{\\\"enable\\\":true,\\\"title\\\":\\\"提交订单\\\"},\\\"descCss\\\":{},\\\"desc\\\":\\\"\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"submit\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"submitOrder\\\"},\\\"promotion_ab96af10ec01db7dfd2b9fbefe406c91\\\":{\\\"ref\\\":\\\"7cb7749\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"promotionType\\\":\\\"item\\\",\\\"outId\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"orderOutId\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"valueCss\\\":{},\\\"confirm\\\":\\\"完成\\\",\\\"components\\\":[{\\\"id\\\":\\\"Tmall$bigMarkdown-10392680933_109327432388\\\",\\\"price\\\":\\\"\\\",\\\"title\\\":\\\"年货价\\\"}],\\\"title\\\":\\\"商品优惠\\\",\\\"asSelect\\\":{\\\"selectedIds\\\":[\\\"Tmall$bigMarkdown-10392680933_109327432388\\\"]},\\\"desc\\\":\\\"年货价\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimplePopup\\\",\\\"fields\\\":{}}]},\\\"status\\\":\\\"hidden\\\",\\\"id\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"tag\\\":\\\"promotion\\\"},\\\"memo_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"b642b1e\\\",\\\"submit\\\":true,\\\"type\\\":\\\"dinamicx$554$buyinput\\\",\\\"fields\\\":{\\\"placeholder\\\":\\\"选填,请先和商家协商一致\\\",\\\"title\\\":\\\"订单备注\\\",\\\"value\\\":\\\"\\\"},\\\"events\\\":{\\\"onFinish\\\":[{\\\"type\\\":\\\"input\\\",\\\"fields\\\":{\\\"value\\\":\\\"\\\"}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"memo\\\"}}\",\"linkage\":\"{\\\"common\\\":{\\\"compress\\\":true,\\\"submitParams\\\":\\\"^^$$Z2df6357cdbb668d73d1aa79bbd13ac29b|null{$_$}H4sIAAAAAAAAAM1X227cyBH9lQENLHYBLdW8D7UwAnkkrxVbl0gjbxZBQDTJpqYjks10NyWPDBv7vtm85S1AXgLkF4zkd2zkN3K6ybnIhr1GLkBgQOYUq6uqT1WdKr50Kkkbdivk9RnFkzpqutrZe+l0NdWVkM182THzu6ipUidQdfacQjQurXlOc+pqSUvmFjVnrXYbUbLaVaKXBXPPtiw8950dpx1OP4nwLGTJWwpP5NWO09Er9jE/moqcChcuO9EaH+USdnjhNkzTLbFRqNkL99Hl9757tjI42EbIV6xlEv52nJKpAoJ//uMvb9/88PbNj+9++hOkDZXXTEO+ifPbw5PD8/1nEKyDTRFsLQpaGxTuFtnsxIGkV0zuK8Wv2s8GCiduODAqJKOat1ensmTSlez3PVPanW1LzwfhEAaTB/NT5ez95qXD1X4r2mUjevyuaK0YImm5aK2tAc6vPRs8k894yzYnNWuOShPrGMYjfjfokx2Hjy9j4idBFKU+8eIdR1335kQYeqHnR3FKwhS6BZXaiL0kIlOSTP0wTtItj/ZdTKJ4CgvDjS8GQy9fATfR29MOzdOYVh5hBfHKPCmr0s/TKmcVC0lcpB6unvfLX/W01Vwv4Q5Rtjeb38RFLDm/m6H6kBdUplssUF2ubmhdu7Trak7bghk7ha1yaMEikzPRllwDs9fk9euyyy+7K1PO5pe5m80Dm/OGvfaiZBrggtOYEAJDnRSNMCeBqkGSq8eQ/HKhDlCWHHU9ZkTnM9HkwiCBIG1Aa4FjDG1Ep52xZ/U2oSBSYmoMF0bxC7kc/d1SyRZIvcmqrbrh7sdH2ZMDWB1b7d1Pf3z75s/v/vq3d3/4u/Fle9kjBnzbtxdDUmzFDIbwBkjuay153muG0kLrAwqOCzj38myigurhC81atQYCwqHVNMOJEQSuTk2qj9rTunwMTqFoNPvq1W83VeBXoR/npAgYneZRXCURLadBFOJvRKsyQfw2Z8dMKbQ3woEEdMNv2BoVWpYSr1c5GUCveXu9P7wY01DyG25CHgoGyRsURV1aBQMPeyauuNK8GE/+F0y2jJVqZVZZzNcISVYwXOSY6YUoh150WoNUbWD+eK4WVD3nUve0PkLfrs3RD/Jnsge8QBCmg/AMsx9Ni+nWumbSoOElpuWnXjA1ybIZGMRJGPpRSgJDDryz1zlsaQ60r9ZxrN9c0Jt78oXoOgjO6LJBWY/gIquthmhVHLBsJ4mpwZZpM6PwiMBLZshzhOnw+Gz+Pa62PbAwbvYcO2c2o8XZ8LlaKqD13vm8VyBJpUaxWqDDYFYYZja9baLQaKBxBj4+Pz3OZvvn8+zy4vAcihV0HvXLE3G7id/IbEMXoq24bCxKF9a7pbF79L+Sg5atxujolnawjsna1yvfpiFNAhuRczOKENjQoA/0A949eJAtogy8neIcyO85k6bYgchaxkfbjRbdOMHtPd2853XpLsyEph3/4GRPYeVY3PG6pruRSyZfYrD0L76Z7LelFLychG7o+t9Mfj0HX5LJI2Nt9+npPEyffDXZBw+z71j+lOvdKEjcIJ58+fTJ/PjZzqTm12zyLSuuxVeT0eluCPOzBQBkuwEY3vybHNsLTy5oRSUfjSBUru4BP0zk96uUqxN2u77RyEyq7zoh9TnDroL+u5Qb5h6HsUn9MWDaJFVhRA4F4WD+m1HAhURbrQb1SG1AECRdzuyMBI8auoJqMTI20vchezpsxabHyDrymmXZ7wRvM17iCTa82Pcxf/3pNAzSzHQ05KCHghmVGow16JEcXUtoYsZWGJEkjNMgNYcZhndgjzU6o+VNxkzPssG4kUvWouAzjaFnHa4MJIRYCuZ38IQ+HXjkU7O26JUWTWa2o0xpusyozsY+yGy1ZaY5zaV8zFQ7VdtitkAVGF7OWnb7uKbgEktc22+0uGamnPO4YnGeVGYrSf24ZIR6aZLQhBQRictpPA2KNPYNShLLhJRM4tRC607t7e42lLdu4272y10b1C7H/V+4C93UvwDboZ0f2lr5Aj/s7vBwezPKvOzeTpS1fV1nZPjPPt+bmVvybUWY/rd3ETjbdmfNfvLPF6prHlIfoPsudrkkTSPiKqZ1zQwXf51T6ZrFRDIsOIyjDB3PS1wv8FzPc9OpfWVq5LC94VK05hB0Lg6e+m6Il4pjajgBtsE4p5QWmOE09oK4IgVLU5RhmhJiCKZvrObtcy++i5gX+uW0DChLqE8pIZ5XsYBFZWUcGtX5mPV5RKKI0TgsCAn8fJqURexHU+bl4dSv4qIw+qg5O00Qyf8bXZntAt9S+gJbqbYD4ai0a9bPLkDvtT/umZZxFGJA+yEe4siP47CcJmHlF3kQEp+Y3N1jDPMZ9rPr9vuH7LLQdyXVzMa7+jxZEx6+Fs3a1Us2x+fLevqvd+Thy3KY3VzNRI9PuUuF1l+xsGbdibCDcn3mgKtC9K1+zKBn9nvTI4bT8fwfrQVnM2Dwv10L8A16cvod3GzvBFr2DKn/5EqAu33OSgAsYPzeSgBRi80DDj5zPJkyHMPDsmSD+xddNjizDBAAAA==\\\",\\\"validateParams\\\":\\\"^^$$3830b7703307690f7108dc0cf329632c{$_$}H4sIAAAAAAAAAIWRzUrDQBSF32XWYUijTUh3SRp/QErxp+BKbmdu09DJTJiZorUU3ItL176G4OtUfA1vLGo34u7O4c45Z75Zs5mFBm+NXYyBJnfatIoN1qxV4GfGNperFruzUODciFbZgAnTcFD1FKbAvQWJXKgateeNkai4M0srkI/3HCYRC5je3T7p02ysrDVQUrgJWAsV/pXjwUzBcIpsje4y5Ip8asEb9LAndwsK73h+dR3x8bfhzpsqV6jRUl7AJDpBwsfby/b1Yfv6+P70TGoDdoGe9N+ex+WoPM/OSPgpm1JZZQSojsL9/KYYMVKWDm3mXF3p/0G5OViUvLXo6DHga6N524HnQ/AwIary6x92wBBlMUexKIgrG8xAOQwYamFXrb/wttYV9ciHWT+MkijtxVF5WIZxr8yjKD46KPMkS6KyyNM4jpNeHGZ5mOYZ22w+ASTVTzT2AQAA\\\"},\\\"signature\\\":\\\"6960a65f38e64305dfac5d8fa113bca0\\\"}\",\"hierarchy\":\"{\\\"structure\\\":{\\\"voucherOptionsHeader_1\\\":[\\\"voucherPopupTitle_1\\\"],\\\"voucherOptions_1\\\":[\\\"voucherOptionsHeader_1\\\",\\\"voucherOption_1|no_use_platformChangeCoupon:0\\\",\\\"voucherOption_1|null:1\\\",\\\"voucherPopupConfirm_1\\\"],\\\"serviceCOBlock_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\":[\\\"service_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\"],\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\":[\\\"itemInfo_ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"alicomItemBlock_ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"promotion_ab96af10ec01db7dfd2b9fbefe406c91\\\"],\\\"confirmPromotionAndService_1\\\":[\\\"voucher_1\\\"],\\\"confirmOrder_1\\\":[\\\"topReminds_1\\\",\\\"addressBlock_1\\\",\\\"sesameBlock_1\\\",\\\"cuntaoBlock_1\\\",\\\"order_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"confirmPromotionAndService_1\\\",\\\"anonymous_1\\\",\\\"activityTips_1872541\\\",\\\"submitBlock_1\\\",\\\"ncCheckCode_ncCheckCode1\\\"],\\\"order_2f426b0c3ea8b56f75ad8354ad85afd7\\\":[\\\"orderInfo_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"deliveryMethod_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"serviceCOBlock_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"promotion_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"invoice_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"memo_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"orderPay_2f426b0c3ea8b56f75ad8354ad85afd7\\\"],\\\"submitBlock_1\\\":[\\\"submitOrder_1\\\"],\\\"addressBlock_1\\\":[\\\"address_1\\\"]}}\",\"endpoint\":\"{\\\"mode\\\":\\\"\\\",\\\"features\\\":\\\"5\\\",\\\"osVersion\\\":\\\"H5\\\",\\\"protocolVersion\\\":\\\"3.0\\\",\\\"ultronage\\\":\\\"true\\\"}\"}"}
    '''

    '''
    {"params":"{\"data\":\"{\\\"itemInfo_ab96af10ec01db7dfd2b9fbefe406c91\\\":{\\\"ref\\\":\\\"f36c1fb\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"bizCode\\\":\\\"ali.china.tmall.appliance\\\"}},\\\"type\\\":\\\"dinamicx$546$buyitem\\\",\\\"fields\\\":{\\\"skuLevel\\\":[],\\\"timeLimit\\\":\\\"\\\",\\\"subtitles\\\":\\\"表壳尺寸:其他;表带尺寸:适合 150-200 毫米腕围;表系列:黑色;\\\",\\\"price\\\":\\\"￥1299.00\\\",\\\"icon\\\":\\\"//gw.alicdn.com/imgextra/i4/1714128138/O1CN01L0m7Pt29zFlBi3yBH_!!1714128138.jpg\\\",\\\"count\\\":\\\"x1\\\",\\\"weight\\\":\\\"\\\",\\\"disabled\\\":\\\"false\\\",\\\"services\\\":[{\\\"value\\\":\\\"天猫无忧购\\\"},{\\\"value\\\":\\\"15天价保\\\"},{\\\"value\\\":\\\"七天无理由退换\\\"}],\\\"title\\\":\\\"【年货价】【天猫V榜推荐】小米手表运动跑步NFC男女款学生多功能小型智能手机手环支付宝付款wifi手表小爱同学支持eSIM\\\",\\\"icons\\\":[{\\\"value\\\":\\\"//gw.alicdn.com/tfs/TB15VswpYr1gK0jSZFDXXb9yVXa-84-36.png\\\"}]},\\\"id\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"tag\\\":\\\"itemInfo\\\"},\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\":{\\\"ref\\\":\\\"360f46f\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"valid\\\":\\\"true\\\",\\\"itemId\\\":\\\"602735592016\\\",\\\"bizCode\\\":\\\"ali.china.tmall.appliance\\\",\\\"cartId\\\":\\\"1750807824679\\\",\\\"shoppingOrderId\\\":\\\"0\\\",\\\"villagerId\\\":\\\"0\\\",\\\"skuId\\\":\\\"4414125690490\\\"}},\\\"type\\\":\\\"block$null$emptyBlock\\\",\\\"fields\\\":{},\\\"id\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"tag\\\":\\\"item\\\"},\\\"address_1\\\":{\\\"ref\\\":\\\"f83ecc7\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"useMDZT\\\":\\\"false\\\",\\\"useStation\\\":\\\"false\\\",\\\"lng\\\":\\\"121.35150025\\\",\\\"selectedId\\\":\\\"1247011080\\\",\\\"linkAddressId\\\":\\\"0\\\",\\\"options\\\":\\\"[{\\\\\\\"addressDetail\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"addressIconUrl\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"agencyReceiveDesc\\\\\\\":\\\\\\\"收货不便时,可选择免费暂存服务\\\\\\\",\\\\\\\"areaName\\\\\\\":\\\\\\\"普陀区\\\\\\\",\\\\\\\"attributes\\\\\\\":[],\\\\\\\"baseDeliverAddressDO\\\\\\\":{\\\\\\\"address\\\\\\\":\\\\\\\"310107^^^上海^^^上海市^^^普陀区^^^桃浦镇 红棉路310弄8号401室^^^ ^^^桃浦镇^^^310107103^^^31.2832337507^^^121.35150025\\\\\\\",\\\\\\\"addressDetail\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"addressDetailWithoutTown\\\\\\\":\\\\\\\"红棉路310弄8号401室\\\\\\\",\\\\\\\"algorithmFrom\\\\\\\":\\\\\\\"cainiao#Mon Oct 28 22:38:33 CST 2019\\\\\\\",\\\\\\\"area\\\\\\\":\\\\\\\"普陀区\\\\\\\",\\\\\\\"chinaAddress\\\\\\\":true,\\\\\\\"city\\\\\\\":\\\\\\\"上海市\\\\\\\",\\\\\\\"confidence\\\\\\\":96,\\\\\\\"country\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"cuntaoAddress\\\\\\\":false,\\\\\\\"devisionCode\\\\\\\":\\\\\\\"310107\\\\\\\",\\\\\\\"eleAddress\\\\\\\":false,\\\\\\\"extraInfo\\\\\\\":\\\\\\\"{\\\\\\\\\\\\\\\"checkInf\\\\\\\\\\\\\\\":\\\\\\\\\\\\\\\"cainiao#Mon Oct 28 22:38:33 CST 2019\\\\\\\\\\\\\\\"}\\\\\\\",\\\\\\\"fullMobile\\\\\\\":\\\\\\\"86-17621951401\\\\\\\",\\\\\\\"fullName\\\\\\\":\\\\\\\"杜鹏飞\\\\\\\",\\\\\\\"gmtCreate\\\\\\\":1375542543000,\\\\\\\"gmtModified\\\\\\\":1556008689000,\\\\\\\"guoguoAddress\\\\\\\":false,\\\\\\\"helpBuyAddress\\\\\\\":false,\\\\\\\"id\\\\\\\":1247011080,\\\\\\\"illegalCunTaoAddress\\\\\\\":false,\\\\\\\"minDivisonCode\\\\\\\":\\\\\\\"310107103\\\\\\\",\\\\\\\"mobile\\\\\\\":\\\\\\\"17621951401\\\\\\\",\\\\\\\"mobileInternationalCode\\\\\\\":\\\\\\\"86\\\\\\\",\\\\\\\"needToUpgrade\\\\\\\":false,\\\\\\\"pOIAddress\\\\\\\":false,\\\\\\\"postCode\\\\\\\":\\\\\\\"200331\\\\\\\",\\\\\\\"province\\\\\\\":\\\\\\\"上海\\\\\\\",\\\\\\\"qinQingAddress\\\\\\\":false,\\\\\\\"status\\\\\\\":0,\\\\\\\"tag\\\\\\\":0,\\\\\\\"town\\\\\\\":\\\\\\\"桃浦镇\\\\\\\",\\\\\\\"townDivisionCode\\\\\\\":\\\\\\\"310107103\\\\\\\",\\\\\\\"userId\\\\\\\":1774425903,\\\\\\\"versionObject\\\\\\\":7,\\\\\\\"x\\\\\\\":\\\\\\\"31.2832337507\\\\\\\",\\\\\\\"y\\\\\\\":\\\\\\\"121.35150025\\\\\\\"},\\\\\\\"checked\\\\\\\":false,\\\\\\\"cityName\\\\\\\":\\\\\\\"上海市\\\\\\\",\\\\\\\"consolidationGuide\\\\\\\":false,\\\\\\\"countryName\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"defaultAddress\\\\\\\":false,\\\\\\\"deliveryAddressId\\\\\\\":1247011080,\\\\\\\"disable\\\\\\\":false,\\\\\\\"divisionCode\\\\\\\":\\\\\\\"310107\\\\\\\",\\\\\\\"enableMDZT\\\\\\\":false,\\\\\\\"enableStation\\\\\\\":false,\\\\\\\"enforceUpdate4Address\\\\\\\":true,\\\\\\\"fullName\\\\\\\":\\\\\\\"杜鹏飞\\\\\\\",\\\\\\\"hidden\\\\\\\":false,\\\\\\\"id\\\\\\\":\\\\\\\"1872428\\\\\\\",\\\\\\\"lat\\\\\\\":\\\\\\\"31.2832337507\\\\\\\",\\\\\\\"lgShopId\\\\\\\":0,\\\\\\\"lng\\\\\\\":\\\\\\\"121.35150025\\\\\\\",\\\\\\\"mainland\\\\\\\":true,\\\\\\\"mobile\\\\\\\":\\\\\\\"17621951401\\\\\\\",\\\\\\\"name\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"needUpdate4Address\\\\\\\":false,\\\\\\\"needUpgradeAddress\\\\\\\":false,\\\\\\\"platformType\\\\\\\":\\\\\\\"H5\\\\\\\",\\\\\\\"postCode\\\\\\\":\\\\\\\"200331\\\\\\\",\\\\\\\"provinceName\\\\\\\":\\\\\\\"上海\\\\\\\",\\\\\\\"stationId\\\\\\\":0,\\\\\\\"status\\\\\\\":\\\\\\\"normal\\\\\\\",\\\\\\\"storeAddress\\\\\\\":true,\\\\\\\"townDivisionId\\\\\\\":310107103,\\\\\\\"townName\\\\\\\":\\\\\\\"桃浦镇\\\\\\\",\\\\\\\"updateAddressTip\\\\\\\":\\\\\\\"\\\\\\\"}]\\\",\\\"sites\\\":\\\"[]\\\",\\\"lat\\\":\\\"31.2832337507\\\"}},\\\"type\\\":\\\"dinamicx$461$buyaddress\\\",\\\"fields\\\":{\\\"mobilephone\\\":\\\"17621951401\\\",\\\"name\\\":\\\"杜鹏飞\\\",\\\"iconUrl\\\":\\\"https://gw.alicdn.com/tfs/TB17gX2wYvpK1RjSZPiXXbmwXXa-128-128.png\\\",\\\"value\\\":\\\"上海上海市普陀区桃浦镇红棉路310弄8号401室\\\",\\\"desc\\\":\\\"收货不便时,可选择免费暂存服务\\\",\\\"cornerType\\\":\\\"both\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{\\\"fields\\\":{\\\"info\\\":{\\\"value\\\":\\\"1247011080\\\"}}},\\\"url\\\":\\\"//buy.m.tmall.com/order/addressList.htm?enableStation=true&requestStationUrl=%2F%2Fstationpicker-i56.m.taobao.com%2Finland%2FshowStationInPhone.htm&_input_charset=utf8&hidetoolbar=true&bridgeMessage=true\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"address\\\"},\\\"invoice_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"29bfffb\\\",\\\"submit\\\":true,\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"descCss\\\":{\\\"color\\\":\\\"#FFFFFF\\\"},\\\"title\\\":\\\"开具发票\\\",\\\"value\\\":\\\"电子发票-明细-个人-个人\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{\\\"__oldComponent\\\":\\\"{\\\\\\\"tag\\\\\\\":\\\\\\\"invoice\\\\\\\",\\\\\\\"id\\\\\\\":\\\\\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\\\\\",\\\\\\\"type\\\\\\\":\\\\\\\"biz\\\\\\\",\\\\\\\"fields\\\\\\\":{\\\\\\\"method\\\\\\\":\\\\\\\"post\\\\\\\",\\\\\\\"title\\\\\\\":\\\\\\\"发票\\\\\\\",\\\\\\\"url\\\\\\\":\\\\\\\"https://invoice-ua.taobao.com/e-invoice/invoice-apply-tm.html?source=order&sellerId=1714128138\\\\\\\",\\\\\\\"desc\\\\\\\":\\\\\\\"电子发票-明细-个人-个人\\\\\\\",\\\\\\\"info\\\\\\\":{\\\\\\\"payerBank\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"payerAddress\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"invoiceKinds\\\\\\\":\\\\\\\"0\\\\\\\",\\\\\\\"payerName\\\\\\\":\\\\\\\"个人\\\\\\\",\\\\\\\"payerRegisterNo\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"payerPhone\\\\\\\":\\\\\\\"\\\\\\\",\\\\\\\"invoiceKind\\\\\\\":\\\\\\\"0\\\\\\\",\\\\\\\"businessType\\\\\\\":\\\\\\\"0\\\\\\\",\\\\\\\"payerBankAccount\\\\\\\":\\\\\\\"\\\\\\\"}}}\\\"},\\\"url\\\":\\\"https://invoice-ua.taobao.com/e-invoice/invoice-apply-tm.html?source=order&sellerId=1714128138\\\"}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"invoice\\\"},\\\"promotion_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"7cb7749\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"promotionType\\\":\\\"shop\\\",\\\"outId\\\":\\\"s_1714128138\\\",\\\"orderOutId\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"valueCss\\\":{},\\\"confirm\\\":\\\"完成\\\",\\\"components\\\":[{\\\"id\\\":\\\"Tmall$shopPromotionAll-5899957898_110307136347\\\",\\\"price\\\":\\\"\\\",\\\"title\\\":\\\"店铺满99包邮\\\"},{\\\"id\\\":\\\"0\\\",\\\"price\\\":\\\"\\\",\\\"title\\\":\\\"不使用优惠\\\"}],\\\"title\\\":\\\"店铺优惠\\\",\\\"asSelect\\\":{\\\"selectedIds\\\":[\\\"Tmall$shopPromotionAll-5899957898_110307136347\\\"]},\\\"desc\\\":\\\"店铺满99包邮\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimplePopup\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"promotion\\\"},\\\"deliveryMethod_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"003192e\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"deliveryId\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"confirm\\\":\\\"完成\\\",\\\"components\\\":[{\\\"ext\\\":\\\"{\\\\\\\"fareCent\\\\\\\":0,\\\\\\\"id\\\\\\\":\\\\\\\"2\\\\\\\",\\\\\\\"serviceType\\\\\\\":\\\\\\\"-4\\\\\\\"}\\\",\\\"id\\\":\\\"2\\\",\\\"price\\\":\\\"快递 免邮\\\",\\\"title\\\":\\\"普通配送\\\"}],\\\"price\\\":\\\"快递 免邮\\\",\\\"title\\\":\\\"配送方式\\\",\\\"asSelect\\\":{\\\"selectedIds\\\":[\\\"2\\\"]},\\\"value\\\":\\\"快递 免邮\\\",\\\"desc\\\":\\\"普通配送\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimplePopup\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"deliveryMethod\\\"},\\\"anonymous_1\\\":{\\\"ref\\\":\\\"c1973e0\\\",\\\"submit\\\":true,\\\"type\\\":\\\"dinamicx$561$buyprotocolcheckbox\\\",\\\"fields\\\":{\\\"title\\\":\\\"匿名购买\\\",\\\"isChecked\\\":true},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"select\\\",\\\"fields\\\":{\\\"isChecked\\\":\\\"true\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"anonymous\\\"},\\\"voucher_1\\\":{\\\"ref\\\":\\\"ae969fe\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"selectedId\\\":\\\"no_use_platformChangeCoupon\\\"}},\\\"type\\\":\\\"dinamicx$550$buyimageselect\\\",\\\"fields\\\":{\\\"price\\\":\\\"不使用\\\",\\\"extraLink\\\":\\\"true\\\",\\\"iconUrl\\\":\\\"//gw.alicdn.com/tfs/TB1caHmXL5G3KVjSZPxXXbI3XXa-120-36.png\\\",\\\"cornerType\\\":\\\"both\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openPopupWindow\\\",\\\"fields\\\":{\\\"css\\\":{\\\"height\\\":\\\"0.6\\\"},\\\"options\\\":{\\\"needCloseButton\\\":\\\"true\\\"},\\\"nextRenderRoot\\\":\\\"voucherOptions_1\\\",\\\"params\\\":{}}}],\\\"detailClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"params\\\":{},\\\"url\\\":\\\"//pages.tmall.com/wow/member-club/act/xiadanyeguiz?wh_biz=tm\\\"}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"voucher\\\"},\\\"confirmOrder_1\\\":{\\\"ref\\\":\\\"8318d7a\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"pageType\\\":\\\"GENERAL\\\",\\\"umid\\\":\\\"\\\",\\\"__ex_params__\\\":\\\"{\\\\\\\"ovspayrendercnaddresskey\\\\\\\":true,\\\\\\\"userAgent\\\\\\\":\\\\\\\"Mozilla/5.0 (Linux; Android 4.4.2; XT1570 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36\\\\\\\",\\\\\\\"ovspayrenderkey\\\\\\\":false,\\\\\\\"tradeProtocolFeatures\\\\\\\":\\\\\\\"5\\\\\\\"}\\\",\\\"joinId\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\"}},\\\"type\\\":\\\"block$null$emptyBlock\\\",\\\"fields\\\":{},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"confirmOrder\\\"},\\\"service_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"166250e\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"serviceType\\\":\\\"1\\\",\\\"outId\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"confirm\\\":\\\"完成\\\",\\\"componentGroups\\\":[{\\\"asSelect\\\":{\\\"optional\\\":\\\"false\\\",\\\"selectedIds\\\":[\\\"{'bizType':1,'optionId':'checkBoxOptionId','serviceId':'1065','storeId':0}\\\"]},\\\"components\\\":[{\\\"ext\\\":\\\"0.00\\\",\\\"id\\\":\\\"{'bizType':1,'optionId':'checkBoxOptionId','serviceId':'1065','storeId':0}\\\",\\\"title\\\":\\\"聚划算卖家赠送，若确认收货前退货，可获保险赔付\\\"}]}],\\\"extraLink\\\":\\\"true\\\",\\\"title\\\":\\\"运费险\\\",\\\"desc\\\":\\\"聚划算卖家赠送，若确认收货前退货，可获保险赔付 \\\"},\\\"events\\\":{\\\"detailClick\\\":[{\\\"type\\\":\\\"openUrl\\\",\\\"fields\\\":{\\\"pageType\\\":\\\"H5\\\",\\\"method\\\":\\\"GET\\\",\\\"params\\\":{\\\"target\\\":\\\"_self\\\"},\\\"url\\\":\\\"https://render.alipay.com/p/h5/insscene/www/insureProtocol.html?1=1&buyerId=1774425903&sellerId=1714128138&serviceId=1065\\\"}}],\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimpleGroupPopup\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"service\\\"},\\\"ncCheckCode_ncCheckCode1\\\":{\\\"ref\\\":\\\"fc57d42\\\",\\\"submit\\\":true,\\\"type\\\":\\\"native$null$ncCheckCode\\\",\\\"fields\\\":{\\\"nc\\\":\\\"1\\\",\\\"token\\\":\\\"b6fe6b7f4414926de0a1977a70c506d8683c9621\\\"},\\\"id\\\":\\\"ncCheckCode1\\\",\\\"tag\\\":\\\"ncCheckCode\\\"},\\\"submitOrder_1\\\":{\\\"ref\\\":\\\"40aa9e9\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"showPrice\\\":\\\"1299.00\\\",\\\"submitOrderType\\\":\\\"UNITY\\\"}},\\\"type\\\":\\\"dinamicx$475$buysubmit\\\",\\\"fields\\\":{\\\"isShowFamilyPayBtn\\\":\\\"false\\\",\\\"price\\\":\\\"￥1299.00\\\",\\\"priceTitle\\\":\\\"合计:\\\",\\\"count\\\":\\\"共1件，\\\",\\\"payBtn\\\":{\\\"enable\\\":true,\\\"title\\\":\\\"提交订单\\\"},\\\"descCss\\\":{},\\\"desc\\\":\\\"\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"submit\\\",\\\"fields\\\":{}}]},\\\"id\\\":\\\"1\\\",\\\"tag\\\":\\\"submitOrder\\\"},\\\"promotion_ab96af10ec01db7dfd2b9fbefe406c91\\\":{\\\"ref\\\":\\\"7cb7749\\\",\\\"submit\\\":true,\\\"hidden\\\":{\\\"extensionMap\\\":{\\\"promotionType\\\":\\\"item\\\",\\\"outId\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"orderOutId\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\"}},\\\"type\\\":\\\"dinamicx$498$buyselect\\\",\\\"fields\\\":{\\\"valueCss\\\":{},\\\"confirm\\\":\\\"完成\\\",\\\"components\\\":[{\\\"id\\\":\\\"Tmall$bigMarkdown-10392680933_109327432388\\\",\\\"price\\\":\\\"\\\",\\\"title\\\":\\\"年货价\\\"}],\\\"title\\\":\\\"商品优惠\\\",\\\"asSelect\\\":{\\\"selectedIds\\\":[\\\"Tmall$bigMarkdown-10392680933_109327432388\\\"]},\\\"desc\\\":\\\"年货价\\\"},\\\"events\\\":{\\\"itemClick\\\":[{\\\"type\\\":\\\"openSimplePopup\\\",\\\"fields\\\":{}}]},\\\"status\\\":\\\"hidden\\\",\\\"id\\\":\\\"ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"tag\\\":\\\"promotion\\\"},\\\"memo_2f426b0c3ea8b56f75ad8354ad85afd7\\\":{\\\"ref\\\":\\\"b642b1e\\\",\\\"submit\\\":true,\\\"type\\\":\\\"dinamicx$554$buyinput\\\",\\\"fields\\\":{\\\"placeholder\\\":\\\"选填,请先和商家协商一致\\\",\\\"title\\\":\\\"订单备注\\\",\\\"value\\\":\\\"\\\"},\\\"events\\\":{\\\"onFinish\\\":[{\\\"type\\\":\\\"input\\\",\\\"fields\\\":{\\\"value\\\":\\\"\\\"}}]},\\\"id\\\":\\\"2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"tag\\\":\\\"memo\\\"}}\",\"linkage\":\"{\\\"common\\\":{\\\"compress\\\":true,\\\"submitParams\\\":\\\"^^$$Z2df6357cdbb668d73d1aa79bbd13ac29b|null{$_$}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\\\",\\\"validateParams\\\":\\\"^^$$3830b7703307690f7108dc0cf329632c{$_$}H4sIAAAAAAAAAIWRzUrDQBSF32XWYUijTUh3SRp/QErxp+BKbmdu09DJTJiZorUU3ItL176G4OtUfA1vLGo34u7O4c45Z75Zs5mFBm+NXYyBJnfatIoN1qxV4GfGNperFruzUODciFbZgAnTcFD1FKbAvQWJXKgateeNkai4M0srkI/3HCYRC5je3T7p02ysrDVQUrgJWAsV/pXjwUzBcIpsje4y5Ip8asEb9LAndwsK73h+dR3x8bfhzpsqV6jRUl7AJDpBwsfby/b1Yfv6+P70TGoDdoGe9N+ex+WoPM/OSPgpm1JZZQSojsL9/KYYMVKWDm3mXF3p/0G5OViUvLXo6DHga6N524HnQ/AwIary6x92wBBlMUexKIgrG8xAOQwYamFXrb/wttYV9ciHWT+MkijtxVF5WIZxr8yjKD46KPMkS6KyyNM4jpNeHGZ5mOYZ22w+ASTVTzT2AQAA\\\"},\\\"signature\\\":\\\"6960a65f38e64305dfac5d8fa113bca0\\\"}\",\"hierarchy\":\"{\\\"structure\\\":{\\\"voucherOptionsHeader_1\\\":[\\\"voucherPopupTitle_1\\\"],\\\"voucherOptions_1\\\":[\\\"voucherOptionsHeader_1\\\",\\\"voucherOption_1|no_use_platformChangeCoupon:0\\\",\\\"voucherOption_1|null:1\\\",\\\"voucherPopupConfirm_1\\\"],\\\"serviceCOBlock_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\":[\\\"service_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\"],\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\":[\\\"itemInfo_ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"alicomItemBlock_ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"promotion_ab96af10ec01db7dfd2b9fbefe406c91\\\"],\\\"confirmPromotionAndService_1\\\":[\\\"voucher_1\\\"],\\\"confirmOrder_1\\\":[\\\"topReminds_1\\\",\\\"addressBlock_1\\\",\\\"sesameBlock_1\\\",\\\"cuntaoBlock_1\\\",\\\"order_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"confirmPromotionAndService_1\\\",\\\"anonymous_1\\\",\\\"activityTips_1872541\\\",\\\"submitBlock_1\\\",\\\"ncCheckCode_ncCheckCode1\\\"],\\\"order_2f426b0c3ea8b56f75ad8354ad85afd7\\\":[\\\"orderInfo_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"item_ab96af10ec01db7dfd2b9fbefe406c91\\\",\\\"deliveryMethod_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"serviceCOBlock_yfx_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"promotion_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"invoice_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"memo_2f426b0c3ea8b56f75ad8354ad85afd7\\\",\\\"orderPay_2f426b0c3ea8b56f75ad8354ad85afd7\\\"],\\\"submitBlock_1\\\":[\\\"submitOrder_1\\\"],\\\"addressBlock_1\\\":[\\\"address_1\\\"]}}\",\"endpoint\":\"{\\\"mode\\\":\\\"\\\",\\\"features\\\":\\\"5\\\",\\\"osVersion\\\":\\\"H5\\\",\\\"protocolVersion\\\":\\\"3.0\\\",\\\"ultronage\\\":\\\"true\\\"}\"}"}
    '''
