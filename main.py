import requests
from bs4 import BeautifulSoup as BS


def get_content(html):
    soup = BS(html, 'html.parser')
    return soup


def get_user_id(html):
    # Получаем pupilId
    table = html.find('table', class_='pesonal-data__info')
    for table_inform in table.find_all('tbody'):
        rows = table_inform.find_all('tr')
        for row in rows:
            user_inform = row.find('td', class_='personal-data__info-value personal-data__info-value_bold')
            if user_inform == None:
                continue
            if user_inform.text.isdigit():
                user_id = user_inform.text
                return user_id


def get_user_info(html):
    # Получаем rooId, instituteId, departmentId
    info = html.find_all('a', class_='d-block')
    links = []
    for link in info:
        links = link.get('href').split('/')
    res = []
    for i in links:
        if i.isdigit():
            res.append(i)
    return res


def get_marks_table(log, passw):
    login_password = {'login': log, 'password': passw}
    url = 'https://elschool.ru/logon/index'
    try:
        with requests.Session() as s:
            logging_to_site = s.post(url, data=login_password)
            main_page = get_content(logging_to_site.text)
            user_id = get_user_id(main_page)
            user_info = get_user_info(main_page)

            table = s.get(f'https://elschool.ru/users/diaries/grades?rooId={user_info[0]}&instituteId={user_info[1]}&departmentId={user_info[2]}&pupilId={user_id}')
            html = get_content(table.text)
            marks_table = html.find('table', class_='table table-bordered GradesTable MobileGrades')

            tds = []
            subject = []
            for lessons in marks_table.find_all('tbody'):
                rows = lessons.find_all('tr')
                for row in rows:
                    half = row.find('td', class_='grades-period-name').text
                    if half == '3 чет.' or half == '2 пол.':
                        marks = row.find_all('span')
                        for el in range(len(marks)):
                            marks[el] = int(marks[el].text)
                        marks_second_half = [marks]
                        for el in marks_second_half:
                            tds.append(el)

            for name_lesson in marks_table.find_all('thead'):
                names = name_lesson.find_all('th')
                for name in names:

                    subject.append(name.text)

            data = {}
            for i in range(len(subject)):
                data.update({subject[i]: tds[i]})

            return data
    except Exception:
        return 'Неправильно введены данные!'


# Функкция для уведомления о новой оценке в дневнике
def get_data(old, new):
    html_old = get_content(old)

    # Получеам список оценок
    def get_marks(html):
        tds = []
        for lessons in html.find_all('tbody'):
            rows = lessons.find_all('tr')
            for row in rows:
                half = row.find('td', class_='grades-period-name').text
                if half == '2 пол.' or half == '3 чет.':
                    marks = row.find_all('span')
                    for el in range(len(marks)):
                        marks[el] = int(marks[el].text)
                    marks_second_half = [marks]
                    for el in marks_second_half:
                        tds.append(el)
        return tds

    # Получеам список уроков
    def get_lessons(html):
        subject = []
        for name_lesson in html.find_all('thead'):
            names = name_lesson.find_all('th')
            for name in names:
                subject.append(name.text)
        return subject

    # Объединяем оценки и уроки в список
    def unite_data(les, scores):
        data = {}
        for i in range(len(les)):
            data.update({les[i]: scores[i]})
        return data

    data_now = new
    lessons_old, subjects_old = get_lessons(html_old), get_marks(html_old)
    data_old = unite_data(lessons_old, subjects_old)

    # Если новый словарь оценок, равен старому, то ничего не делаем, иначе ввыводим разницу
    if data_now == data_old:
        return False
    else:
        result = []
        for key, value in data_now.items():
            if data_old[key] != data_now[key]:
                new_marks = data_now[key][len(data_old[key]):]
                if len(new_marks) > 1:
                    result.append('Новые оценки по предмету {}: {}'.format(key, ' '.join(map(str, new_marks))))
                elif len(new_marks) == 1:
                    result.append('Новая оценка по предмету {}: {}'.format(key, ' '.join(map(str, new_marks))))
        return '\n'.join(result)

# Функция для получения html страницы дневника
def elschool_html(log, passw):
    try:
        login_password = {'login': log, 'password': passw}
        url = 'https://elschool.ru/logon/index'
        headers = {'Pragma': 'no-cache', 'Cache-Control': 'no-cache'}
        with requests.Session() as s:
            logging_to_site = s.post(url, data=login_password, headers=headers)
            main_page = get_content(logging_to_site.text)
            user_id = get_user_id(main_page)
            user_info = get_user_info(main_page)
            table = s.get(f'https://elschool.ru/users/diaries/grades?rooId={user_info[0]}&instituteId={user_info[1]}&departmentId={user_info[2]}&pupilId={user_id}')
            table_html = get_content(table.text)
            marks_table = table_html.find('table', class_="table table-bordered GradesTable MobileGrades")

            return str(marks_table)
    except:
        return 'Неправильно введены данные!'
