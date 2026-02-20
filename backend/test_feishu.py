import requests
import os

APP_TOKEN = "IsL0w4WpDiYGhekvnKAcLEHJn9c"
TABLE_ID = "tblAyqYazaUimRnc"
APP_ID = "cli_a9045d9277f8dcc1"
APP_SECRET = "KHpqxcUp7iyiugqxPHS0Tc0xC7ioXgsw"

def get_tenant_access_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    if data.get("code") == 0:
        return data.get("tenant_access_token")
    else:
        print(f"Failed to get token: {data}")
        return None

def get_table_records(token):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)

if __name__ == "__main__":
    access_token = get_tenant_access_token()
    if access_token:
        get_table_records(access_token)
