from flask import Flask, redirect, url_for, render_template, request
import datetime, requests, numpy

app = Flask(__name__)
URL = "https://api.pro.coinbase.com"
products = requests.get(URL + "/products")
data_list = products.json()
all_pairs = []
for pair in data_list:
    all_pairs.append(pair["id"].upper())


@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        dt = request.form["datetime"]
        user_pair = request.form["pair"]
        return redirect(url_for("result", trading_pair=user_pair.upper(), date_time=dt))
    else:
        return render_template("home.html", pair_list=all_pairs)


@app.route("/<trading_pair>/<date_time>")
def result(trading_pair, date_time):
    start = datetime.datetime.fromisoformat(date_time + ":00")
    end = start + datetime.timedelta(hours=0, minutes=1)
    end_date, end_time = end.strftime("%Y-%m-%d %H:%M:%S").split()
    start_date, start_time = start.strftime("%Y-%m-%d %H:%M:%S").split()

    path = "/products/" + trading_pair + "/candles"
    query = {
        "start": start_date + "T" + start_time,
        "end": end_date + "T" + end_time,
        "granularity": "60"
    }

    try:
        response = requests.get(URL + path, params=query)
        response.raise_for_status()

        data = response.json()
        if not data:
            na = "Data not available at this specific date and time"
            return render_template("result.html", open=na, pair=trading_pair, date=start_date, time=start_time[:-3])
        else:
            candle = data[0]
            open = str(candle[3]) if isinstance(candle[3], int) else str(numpy.format_float_positional(candle[3]))
            high = str(candle[2]) if isinstance(candle[2], int) else str(numpy.format_float_positional(candle[2]))
            low = str(candle[1]) if isinstance(candle[1], int) else str(numpy.format_float_positional(candle[1]))
            close = str(candle[4]) if isinstance(candle[4], int) else str(numpy.format_float_positional(candle[4]))
            return render_template("result.html", open="Open: "+open, high="High: "+high, low="Low: "+low,
                                   close="Close: "+close, pair=trading_pair, date=start_date, time=start_time[:-3])
    except requests.exceptions.HTTPError as err:
        return render_template("result.html", open="ERROR", pair=trading_pair, date=start_date, time=start_time[:-3])
    except requests.exceptions.ConnectionError as err:
        return render_template("result.html", open="ERROR", pair=trading_pair, date=start_date, time=start_time[:-3])


if __name__ == "__main__":
    app.run(debug="true")