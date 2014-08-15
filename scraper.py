import os
import requests
import json
import sqlite3
import time

conn = sqlite3.connect('./data.sqlite')
db = conn.cursor()

def get(url):
  username = os.environ['MORPH_GH_USERNAME']
  password = os.environ['MORPH_GH_PASSWORD']
  r = requests.get(url, auth=(username, password), headers={'Connection':'close'})
  if(r.ok):
    headers = r.headers
    body = json.loads(r.content)
    remaining = int(headers["x-ratelimit-remaining"])
    reset = int(headers["x-ratelimit-reset"])
    now = int(time.time())
    wait = (reset - now)

    for user in body:
      data = {
        'id': user['id'],
        'login': user['login'],
        'gravatar_id': user['gravatar_id'],
        'site_admin': to_bool(user["site_admin"])
      }
      save(data)

    last = str(body[-1]['id'])
    print last, remaining, wait

    if remaining < 5:
      time.sleep(wait+10)
    else:
      get('https://api.github.com/users?since='+last)


def save(data):
  db.execute("insert into data values (?,?,?,?)", (data["id"],data["login"],data["gravatar_id"],data["site_admin"]) )
  conn.commit()

def to_bool(s):
  return 1 if s == True else 0

def main():
  db.execute('''
    CREATE TABLE IF NOT EXISTS data( 
      id INTEGER, 
      login TEXT, 
      gravatar_id VARCHAR(32), 
      site_admin INTEGER,
      UNIQUE(id)
    )'''
  )
  db.execute('SELECT * FROM data ORDER BY id DESC LIMIT 1;')
  users = db.fetchall()
  if not users:
    get('https://api.github.com/users')
  else: 
    last = str(users[0][0])
    get('https://api.github.com/users?since='+last)

if __name__ == '__main__':
    main()
