import json
import requests
import re
import os
from bs4 import BeautifulSoup
from linebot import LineBotApi
from linebot.models import TextSendMessage
from statistics import mean



"xa0はスクレイピング時に含まれる特殊文字"

# 設定情報読み込み
with open("settings.json", encoding="utf-8") as f:
    res = json.load(f)
# 定数 ---------------
# チャネルアクセストークン
CH_TOKEN = res["CH_TOKEN"]
# ユーザーID
USER_ID = res["USER_ID"]
# 天気予報URL（川湯）
URL = 'https://tenki.jp/amedas/1/3/19021.html'
URL2 = 'https://tenki.jp/leisure/1/3/6/4080/'

def get_page_info():
    """ 読み込みページ情報取得 """

    res = requests.get(URL)
    html = res.text.encode(res.encoding)
    soup = BeautifulSoup(html, 'lxml')
    
    return (soup)

def get_page_info_2():
    """ 読み込みページ情報取得 """

    res = requests.get(URL2)
    html = res.text.encode(res.encoding)
    soup2 = BeautifulSoup(html, 'lxml')
    
    return (soup2)


def get_wether_info(soup, soup2):
    """ 今日明日の天気予報dict情報の取得 """

    # 今日明日の天気リスト
    weather_list = []
    today_weather = {}
    
    #日付と時間が重なるとバグるので日付を削除するための臨時修正　要修正
    day_list = ["1日", 	"2日", 	"3日",	"4日",	"5日",	"6日",	"7日",	"8日",	"9日",	"10日",	"11日",	"12日",	"13日",	"14日",	"15日",
            "16日",	"17日",	"18日",	"19日",	"20日",	"21日",	"22日",	"23日",	"24日",	"25日",	"26日",	"27日",	"28日",	"29日",	"30日",	"31日"] 

    #1時間観測値の抜き出し
    contents = soup.find_all(class_= "section-wrap")
    idx = contents[3] #section-wrap[3]が1時間おきの気象情報の値になっているため

    contents3 = soup2.find_all(class_= "forecast-days-wrap")
    idx2 = contents3[0] #section-wrap[0]に天気情報があるため


    weather_info_list = [] #1時間おきの気象データすべてを取得後し、タグを外して入れるリスト　
    time_list = [] #予測に使用する時間の情報のインデックスを取得して入れておくリスト
    time_list2 = [] #予測に使用しない時間帯も含めた時間の情報のインデックスを取得して入れておくリスト
    temperature_list = [] #気温の情報を入れておくリスト
    temperature_list2 = [] #夜間の気温が-10℃を下回ったかの判断に使用するリスト
    wind_speed_list = [] #風速情報を入れておくリスト
    snow_list = [] #降雪量
    weather = [] #当日の天気
   
    all_dict = {}       #その日の時間ごとの気温を格納する辞書
    flug = 0 # 0なら通常の予測を行い、1なら夜間に-10℃を下回った際に見られる可能性を通知する、2なら通知は行わない
    
    DATA_FILE = "yesterday.txt"

    #表示の際にprintを使用していないのでlistに入れて時間を無理やり表示    
    num_list = [1, 2, 3, 4, 5, 6, 7, 21, 22, 23, 24]

    for i in idx.find_all("td"): #tdタグのものが必要な気象情報になっているため
        weather_info_list.append(i.text)
        
    for i in idx2.find_all("p"): #pタグのものが必要な気象情報(天気)になっているため
        weather.append(i.text)
    today_weather["weather"] = weather[2]
    
    #日付削除のための臨時修正　要修正箇所
    for i in day_list:
        for j in weather_info_list:
            if i == j:
                weather_info_list.remove(i)
                
    #条件に当てはめる時間の気温を取得
    for i in weather_info_list:
        if re.match('21:00', i):
            time_list.append(weather_info_list.index(i))
            time_list2.append(weather_info_list.index(i))
        elif re.match('22:00', i):
            time_list.append(weather_info_list.index(i))
            time_list2.append(weather_info_list.index(i))
        elif re.match('23:00', i):
            time_list.append(weather_info_list.index(i))
            time_list2.append(weather_info_list.index(i))
        elif re.match('24:00', i):
            time_list.append(weather_info_list.index(i))
            time_list2.append(weather_info_list.index(i))
        elif re.match('01:00', i):
            time_list.append(weather_info_list.index(i))
            time_list2.append(weather_info_list.index(i))
        elif re.match('02:00', i):
            time_list.append(weather_info_list.index(i)) 
            time_list2.append(weather_info_list.index(i))
        elif re.match('03:00', i):
            time_list.append(weather_info_list.index(i)) 
            time_list2.append(weather_info_list.index(i)) 

    #ここからは現時点(25/11/21)で予測には使用しない値                                          
        elif re.match('04:00', i):
            time_list2.append(weather_info_list.index(i))
        elif re.match('05:00', i):
            time_list2.append(weather_info_list.index(i))
        elif re.match('06:00', i):
            time_list2.append(weather_info_list.index(i))
        elif re.match('07:00', i):
            time_list2.append(weather_info_list.index(i))  

    for i in time_list:
        temperature_list.append(float(weather_info_list[i + 1]))
        
    for i in time_list2:
        temperature_list2.append(float(weather_info_list[i + 1]))
    
    today_weather["avg_tempreture"] = round(mean(temperature_list), 1)
    today_weather["min_tempreture"] = min(temperature_list2)
    
    #平均風速の取得
    for i in time_list:
        wind_speed_list.append(float(weather_info_list[i + 4]))
    today_weather["avg_wind_speed"] = round(mean(wind_speed_list), 1)
    
    #積雪量の取得
    contents2 = soup.find_all(class_= "amedas-history-list clearfix")
    idx2 = contents2[2]#降雪量の値が入っている
    for i in idx2.find_all("li"): #liタグのものが必要な気象情報(降雪量)になっているため
        snow_list.append(i.text)
    data = snow_list[0]
    snow = re.sub("\n|\xa0| |3時間|cm|", "", data)
    today_weather["snow"] = int(snow)
  

    #気温の表示
    for i in time_list2:
        all_dict[weather_info_list[i]] = weather_info_list[i + 1]
    
    num = 0
    for key, value in sorted(all_dict.items()):
        today_weather[str(num_list[num])] = f"{key}: {value}"
        num += 1

    #前日の観測データの取得
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                # ファイルの中身が空だったり数値以外の場合の対策
                if content.strip().isdigit():
                    yesterday_flug = int(content)
        except Exception as e:
            print(f"読み込みエラー: {e}")
            
    if yesterday_flug ==0:
        yesterday_data = "可能でした"
    elif yesterday_flug ==1:
        yesterday_data = "おそらく可能でした"
    elif yesterday_flug ==2:
        yesterday_data = "不可能でした"   
        
    today_weather["yesterday"] = yesterday_data
    
    
    #2026年岡村さんの状態遷移図反映版判定メゾット
    #前日観察可能
    if yesterday_flug ==0:
        #今日の観測の可否
        if (today_weather["avg_tempreture"] < -10) and (float(today_weather["snow"]) == 0):
            today_weather["analyze"] = "観測できます"
            flug = 0
        
        elif (-10 <=  today_weather["avg_tempreture"] < 1)  and (today_weather["snow"] == 0):
            today_weather["analyze"] = "観察できるかもしれません"
            flug = 1
        
        
        elif(today_weather["avg_tempreture"] >= 1) or (today_weather["snow"] > 0) or (today_weather["min_tempreture"] >= 0):
            today_weather["analyze"] = "観測できません"
            flug = 2
    
    #前日観察継続
    elif yesterday_flug == 1:
        #今日の観測の可否
        if (today_weather["avg_tempreture"] <= -10) and (today_weather["snow"] == 0):
            today_weather["analyze"] = "観測できます"
            flug = 0
        
        elif(today_weather["avg_tempreture"] >= -10) or (today_weather["snow"] > 0):
            today_weather["analyze"] = "観測できません"
            flug = 2
        
    #前日観察不可能
    elif yesterday_flug == 2:
        #今日の観測の可否
        if (today_weather["avg_wind_speed"] <= 1.4) and (today_weather["snow"] == 0):
            if (today_weather["avg_tempreture"] <= -13) or (today_weather["min_tempreture"] <= -16):
                today_weather["analyze"] = "観測できます"
                flug = 0
                    
        elif(today_weather["avg_tempreture"] >= 0) and (today_weather["snow"] > 0) and (min(temperature_list2) >= 0):
            today_weather["analyze"] = "観測できません"
            flug = 2

    today_weather["flug"] = flug
    
     # 今日のフラグをファイルに書き込む
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(str(flug))
    except Exception as e:
        print(f"書き込みエラー: {e}")
    
    
    # 今日明日の天気リストの格納
    weather_list.append(today_weather)
    
    return weather_list

def create_msg(weather_list):
    if  (weather_list[0]["flug"] == 0) or (weather_list[0]["flug"] == 2):
        
        """ LINE BOTメッセージ作成 """

        # BOTメッセージフォーマット
        msg_format = """
        天気              : {0}
        平均気温(C)       : {1}
        最低気温(C)       : {2}
        平均風速(m/s)     : {3}
        積雪量(cm)        : {4}
        ジュエリーバブルの観測  : {5}
        
        夜間の気温
        {6}
        {7}
        {8}
        {9}
        {10}
        {11}
        {12}
        {13}
        {14}
        {15}
        {16}
        予測には6時までの値を使用
        
        前日の観測: {17}
        """
        
        msg = ""
        for weather in weather_list:
            msg += msg_format.format(
                weather["weather"],
                weather["avg_tempreture"],
                weather["min_tempreture"],
                weather["avg_wind_speed"],
                weather["snow"],
                weather["analyze"],
                weather["21"],
                weather["22"],
                weather["23"],
                weather["24"],
                weather["1"],
                weather["2"],
                weather["3"],
                weather["4"],
                weather["5"],
                weather["6"],
                weather["7"],
                weather["yesterday"]
            )
        bot_msg = msg
    
    else:
        """ LINE BOTメッセージ作成 """

        # BOTメッセージフォーマット
        msg_format = """
        天気              : {0}
        平均気温(C)       : {1}
        最低気温(C)       : {2}
        平均風速(m/s)     : {3}
        積雪量(cm)        : {4}
        ジュエリーバブルの観測  : {5}
        
        夜間の気温
        {6}
        {7}
        {8}
        {9}
        {10}
        {11}
        {12}
        {13}
        {14}
        {15}
        {16}
        予測には6時までの値を使用
        
        前日の観測: {17}
        """
        
        msg = ""
        for weather in weather_list:
            msg += msg_format.format(
                weather["weather"],
                weather["avg_tempreture"],
                weather["min_tempreture"],
                weather["avg_wind_speed"],
                weather["snow"],
                weather["analyze"],
                weather["21"],
                weather["22"],
                weather["23"],
                weather["24"],
                weather["1"],
                weather["2"],
                weather["3"],
                weather["4"],
                weather["5"],
                weather["6"],
                weather["7"],
                weather["yesterday"]
            )
        bot_msg = msg

    return bot_msg


def main():
    """ LINE BOTメイン処理 """
    

    # 天気予報ページ情報取得
    soup = get_page_info()
    soup2 = get_page_info_2()


    # 今日明日の天気予報情報
    weather_list = get_wether_info(soup, soup2)
    
    # LINE BOTメッセージ
    
    if (weather_list[0]["analyze"]) ==  "観測できません":
        pass
    
    else:
        msg = create_msg(weather_list)
        messages = TextSendMessage(text=msg)
        line_bot_api = LineBotApi(CH_TOKEN)
        line_bot_api.push_message(USER_ID, messages=messages)






if __name__ == "__main__":
    main()


# 全体のブラッシュアップと可読性の向上 日付の助教を修正(おそらく<bold>タグの除去で解決)
#前日の気温を考慮 観測可能時の気温を閾値にして気温を変化
