#!/usr/local/bin/python3.6

import os
import time
import argparse
import json
import conf
import psutil
from browsermobproxy import Server
from functools import reduce
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError


def is_different_previous_search(driver, args):
    # 検索ワードおよびオプション解析
    search_words = args.words
    or_search_words = args.or_words
    on_sale = args.sale
    new_item = args.new
    category_toy = args.toy
    price_max = args.price_max
    price_min = args.price_min

    # 検索メイン
    try:
        keyword = "%20".join(search_words)
        if or_search_words == None:
            keyword_list = [keyword]
        else:
            keyword_list = ["%20".join(word) for word in or_search_words]
            keyword_list.append(keyword)

        print(" or ".join(keyword_list))
        print()

        # 検索結果格納用
        url_list = []
        delete_list = []
        append_list = []

        for keyword in keyword_list:

            file_path = f"/home/pi/projects/mercari_notice/src/res/search_{keyword}.res"
            print(f"【検索 : {keyword}】")
            print()

            # 前回の検索結果を取得
            pre_search_result = []
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as fi:
                    pre_search_result = json.load(fi)
                    print("前回結果")
                    [print(pre) for pre in pre_search_result]
                    print()

            # 検索ページへ遷移
            print("検索ページへ遷移中...")

            # 検索条件オプション
            #option_on_sale = "&statusIds=%5B%22on_sale%22%5D" if on_sale else ""
            #option_new_item = "&itemConditionIds=%5B1%2C2%5D" if new_item else ""
            #option_category_toy = "&parentCategoryId=1328&childCategoryId=83&grandChildCategoryIds=%5B749%5D" if category_toy else ""
            option_on_sale = "&status_on_sale=1" if on_sale else ""
            option_new_item = "&item_condition_id%5B1%5D=1&item_condition_id%5B2%5D=1" if new_item else ""
            option_category_toy = "&category_root=1328&category_child=83&category_grand_child%5B749%5D=1" if category_toy else ""
            option_price_max = f"&price_max={price_max}" if price_max != None else ""
            option_price_min = f"&price_min={price_min}" if price_min != None else ""

            url = f"https://www.mercari.com/jp/search/?sort_order=&keyword={keyword}{option_category_toy}{option_new_item}{option_price_min}{option_price_max}{option_on_sale}"
            print(url)
            driver.get(url)

            # 遷移完了するまで待機(全要素が表示されるまで)
            page_css = "#search-result .heading"
            text = keyword.replace("%20", ' ') + " の検索結果"
            print(text)
            # WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, page_css), text))
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located)
            print("検索ページへ遷移完了")
            print()
    
            # スクリーンショット
            # driver.save_screenshot("mercari_page.png")
    
            # 検索結果を取得
            #item_selector = "li > div > a > figure.style_card__1SiAF.style_responsiveLv1__26FNN.common_fontFamily__3-3Si.style_fluid__19gwX"
            #item_name = "figcaption > span"
            #item_price = "div.style_thumbnail__N_xAi > span[aria-label='Price']"
            item_img = "figure.items-box-photo > img"
            #item_selector = "section.items-box"
            #item_name = "div.items-box-body > h3.items-box-name"
            #item_price = "div.items-box-body > div.items-box-num > div.items-box-price"
            item_selector = ".items-box"
            # item_img = ".lazyloaded" # なんかたまにエラーでる
            item_name = ".items-box-name"
            item_price = ".items-box-price"
            elements = driver.find_elements_by_css_selector(item_selector)

            # 検索結果を格納
            search_result = []
            no_result_selector = "p.search-result-description"
            if len(driver.find_elements_by_css_selector(no_result_selector)) == 0:
                search_result = [
                    [elm.find_element_by_css_selector(item_name).text,
                    elm.find_element_by_css_selector(item_price).text,
                    elm.find_element_by_css_selector(item_img).get_attribute("data-src")]
                    for elm in elements[:100]]
                print("今回結果")
                [print(res) for res in search_result]
                print()

            # ファイルに出力
            with open(file_path, "w", encoding="utf-8") as fo:
                json.dump(search_result, fo, ensure_ascii=False, indent=4)

            # 前回と検索結果に差分があったか
            # 順番が違うだけで差分ありの判定になるためsetで一致を確認
            if pre_search_result != search_result:
                only_pre = [dic for dic in pre_search_result if dic not in search_result]
                only_cur = [dic for dic in search_result if dic not in pre_search_result]
                if len(only_pre) > 0 or len(only_cur) > 0:
                    print(f"削除 : {only_pre}")
                    print(f"追加 : {only_cur}")
                    print()
                    url_list.append(url)
                    delete_list.extend(only_pre)
                    append_list.extend(only_cur)
            print()

        # 重複排除
        print(f"削除 : {delete_list}")
        print(f"追加 : {append_list}")
        delete_list = distinct(delete_list)
        append_list = distinct(append_list)

        return len(url_list) > 0, url_list, delete_list, append_list
    except:
        import traceback
        traceback.print_exc()

        # スクリーンショット
        driver.save_screenshot("err.png")
    finally:
        # ブラウザ閉じ
        print("ブラウザ終了")
        driver.close()
        driver.quit()

def distinct(list):
    ret = []
    for i in list:
        if not i in ret:
            ret.append(i)
    return ret

if __name__ == "__main__":
    try:
        # proxyサーバー起動
        # proxy_path ="/home/pi/package/browsermob-proxy-2.1.4/bin/browsermob-proxy"
        # server = Server(proxy_path, options={"port": 8080})
        # server.start()
        # proxy = server.create_proxy()

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        # proxyサーバー指定
        # chrome_options.add_argument(f"--proxy-server={proxy.proxy}")

        # UA偽装
        # chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0 Mobile/14C92 Safari/602.1')

        driver = webdriver.Chrome(executable_path="/home/pi/projects/selenium/chromedriver", chrome_options=chrome_options)

        # 引数チェック
        parser = argparse.ArgumentParser()
        parser.add_argument("-s", "--sale", help="now on sale item", action="store_true")
        parser.add_argument("-n", "--new", help="only new item", action="store_true")
        parser.add_argument("-t", "--toy", help="only category toy", action="store_true")
        parser.add_argument("-px", "--price_max", help="price max")
        parser.add_argument("-pn", "--price_min", help="price min")
        parser.add_argument("--or_words", help="or search", nargs="+", action="append")
        parser.add_argument("words", help="search words", nargs="+")
        args = parser.parse_args()

        # 検索
        is_diff, url_list, pre_list, cur_list = is_different_previous_search(driver, args)
        if is_diff:
            text = "■削除\n" + reduce(lambda x, y: f"{x}\n{y}", [json.dumps(z, ensure_ascii=False) for z in pre_list], "") + "\n\n"
            text += "■追加\n" + reduce(lambda x, y: f"{x}\n{y}", [json.dumps(z, ensure_ascii=False) for z in cur_list], "") + "\n\n"
            text += "\n".join(url_list)
            msg = TextSendMessage(text=text)
            print(text)
            conf.line_bot_api.push_message(conf.hide_id, msg)
            conf.line_bot_api.push_message(conf.tomo_id, msg)
    except LineBotApiError as e:
        # error handle
        print(e.message)
    except Exception as ex:
        import traceback
        traceback.print_exc()
        msg = TextSendMessage(text=f"{args.words}\nエラーが発生しました")
        conf.line_bot_api.push_message(conf.hide_id, msg)
    finally:
        print("END")
