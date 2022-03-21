import os, hmac, hashlib, requests, base64, datetime, sys
import numpy

URL = "https://api.pro.coinbase.com"
CB_ACCESS_TIMESTAMP = str(int(datetime.datetime.now().timestamp()))

CB_ACCESS_KEY = os.environ.get("CB_ACCESS_KEY")
CB_ACCESS_PASSPHRASE = os.environ.get("CB_ACCESS_PASSPHRASE")
SECRET = os.environ.get("SECRET")


class CBAuthentication(requests.auth.AuthBase):
    def __call__(self, request):
        message = CB_ACCESS_TIMESTAMP + request.method + request.path_url
        cb_access_sign = base64.b64encode(hmac.new(base64.b64decode(SECRET), bytes(message, 'utf-8'), digestmod=hashlib.sha256).digest())
        request.headers.update({
            "cb-access-key": CB_ACCESS_KEY,
            "cb-access-passphrase": CB_ACCESS_PASSPHRASE,
            "cb-access-sign": cb_access_sign,
            "cb-access-timestamp": CB_ACCESS_TIMESTAMP
        })

        return request


def account_balance():
    try:
        response = requests.get(URL + "/accounts", auth=CBAuthentication())
        response.raise_for_status()

        account_list = response.json()
        for account in account_list:
            if float(account["balance"]) > 0:
                print("You have " + account["available"] + " " + account["currency"])
    except requests.exceptions.HTTPError as err:
        print(err)
    except requests.exceptions.ConnectionError as err:
        print(err)


def trading_pair():
    response = requests.get("https://api.pro.coinbase.com/products")
    data = response.json()
    all_pairs = set()
    for pair in data:
        all_pairs.add(pair["id"].lower())

    print()
    print("Enter a trading pair (ex. btc-usd, eth-usdc): ")
    while True:
        user_pair = input()
        if user_pair == "1":
            sys.exit()
        if user_pair.strip().lower() in all_pairs:
            return user_pair
        else:
            print("Not a valid trading pair, please try again or press 1 to quit")


def date_time():
    print()
    print("Now, enter the date and time in UTC or press 2 to get current data (ex. 2020-08-24 14:30): ")
    while True:
        date_input = input()
        if date_input == "1":
            sys.exit()
        elif date_input == "2":
            return datetime.datetime.utcnow().replace(microsecond=0) - datetime.timedelta(hours=0, minutes=2)
        try:
            date_time_list = date_input.split()
            year, month, day = map(int, date_time_list[0].split("-"))
            hour, minute = map(int, date_time_list[1].split(":"))
            date_obj = datetime.datetime(year, month, day, hour, minute, 0)
            if date_obj > datetime.datetime.utcnow():
                print("Date is in the future, please try again or press 1 to quit")
                continue
            else:
                return date_obj
        except ValueError:
            print("Not a valid date, please try again or press 1 to quit")


def ohlc_data():
    pair = trading_pair()
    date_time_obj = date_time()
    date_time_obj_plus_minute = date_time_obj + datetime.timedelta(hours=0, minutes=1)
    date_str = date_time_obj.strftime("%Y-%m-%d")
    time_str = date_time_obj.strftime("%H:%M:%S")
    end_time_str = date_time_obj_plus_minute.strftime("%H:%M:%S")

    path = "/products/" + pair + "/candles"
    query = {
        "start": date_str + "T" + time_str,
        "end": date_str + "T" + end_time_str,
        "granularity": "60"
    }

    try:
        response = requests.get(URL + path, params=query)
        response.raise_for_status()

        data = response.json()
        if not data:
            print("Data for " + pair + " not available at that date and time")
        else:
            candle = data[0]
            print()
            print("Historical OHLC data for " + pair + " on " + date_str + " at " + time_str[:-3] + " UTC")
            open = str(candle[3]) if isinstance(candle[3], int) else str(numpy.format_float_positional(candle[3]))
            high = str(candle[2]) if isinstance(candle[2], int) else str(numpy.format_float_positional(candle[2]))
            low = str(candle[1]) if isinstance(candle[1], int) else str(numpy.format_float_positional(candle[1]))
            close = str(candle[4]) if isinstance(candle[4], int) else str(numpy.format_float_positional(candle[4]))
            print("Open: " + open)
            print("High: " + high)
            print("Low: " + low)
            print("Close: " + close)
    except requests.exceptions.HTTPError as err:
        print(err)
    except requests.exceptions.ConnectionError as err:
        print(err)


print("Press 1 to get account balances, or 2 to get historical data for a trading pair at a specific date and time: ")
while True:
    user_input = input()
    if user_input == "1":
        account_balance()
        break
    elif user_input == "2":
        ohlc_data()
        break
    else:
        print("Not a valid input, try again")