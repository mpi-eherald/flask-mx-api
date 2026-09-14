import os
import httpx
from benedict import benedict
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_apscheduler import APScheduler
from datetime import datetime as dt

load_dotenv()

class Config:
  SCHEDULER_API_ENABLED = True


assetStatus = []


app = Flask(__name__)
app.config.from_object(Config)

scheduler = APScheduler()
scheduler.init_app(app) 


@scheduler.task('cron', id='run_sync_once_per_minute', minute="*")
def sync_asset_status():
  global assetStatus
  print("Syncing MaintainX asset status")
  token = os.getenv('MAINTAINX_TOKEN')
  baseUrl = 'https://api.getmaintainx.com/v1/assets?expand=status&limit=200'
  headers = {
    'Authorization': f'Bearer {token}' 
  }

  r = httpx.get(baseUrl, headers=headers)

  assets = r.json()["assets"]

  results = []
    
  for asset in assets:
    a = benedict(asset)
    try:
      if 'status.customStatus' in a:
        results.append({
          "id": asset["id"],
          "name": asset["name"],
          "status": asset["status"]["customStatus"]["label"].upper(),
          "downtimeType": asset["status"]["downtimeType"],
          "description": asset["status"]["description"],
          "startedAt": dt.fromisoformat(asset["status"]["startedAt"]).date()
        })
        continue
    except:
      pass

    # if asset["status"]["customStatus"] in asset:
    #   results.append({
    #     "id": asset["id"],
    #     "name": asset["name"],
    #     "status": asset["status"]["customStatus"]["label"],
    #     "downtimeType": asset["status"]["downtimeType"],
    #     "description": asset["status"]["description"],
    #     "startedAt": dt.fromisoformat(asset["status"]["startedAt"]).date()
    #   })

    if a["status"]["status"] == "OFFLINE":
      results.append({
          "id": a["id"],
          "name": a["name"],
          "status": a["status"]["status"],
          "downtimeType": a["status"]["downtimeType"],
          "description": a["status"]["description"],
          "startedAt": dt.fromisoformat(a["status"]["startedAt"]).date()
        })
      continue

    results.append({
      "id": a["id"],
      "name": a["name"],
      "status": a["status"]["status"]
    })

  assetStatus = sorted(results, key=lambda x: x["status"])
  print(f"Success: synced {len(assets)} assets")


@app.route("/")
def root():
  return render_template('asset_status.html', assets=assetStatus)


with app.app_context():
  sync_asset_status()


scheduler.start()



if __name__ == "__main__":
  app.run()