# -*- coding: utf-8 -*-
import json
from colorama import init
from vk_api import VkApi
from vk_api.exceptions import AuthError, VkApiError
import re
import sqlite3

TZ = 3600 * 3
USER_AGENT = 'KateMobileAndroid/52.4 (Android 8.1; SDK 27; armeabi-v7a; Xiaomi Redmi 5A; ru)'
config = {}


class Colors:
    INFO = '\033[34;1m'
    OK = '\033[32;1m'
    WARNING = '\033[33;1m'
    ERROR = '\033[31;1m'
    RESET = '\033[0m'


def con(text):
    print(text + Colors.RESET)


def captcha_handler(captcha):
    r = input('Введите капчу ' + captcha.get_url() + ': ').strip()
    return captcha.try_again(r)


def main():
    init()

    global config
    try:
        with open('config.json') as f:
            config = json.load(f)

    except FileNotFoundError:
        config = {'limit': 1000, 'types': {'chats': True, 'groups': True, 'users': True}}

        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)

    if config['limit'] <= 0:
        config['limit'] = 1e10
    s = 'YOUR_VK_TOKEN'
    if len(s) == 220:
        vk = VkApi(token=s, captcha_handler=captcha_handler)

        vk.http.headers.update({
            'User-agent': USER_AGENT,
            'Timeout':'10'
        })

    elif ':' in s:
        sp = s.split(':')
        vk = VkApi(sp[0], sp[1], app_id=2685278, captcha_handler=captcha_handler)
        vk.http.headers.update({
            'User-agent': USER_AGENT,
            'Timeout':'10'
        })

        try:
            vk.auth(token_only=True)
        except AuthError:
            con(Colors.ERROR + 'Неверный логин или пароль')
            return
    else:
        con(Colors.WARNING + 'Введите данные для входа в виде "логин:пароль" или "токен"')
        return

    try:
        user = vk.method('users.get')[0]
    except VkApiError as ex:
        if ex.__dict__['error']['error_code'] == 5:
            error_text = 'неверный токен'
        else:
            error_text = str(ex)

        con(Colors.ERROR + 'Ошибка входа: ' + error_text)
        return
    con(Colors.OK + 'Вход выполнен')

    #Получение списка групп человека
    groups=[]
    gr=vk.method('groups.get',{'fields':'description'})
    groups.append(gr)
    print(groups)

    #Получение информации о группе
    groups_desc=[]
    gr_desc=vk.method('groups.getById',{'group_id':'128124426'})
    groups_desc.append(gr_desc)
    print(groups_desc)

    #Получение подписчиков группы
    try:
         for gr_id in group_ids:
            groups_members_asc=[]
            gr_mem_asc=vk.method('groups.getMembers',{'count':1000,'group_id':'GROUP_ID','sort':'id_asc'})
            groups_members_asc.append(gr_mem_asc)
            items_asc = groups_members_asc[0]['items']


            groups_members_desc=[]
            gr_mem_desc=vk.method('groups.getMembers',{'count':1000,'group_id':'GROUP_ID','sort':'id_desc'})
            groups_members_desc.append(gr_mem_desc)
            items_desc = groups_members_desc[0]['items']

    except: print('error calling getMembers method')

    items= items_asc+items_desc

    #указываем путь до базы данных, где будут храниться все данные
    with open('PATH_TO_FILE_WITH_IDS', 'a', encoding='utf-8') as file:
        for i in items:
            file.write(str(i)+'\n')
        print('запись')


    lines_list = []
    # Открываем файл для чтения
    with open('PATH_TO_FILE_WITH_IDS', 'r') as file:
        # Читаем строки из файла и добавляем их в список
        for line in file:
            # Удаляем лишние пробелы и символы новой строки
            cleaned_line = line.strip()
            # Добавляем очищенную строку в список
            lines_list.append(cleaned_line)


    conn = sqlite3.connect('PATH_TO_DB')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS mytable
                  (id TEXT, first_name TEXT, last_name TEXT, chair_name TEXT, name TEXT, faculty_name TEXT, groups TEXT )''')
    
    # получение информации с профиля
    for i in lines_list:
            pr=vk.method('users.get',{'user_id':i,
                                    'fields':'activities',
                                    'fields':'about',
                                    'fields':'bdate',
                                    'fields':'books',
                                    'fields':'career',
                                    'fields':'education',
                                    'fields':'schools',
                                    'fields':'interests',
                                    'fields':'universities'})
            try:
                groups=vk.method('users.getSubscriptions',{'user_id':i})
            except:
                print('скрытый профиль')
            formatted_string = str(pr)
            formatted_string = formatted_string.replace('[', '').replace(']', '').replace('{', '').replace('}',''). replace("'",'')
            if 'universities' in formatted_string:
                formatted_string = formatted_string.replace('universities:','')
                matches = re.findall(r'(\w+):\s([^,]+)', formatted_string)
                data_dict = {}
                del groups['users']
                groups=str(groups)
                groups=groups.replace('{','').replace('}','').replace('groups','').replace(':','').replace('items','').replace("'",'').replace("''",'').replace('[','').replace(']','').replace(' ','')
                data_str = re.sub(r"count\d+,", "", groups)
                items = data_str.split(',')
                data=''
                for match in matches:
                    key, value = match
                    data_dict[key] = value
                for item in items:
                    try:
                        # получение информации о группе
                        subs=vk.method('groups.getById',{'group_id':item,'fields':'activity,description'})
                        filtered_subs = [{'name': item['name'], 'activity': item['activity'],'description':item['description']} for item in subs]
                        filtered_subs=str(filtered_subs)
                        filtered_subs=filtered_subs.replace('[','').replace(']','').replace('{','').replace('}','').replace("'",'').replace("'",'')
                        data+=filtered_subs + '\n'
                    except:
                        print('пустой профиль')
                cursor.execute("INSERT INTO mytable (id, first_name, last_name, chair_name, name, faculty_name,groups) VALUES (?,?,?,?,?,?,?)",
                (data_dict.get('id', ''), data_dict.get('first_name', ''),data_dict.get('last_name', ''),data_dict.get('chair_name', ''),data_dict.get('name', ''),data_dict.get('faculty_name', ''),data))
                conn.commit()
                print('строка записана')
            else:
                print('ERROR with calling users.get method')


