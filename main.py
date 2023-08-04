from kivy.lang import Builder
from kivy.uix.recycleview import RecycleView
from kivy.properties import ListProperty
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.list import ThreeLineListItem
import re

import requests
import threading
from bs4 import BeautifulSoup
from kivy.clock import Clock
from plyer import notification

KV = '''
BoxLayout:
    orientation: 'vertical'

    MDTopAppBar:
        title: "SMC TRADING"
        left_action_items: [["menu", lambda x: app.navigation_draw()]]
        elevation: 2

    RV:
        viewclass: 'CustomThreeLineListItem'
        data: app.data
        RecycleBoxLayout:
            default_size: None, dp(96)  # Adjust the height here as needed
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'    

    MDRaisedButton:
        text: 'Get Pairs'
        on_release: app.start_background_task()
        disabled: app.loading
        size_hint_x: 1

'''

symbols = [
    {
        "symbol": "NZDCHF"
    },
    {
        "symbol": "NZDUSD"
    },
    {
        "symbol": "AUDCHF"
    },
    {
        "symbol": "AUDUSD"
    },
    {
        "symbol": "CADCHF"
    },
    {
        "symbol": "NZDCAD"
    },
    {
        "symbol": "EURGBP"
    },
    {
        "symbol": "AUDCAD"
    },
    {
        "symbol": "USDCHF"
    },
    {
        "symbol": "EURCHF"
    },
    {
        "symbol": "EURUSD"
    },
    {
        "symbol": "AUDNZD"
    },
    {
        "symbol": "GBPCHF"
    },
    {
        "symbol": "GBPUSD"
    },
    {
        "symbol": "EURCAD"
    },
    {
        "symbol": "EURAUD"
    },
    {
        "symbol": "EURNZD"
    },
    {
        "symbol": "GBPAUD"
    },
    {
        "symbol": "NZDJPY"
    },
    {
        "symbol": "AUDJPY"
    },
    {
        "symbol": "CADJPY"
    },
    {
        "symbol": "USDJPY"
    },
    {
        "symbol": "EURJPY"
    },
    {
        "symbol": "CHFJPY"
    },
    {
        "symbol": "GBPJPY"
    },
    {
        "symbol": "GBPNZD"
    },
    {
        "symbol": "XAUUSD"
    },
    {
        "symbol": "GBPCAD"
    },
    {
        "symbol": "USDCAD"
    }
]

class CustomThreeLineListItem(ThreeLineListItem):
    pass


class RV(RecycleView):
    pass


class WebsiteContentApp(MDApp):
    data = ListProperty([])
    loading = False

    def build(self):
        return Builder.load_string(KV)


    def extract_numeric_value(text):
        try:
            return int(''.join(filter(str.isdigit, text)))
        except ValueError:
            return None
        
    def get_website_content(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                content = response.text
                # Process the website content here as per your requirement
                # For demonstration, we'll append the content to the data list
                self.data.append({
                    "text": url,
                    "secondary_text": content,
                    "tertiary_text": "",
                })
        except requests.exceptions.RequestException as e:
            print("Error:", e)
        finally:
            self.loading = False

    def start_background_task(self):
        background_thread = threading.Thread(target=self.get_sentiments)
        background_thread.start()
        print("Background task started.")

    def get_sentiments(self):
        url = "https://www.myfxbook.com/community/outlook"
        res = requests.get(url)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, 'html.parser')

        # print(soup)
        tables = soup.find_all(
            "table", class_='table table-bordered table-vertical-middle text-center margin-top-5')
        if len(tables) == 0:
            return []

        table = soup.find("table", id='outlookSymbolsTable')
        tbody = table.find('tbody', id='outlookSymbolsTableContent')
        trs = tbody.find_all('tr', class_='outlook-symbol-row')

        data = []
        for tr in trs:
            tds = tr.find_all('td')

            tdavgshort = tds[3]
            tdavglong = tds[4]
            td_current_price = tds[5]

            p_short, p_short_pip = tdavgshort.contents[0:2]
            sp_short = tdavgshort.find_all('span')
            sp_long = tdavglong.find_all('span')

            current_price = td_current_price.find('span')
            symbol = tds[0].a.string.strip()
            if any(s['symbol'] == symbol for s in symbols):
                data.append({
                    'symbol': symbol,
                    'pendingbuy': sp_short[0].string.strip(),
                    'piptopendingbuy': int(list(map(int, re.compile('-?\d+').findall(sp_short[1].string.strip())))[0]),
                    'pendingsell': sp_long[0].string.strip(),
                    'piptopendingsell': int(list(map(int, re.compile('-?\d+').findall(sp_long[1].string.strip())))[0]),
                    'current_price': current_price.string.strip()
                })

        pip_distance = 120
        data = [item for item in data if item['piptopendingbuy']
                           >= pip_distance or item['piptopendingsell'] >= pip_distance]
        self.data.clear()  # Clear existing data
        self.data.extend([
            {
                "text": f"{item['symbol']}",
                "secondary_text": f"Pending Buy: {item['pendingbuy']} / pips distance: {item['piptopendingbuy']}",
                "tertiary_text": f"Pending Sell: {item['pendingsell']} / pips distance: {item['piptopendingsell']}",
            }
            for item in data
        ])

    def check_data_length(self, dt):
        print(len(self.data))
        self.start_background_task()  # Fetch data again
        if len(self.data) > 0:
            notification_title = "New data available!"
            notification_text = "There are new pairs data available."
            notification.notify(title=notification_title,
                                message=notification_text)

    def on_start(self):
        # Start the background task to fetch data initially
        self.start_background_task()

        # Schedule the task to check data length every 1 hour (3600 seconds)
        Clock.schedule_interval(self.check_data_length, 3600)

    def navigation_draw(self):
        print("Navigation drawer opened!")


if __name__ == "__main__":
    app = WebsiteContentApp()
    app.start_background_task()
    app.run()
