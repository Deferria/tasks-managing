import datetime

time_sct = "2026-04-12T15:59:59Z"

dt = datetime.datetime.strptime(time_sct, "%Y-%m-%dT%H:%M:%SZ")

if dt < datetime.datetime.now():
    print("过期了")

print(dt)