import os
import httpx
from dotenv import load_dotenv
from flask import Flask, render_template
from datetime import datetime as dt

load_dotenv()

token = os.getenv('MAINTAINX_TOKEN')
baseUrl = 'https://api.getmaintainx.com/v1/assets?expand=status'
headers = {
  'Authorization': f'Bearer {token}' 
}

r = httpx.get(baseUrl, headers=headers)
print(r.status_code)

assets = r.json()["assets"]
assetStatus = []
for asset in assets:
  if asset["status"]["status"] == "OFFLINE":
    assetStatus.append({
        "id": asset["id"],
        "name": asset["name"],
        "status": asset["status"]["status"],
        "downtimeType": asset["status"]["downtimeType"],
        "description": asset["status"]["description"],
        "startedAt": dt.fromisoformat(asset["status"]["startedAt"]).date()
      })
    continue

  assetStatus.append({
    "id": asset["id"],
    "name": asset["name"],
    "status": asset["status"]["status"]
  })

sorted_assets = sorted(assetStatus, key=lambda x: x['status'])

app = Flask(__name__)

@app.route("/")
def root():
  return render_template('asset_status.html', assets=sorted_assets)