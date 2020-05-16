import requests
import time
from selenium import webdriver
import datetime
import re
import lxml.html
etree = lxml.html.etree

def get_cookie(login_url,user_data):
    print('正在获取cookie...')
    chrome_driver = r'C:\Users\CBZ\Desktop\chromedriver.exe'
    option = webdriver.ChromeOptions()
    option.add_argument('headless')  # 设置option
    driver = webdriver.Chrome(executable_path=chrome_driver,chrome_options=option)
    driver.get(login_url)
    for i in range(3):
        try:
            driver.find_element_by_id('username').send_keys(user_data['username'])
            driver.find_element_by_id('password').send_keys(user_data['password'])
            driver.find_element_by_xpath(
            "//div[@class='auth_tab_content_item w264']/form[@id='casLoginForm']/p[4]/button[@class='auth_login_btn_dl full_width']").click()
        except:
            break
    time.sleep(1)
    cookies = driver.get_cookies()
    # return cookies
    SessionId = f'{cookies[2]["value"]}'
    _d_id = f'{cookies[1]["value"]}'
    iPlanetDirectoryPro = f'{cookies[0]["value"]}'
    cookie = f'ASP.NET_SessionId={SessionId};_d_id={_d_id};iPlanetDirectoryPro={iPlanetDirectoryPro}'
    with open('cookies.txt','w') as fp:
        fp.write(cookie)
        fp.close()
    print('获取成功!')


def get_infos(reserv_infos):
    with open('cookies.txt','r') as fp:
        cookie = fp.read()
        fp.close()
    headers = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36",
        "Referer" : "http://zizhu.nbu.edu.cn/clientweb/xcus/ic2/Default.aspx",
        "Host":"zizhu.nbu.edu.cn",
        "Cookie":cookie
    }
    url = f"http://zizhu.nbu.edu.cn/ClientWeb/pro/ajax/device.aspx?byType=devcls&classkind={reserv_infos['classkind']}&display=fp&md=d&room_id={reserv_infos['room_id']}&purpose=&selectOpenAty=&cld_name=default&date={reserv_infos['date']}&fr_start={reserv_infos['fr_start']}&fr_end={reserv_infos['fr_end']}&act=get_rsv_sta&_=1589375776301"
    response = requests.get(url,headers=headers)
    response_json = response.json()
    return response_json

def get_stea_infos(json_infos):
    infos = []
    results = []
    for i in json_infos['data']:
        infos.append({'seat_name': i['name'], 'seat_ID': i['devId'], 'data': i['ts'], 'freeTime': i['freeTime'],'freeSta':i['freeSta'],
                      'ops': i['ops']})
    for i in infos:
        if (i['data'] != [] and i['freeTime'] >= 90):

            available_tm = ''
            owners = ''
            # 座位开放时间
            op_start_time = datetime.datetime.strptime(f"{i['ops'][0]['date']} {i['ops'][0]['start']}",'%Y-%m-%d %H:%M')
            op_end_time = datetime.datetime.strptime(f"{i['ops'][0]['date']} {i['ops'][0]['start']}", '%Y-%m-%d %H:%M')
            # 已预约时间
            times = []

            for owner in i['data']:
                start_time = datetime.datetime.strptime(owner['start'], '%Y-%m-%d %H:%M')
                end_time = datetime.datetime.strptime(owner['end'], '%Y-%m-%d %H:%M')
                times.append({'start_time': start_time, 'end_time': end_time})

                # owners += owner['start'].split(' ')[1] + '~' + owner['end'].split(' ')[1] + owner['owner'] + '   '
            # print(f"{i['seat_name']}  {owners}  剩余可预约时长{i['freeTime']}")

            if (len(times) > 1):
                # 按照预约时间先后排序
                for n in range(0, len(times)):
                    for m in range(0, len(times) - 1):
                        if (times[n]['start_time'] < times[m]['start_time']):
                            t = times[n]
                            times[n] = times[m]
                            times[m] = t
                # 计算可预约的时间段
                delat_mins = (times[0]['start_time'] - op_start_time).total_seconds() / 60
                if (delat_mins >= 35):
                    available_tm += f"{datetime.datetime.strftime(op_start_time, '%H:%M')}~{datetime.datetime.strftime(times[0]['start_time'], '%H:%M')}" + "\t"
                    delat_mins = (op_end_time - times[len(times) - 1]['end_time']).total_seconds() / 60
                if (delat_mins >= 35):
                    available_tm += f"{datetime.datetime.strftime(times[len(times) - 1]['end_time'], '%H:%M')}~{datetime.datetime.strftime(op_end_time, '%H:%M')}" + "\t"

                for n in range(0, len(times) - 1):
                    delat_mins = (times[n + 1]['start_time'] - times[n]['end_time']).total_seconds() / 60
                    if (delat_mins >= 40):
                        available_tm += f"{(times[n]['end_time'] + datetime.timedelta(minutes=5)).strftime('%H:%M')}~{(times[n + 1]['start_time'] + datetime.timedelta(minutes=-5)).strftime('%H:%M')}" + "\t"
            if (available_tm != ''):
                results.append(f"{i['seat_name']}  {i['seat_ID']}  可预约时间段为：{available_tm}")
        else:
            if (i['freeSta'] == -3):
                results.append(f"{i['seat_name']}  {i['seat_ID']}  不开放")
            elif (i['freeSta'] == 0):
                results.append(f"{i['seat_name']}  {i['seat_ID']}  可预约时间段为：08:00~20:00")
    return results


def get_my_appt():
    results = []
    with open('cookies.txt','r') as fp:
        cookie = fp.read()
        fp.close()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36",
        "Referer": "http://zizhu.nbu.edu.cn/clientweb/xcus/ic2/Default.aspx",
        "Host": "zizhu.nbu.edu.cn",
        "Cookie": cookie
    }
    my_appt_url = "http://zizhu.nbu.edu.cn/ClientWeb/pro/ajax/center.aspx?act=get_History_resv&strat=90&StatFlag=New&_=1589525439388"
    try:
        resp = requests.get(my_appt_url,headers=headers).json()
        msg = resp['msg']
        seats = re.findall("<a>(.+?)</a>", msg)
        rscIDs = re.findall("rsvId='(\d+?)'", msg)
        times = re.findall("<span class='text-primary'>(.+?)</span>", msg)
        start_times = []
        end_times = []

        for i in range(0, len(times)):
            if (i % 2 == 0):
                start_times.append(times[i])
            else:
                end_times.append(times[i])
        for i in range(0, len(seats)):
            results.append({'rscID':rscIDs[i],'seat':seats[i],'start_time':start_times[i],'end_time':end_times[i]})
        if(results==[]):
            return "当前无预约"
        else:
            return results
    except:
        return '0'

def appt_seat(data):
    result = ''
    with open('cookies.txt','r') as fp:
        cookie = fp.read()
        fp.close()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36",
        "Referer": "http://zizhu.nbu.edu.cn/clientweb/xcus/ic2/Default.aspx",
        "Host": "zizhu.nbu.edu.cn",
        "Cookie": cookie
    }
    url = f"http://zizhu.nbu.edu.cn/ClientWeb/pro/ajax/reserve.aspx?dialogid=&dev_id={data['dev_id']}&lab_id=&kind_id=&room_id=&type={data['type']}&prop=&test_id=&term=&number=&classkind=&test_name=&start={data['start']}&end={data['end']}&start_time={data['start_time']}&end_time={data['end_time']}&up_file=&memo=&act=set_resv&_=1589529429574"

    try:
        resp = requests.get(url,headers=headers).json()
        if (resp['ret'] == 1):
            result += '预约成功！'
        else:
            result += resp['msg']
    except:
        result += '0'
    return result
def cancel_appt(rsvID):
    with open('cookies.txt','r') as fp:
        cookie = fp.read()
        fp.close()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36",
        "Referer": "http://zizhu.nbu.edu.cn/clientweb/xcus/ic2/Default.aspx",
        "Host": "zizhu.nbu.edu.cn",
        "Cookie": cookie
    }
    url = f"http://zizhu.nbu.edu.cn/ClientWeb/pro/ajax/reserve.aspx?act=del_resv&id={rsvID}&_=1589533059153"
    try:
        resp = requests.get(url,headers=headers).json()
        if(resp['ret']==1):
            return '操作成功！'
    except:
        return '操作失败！请检查ID是否正确'

if __name__ == '__main__':
    login_url = 'http://zizhu.nbu.edu.cn'
    user_data = {
        'username':'学号',
        'password':'密码'
    }
    reserv_infos={
        'room_id': '100460330',       #预约房间
        'date': '2020-05-15',     #预约时间
        'classkind': '8',     #"1"->空间  "8"->座位
        'fr_start': '08%3A00',
        'fr_end': '20%3A00'
    }
    appt_infos={
        'dev_id':'100460413',
        'type':'dev',
        'start':'2020-05-16+16%3A40',
        'end':'2020-05-16+20%3A00',
        'start_time':1640,
        'end_time':2000
    }
    #获取图书馆信息
    # infos = get_infos(reserv_infos)
    #
    # #若无法访问，则重新获取cookie
    # while(infos['ret']==-1):
    #     print("cookie已失效，重新获取！")
    #     get_cookie(login_url, user_data)
    #     infos = get_infos(reserv_infos)
    #
    # seat_infos = get_stea_infos(infos) #获取可预约的位置信息,list类型
    # for seat_info in seat_infos:
    #     print(seat_info)

    # appt_result = appt_seat(appt_infos)
    # if(appt_result=='0'):
    #     print('Cookie失效！')
    #     get_cookie(login_url,user_data)
    # print(appt_seat(appt_infos))
    #
    # #获取预约信息
    # if(get_my_appt()=='0'):
    #     print('Cookie失效！')
    #     get_cookie(login_url,user_data)
    # print(get_my_appt())
    # my_appt_infos = get_my_appt()
    # 
    # print(cancel_appt('133234'))






