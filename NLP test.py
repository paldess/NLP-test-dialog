import spacy
nlp = spacy.load("ru_core_news_sm")
import re
import nltk
import pymorphy2
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')



# загрузка датасета и отделение слов только менеджера(за ненадобностью проверки слов клиента в задании)

data = pd.read_csv('test_data.csv')
data = data[data['role'] == 'manager']
data.head()




morf = pymorphy2.MorphAnalyzer()

# класс объектов для каждой строки
class NLP:

    def __init__(self, origin):
        self.origin = origin                         # оригинальный текст из данных
        self.lemma = self.func(self.origin)          # лемматизированный текст строки
        self.name_maneger = self.name_func(self.lemma) # имя менеджера
        self.greeting = self.greet(self.origin)      # приветствие
        self.farewell = self.farel(self.origin)      # прощание
        self.company = self.compan(self.lemma)       # название компании

    # функция лемматизации    
    def func(self, text):
        doc = nlp(text)
        return ' '.join([i.lemma_ for i in doc])

    # поиск имени менеджера
    def name_func(self, text):
        if re.search(r'меня \w+ звать', text):
            return re.findall(r'меня \w+ звать', text)[0].split()[-2]
        elif re.search(r'меня звать \w', text):
            return re.findall(r'меня звать \w+', text)[0].split()[-1]
        elif re.search(r'это \w+', text):
            name = re.findall(r'это \w+', text)[0].split()[-1]
            if 'Name' in morf.parse(name)[0].tag:
                return name
            else:
                return None
        else:
            return None

    # поиск приветствия
    def greet(self, text):
        if re.search(r'здравств|добрый день|добрый вечер|доброе утро', text):
            return re.findall(r'здравств.*|добрый день|добрый вечер|доброе утро', text)[0]
        else:
            return False

    # поиск прощания
    def farel(self, text):
        if re.search(r'до свидан|всего хорош|всего добр', text):
            return re.findall(r'до свидан.*|всего хорош.*|всего добр.*', text)[0]
        else:
            return False

    # поиск названия компании
    def compan(self, text):

        if re.search(r'компания', text):
            name = re.findall(r'компания \w+ \w+', text)[0].split()
            if 'NOUN' in morf.parse(name[1])[0].tag:
                return name[1]
            elif 'NOUN' in morf.parse(name[2])[0].tag:
                return ' '.join(name[1:])
            else:
                return None
        else:
            return None



# сбор информации по данным
dict_s = {}                         # словарь извлеченных данных

# извлечение номеров диалогов из столбца 'dlg_id' и дальнейшая обработка по каждому номеру диалога
for i in data['dlg_id'].unique():
    data_iter = data[data['dlg_id'] == i]      # данные диалога одного диалога

    # установка в словарь значений по умолчанию со всеми отрицательными критериями
    dict_s[f'dlg_id_{i}'] = {'name_maneger': 'Не представился',
                             'greeting': False, 'farewell': False,
                             'criterion': False, 'company': 'Не названа'}
    # поиск необходимых слов в каждой строке диалога
    for string in data_iter['text']:
        # создание класса строки 
        out = NLP(string)

        # изменение данных в итоговом словаре если в параметрах класса не отрицательные(отсутствующие) значения
        if out.name_maneger != None:
            dict_s[f'dlg_id_{i}']['name_maneger'] = out.name_maneger

        if out.greeting != False:
            dict_s[f'dlg_id_{i}']['greeting'] = out.greeting
        if out.farewell != False:
            dict_s[f'dlg_id_{i}']['farewell'] = out.farewell
        if out.company != None:
            dict_s[f'dlg_id_{i}']['company'] = out.company

        # проверка выполнения требуемого критерия по приветствию и прощанию менеджера
        if dict_s[f'dlg_id_{i}']['greeting'] != False and dict_s[f'dlg_id_{i}']['farewell'] != False:
            dict_s[f'dlg_id_{i}']['criterion'] = True



# создание итоговой таблицы данных
# 
data_out = data.copy()

# добавление пустых столбцов в датафрейм
for i in list(dict_s['dlg_id_0'].keys()):
    data_out[i] = 0

# заполнение полей из словаря значений
for dlg_id in data['dlg_id'].unique():
    for column in list(dict_s['dlg_id_0'].keys()):
        data_out[column][data_out['dlg_id'] == dlg_id] = dict_s[f'dlg_id_{dlg_id}'][column]



# сохранение в файл
name_file = 'data_parse_py.csv'
data_out.to_csv(name_file, index=False)

