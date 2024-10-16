import asyncio
import time
import datetime

import aiohttp
import aiofiles
import json
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class HHru:
    def __init__(self, phone, password, proxy):
        super().__init__()
        self.phone = phone
        self.password = password
        self.proxy = {'https': proxy}
        self.switch = False if proxy == 'None' else True
        self.user_agent = UserAgent().chrome
        self.xsrf = None
        self.hhtoken = None
        self.boundary = 'boundary'
        self.resume_src = dict()
        self.resume_active = dict()
        self.notifications = True

    async def request(self, method, url, headers=None, data=None):
        async with aiohttp.ClientSession() as session:
            action = getattr(session, method)
            if self.switch:
                async with action(url, headers=headers, data=data, proxy=self.proxy['https']) as response:
                    await response.text()
                    return response
            else:
                async with action(url, headers=headers, data=data) as response:
                    await response.text()
                    return response

    async def _get_cookie_anonymous(self) -> None:
        url = 'https://hh.ru/'
        headers = {'user-agent': self.user_agent}
        response = await self.request('head', url, headers=headers)
        cookie = str(response.headers)
        self.xsrf = re.search(r"(?<=_xsrf=).+?;", cookie).group()[:-1]
        self.hhtoken = re.search(r"(?<=hhtoken=).+?;", cookie).group()[:-1]

    async def _get_request_data(self, resume: str = None):
        headers = {
            'content-type': f'multipart/form-data; boundary={self.boundary}',
            'cookie': f'_xsrf={self.xsrf}; hhtoken={self.hhtoken};',
            'user-agent': self.user_agent,
            'x-xsrftoken': f'{self.xsrf}',
        }
        if resume is None:
            data = f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="_xsrf"\r\n\r\n{self.xsrf}\r\n' \
                   f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="backUrl"\r\n\r\nhttps://hh.ru/\r\n' \
                   f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="failUrl"\r\n\r\n/account/login\r\n' \
                   f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="remember"\r\n\r\nyes\r\n' \
                   f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="username"\r\n\r\n{self.phone}\r\n' \
                   f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="password"\r\n\r\n{self.password}\r\n' \
                   f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="username"\r\n\r\n{self.phone}\r\n' \
                   f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="isBot"\r\n\r\nfalse\r\n--{self.boundary}--\r\n'
        else:
            data = f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="resume"\r\n\r\n{resume}\r\n' \
                   f'--{self.boundary}\r\nContent-Disposition: form-data; ' \
                   f'name="undirectable"\r\n\r\ntrue\r\n' \
                   f'--{self.boundary}--\r\n'
        return headers, data

    async def login(self) -> bool:
        print(f'-------  {datetime.datetime.now()}  -------\nНачать авторизацию')
        await self._get_cookie_anonymous()
        print('Анонимный файл cookie получен')
        url = 'https://hh.ru/account/login'
        headers, data = await self._get_request_data()
        print('Данные запроса для входа получены')
        response = await self.request('post', url, headers=headers, data=data)
        print('Получен ответ на запрос авторизации')
        cookie = str(response.headers)
        print('Файл cookie после получения запроса авторизации')
        self.xsrf = re.search(r"(?<=_xsrf=).+?;", cookie).group()[:-1]
        print(f'xsrf после получения запроса авторизации: {self.xsrf}')
        hhtoken = re.search(r"(?<=hhtoken=).+?;", cookie)
        print('hhtoken получен')
        if hhtoken is not None:
            self.hhtoken = hhtoken.group()[:-1]
            print(f'hhtoken после получения запроса авторизации: {self.hhtoken}')
            data = dict(xsrf=self.xsrf, hhtoken=self.hhtoken)
            async with aiofiles.open('config/tokens.json', 'w') as file:
                await file.write(json.dumps(data))
            print('Токены сохранены в файле')
            return True
        else:
            print('Ошибка входа')
            return False

    async def raise_resume(self, resume: str) -> int:
        print(f'-------  {datetime.datetime.now()}  -------\nНачало поднятия резюме')
        print(f'поднятие резюме {resume}')
        url = "https://hh.ru/applicant/resumes/touch"
        headers, data = await self._get_request_data(resume)
        print(f'отправка запроса на {url}')
        response = await self.request('post', url, headers=headers, data=data)
        print(f'статус ответа: {response.status}')
        return response.status

    async def get_resumes(self) -> bool:
        url = 'https://hh.ru/applicant/resumes'
        headers, _ = await self._get_request_data()
        print(f'-------  {datetime.datetime.now()}  -------\nНачало получения резюме')
        response = await self.request('get', url, headers=headers)
        print('Получен ответ на запрос резюме')
        if response.status == 200:
            print('Статус ответа: OK')
            soup = BeautifulSoup(await response.text(), 'lxml')
            resumes = soup.select('div[data-qa="resume"]')
            # print(f'Resumes !!!!! :{resumes}')
            self.resume_src = dict()
            for resume in resumes:
                title = resume.get("data-qa-title")
                # link = resume.select_one("a[data-qa='resume-title-link']").get("href")
                link = resume.select_one("a[data-sentry-element='Card']").get("href")
                print(f'Резюме "{title}" получено. Ссылка: {link}')
                link = link.split("/")[-1].split("?")[0]
                self.resume_src[title] = link
            print('Источники резюме сохранены.')
            return True
        else:
            print('Статус ответа: не OK')
            return False

    async def add_resume_active(self, title: str, hour: int, minute: int) -> None:
        result = time.localtime(time.time())
        t = (result.tm_year, result.tm_mon, result.tm_mday, hour, minute, result.tm_sec, result.tm_wday,
             result.tm_yday, result.tm_isdst)

        unixtime = int(time.mktime(t))
        self.resume_active[title] = dict(resume_id=self.resume_src[title],
                                         time=dict(hour=hour, minute=minute, seconds=result.tm_sec),
                                         unixtime=unixtime, lunixtime=unixtime-60*60*4)
        await asyncio.sleep(0.01)

    async def del_resume_active(self, title: str) -> None:
        await asyncio.sleep(0.01)
        return self.resume_active.pop(title, False)
