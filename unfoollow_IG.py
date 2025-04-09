import os
import sys
import time
import json
import random
import re

def install(package):
    try:
        __import__(package)
    except ImportError:
        print(f"يتم تثبيت مكتبة {package}...")
        os.system(f"pip install {package}")

install("requests")
install("tabulate")

from datetime import datetime
import requests
from tabulate import tabulate

# المسارات
CACHE_DIR = "cache"
SESSION_FILE = os.path.join(CACHE_DIR, "session.json")

# روابط انستجرام
INSTAGRAM_URL = "https://www.instagram.com"
LOGIN_URL = f"{INSTAGRAM_URL}/accounts/login/ajax/"
PROFILE_URL = f"{INSTAGRAM_URL}/api/v1/users/web_profile_info/"

session = requests.Session()

class API_All:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.headers = {}
        self.cookies = {}

    def setup_headers(self):
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36"
        headers = {"User-Agent": ua}
        res1 = session.get(INSTAGRAM_URL, headers=headers)
        csrf_token = re.search(r'"csrf_token":"(.*?)"', res1.text)
        ig_app_id = re.search(r'X-IG-App-ID":"(.*?)"', res1.text)

        if not csrf_token or not ig_app_id:
            raise Exception("لا يمكننا الحصول على CSRF أو معرّف التطبيق.")

        csrf = csrf_token.group(1)
        app_id = ig_app_id.group(1)

        self.headers = {
            "User-Agent": ua,
            "X-CSRFToken": csrf,
            "X-IG-App-ID": app_id,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{INSTAGRAM_URL}/accounts/login/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
            "Origin": INSTAGRAM_URL,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

        self.cookies = res1.cookies.get_dict()
        self.cookies["csrftoken"] = csrf

    def login(self) -> bool:
        payload = {
            "username": self.username,
            "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(datetime.now().timestamp())}:{self.password}",
            "optIntoOneTap": "false",
            "facebook_hiden_fields": "{}",
            "username_in_email": self.username,
            "queryParams": "",
        }

        res = session.post(LOGIN_URL, headers=self.headers, data=payload, cookies=self.cookies)
        data = res.json()

        if data.get("authenticated"):
            self.cookies.update(res.cookies.get_dict())
            return True

        if data.get("two_factor_required"):
            print("التحقق الثنائي مفعل. يجب إلغاء تفعيله أولاً.")
        elif data.get("message") == "checkpoint_required":
            print("يجب تأكيد عملية التسجيل عبر التطبيق.")
        else:
            print("فشل تسجيل الدخول:", data)

        return False

    def get_user_info(self) -> dict:
        res = session.get(PROFILE_URL, params={"username": self.username}, headers=self.headers)
        return res.json()["data"]["user"]

class INSTAAAAA_VIP:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.api = API_All(username, password)

    def setup_session(self):
        if not os.path.isdir(CACHE_DIR):
            os.makedirs(CACHE_DIR)

        self.api.setup_headers()

        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                session.cookies.update(json.load(f))
        else:
            if not self.api.login():
                sys.exit(1)
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session.cookies.get_dict(), f)

    def display_account_info(self, user_info: dict):
        account_data = [
            ["اسم المستخدم", user_info.get("username", "")],
            ["الاسم الكامل", user_info.get("full_name", "")],
            ["رقم الحساب", user_info.get("id", "")],
            ["المتابعين", user_info.get("edge_followed_by", {}).get("count", "غير متاح")],
            ["المتابعين لهم", user_info.get("edge_follow", {}).get("count", "غير متاح")],
            ["المنشورات", user_info.get("edge_owner_to_timeline_media", {}).get("count", "غير متاح")],
            ["السيرة الذاتية", user_info.get("biography", "")],
            ["الرابط الخارجي", user_info.get("external_url", "")],
            ["هل الحساب خاص؟", user_info.get("is_private", False)],
            ["هل الحساب موثّق؟", user_info.get("is_verified", False)],
            ["حساب تجاري", user_info.get("is_business_account", False)],
            ["الفئة", user_info.get("category_name", "غير متاح")],
            ["البريد الإلكتروني", user_info.get("business_email", "غير متاح") if user_info.get("is_business_account") else "غير متاح"]
        ]
        print("\n" + tabulate(account_data, headers=["الحقل", "القيمة"], tablefmt="fancy_grid"))

    def fetch_following(self, user_id: str):
        url = f"https://i.instagram.com/api/v1/friendships/{user_id}/following/?count=50"
        headers = self.api.headers.copy()
        headers["User-Agent"] = headers.get("User-Agent", "")
        headers["X-CSRFToken"] = headers.get("X-CSRFToken", "")
        headers["X-IG-App-ID"] = headers.get("X-IG-App-ID", "")
        res = session.get(url, headers=headers, cookies=self.api.cookies)
        return res.json().get("users", [])

    def unfollow_all_following(self, user_id: str):
        print("\nجاري إلغاء متابعة الأشخاص الذين لا يتابعونك...")

        unfollowed_log = open("unfollowed.txt", "a", encoding="utf-8")
        total_unfollowed = 0

        while True:
            users = self.fetch_following(user_id)
            if not users:
                print("لا يوجد أشخاص آخرين لإلغاء متابعتهم.")
                break

            for user in users[:10]:  # تقييد العملية إلى 10 مستخدمين فقط في الدقيقة
                user_id = user["pk"]
                username = user["username"]

                is_followed_by = user.get("is_followed_by", False)

                if not is_followed_by:  # إذا كان الشخص لا يتابعك
                    url = f"https://i.instagram.com/api/v1/friendships/destroy/{user_id}/"
                    res = session.post(url, headers=self.api.headers, cookies=self.api.cookies)

                    if res.status_code == 200:
                        print(f"[{total_unfollowed+1}] تم إلغاء متابعة: {username}")
                        unfollowed_log.write(username + "\n")
                        total_unfollowed += 1
                    else:
                        print(f"فشل إلغاء متابعة {username} - كود: {res.status_code}")
                else:
                    print(f"{username} يتابعك، لن يتم إلغاء متابعته.")

                time.sleep(6)  # كل 6 ثواني

            print("بانتظار دقيقة قبل الاستمرار...")
            time.sleep(60)

        unfollowed_log.close()
        print(f"تم إلغاء متابعة {total_unfollowed} شخصاً.")

def main():
    username = input("أدخل اسم المستخدم: ")
    password = input("أدخل كلمة المرور: ")

    bot = INSTAAAAA_VIP(username, password)
    bot.setup_session()

    info = bot.api.get_user_info()
    bot.display_account_info(info)

    confirm = input("\nهل تريد حذف كل من تتابعهم؟ (نعم/لا): ").lower()
    if confirm == "نعم":
        bot.unfollow_all_following(info["id"])

if __name__ == "__main__":
    main()