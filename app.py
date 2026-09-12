import os
import httpx
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


@scheduler.task('cron', id='run_sync_once_per_minute', minute=0)
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
    if asset["status"]["status"] == "OFFLINE":
      results.append({
          "id": asset["id"],
          "name": asset["name"],
          "status": asset["status"]["status"],
          "downtimeType": asset["status"]["downtimeType"],
          "description": asset["status"]["description"],
          "startedAt": dt.fromisoformat(asset["status"]["startedAt"]).date()
        })
      continue

    results.append({
      "id": asset["id"],
      "name": asset["name"],
      "status": asset["status"]["status"]
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