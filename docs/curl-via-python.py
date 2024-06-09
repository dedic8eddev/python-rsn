import requests
import json
url = "http://localhost:9001/api/autocomplete/wine"
data = {"query":"N'importnawak"}
headers = {
    'Authorization': 'Token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZTU4Yzg2NDctMzAzMi00M2VlLWI3ZTctNmQ2YmY4ZmQ2ZWZlIiwiaHR0cF9yb290IjoiaHR0cDovL2xvY2FsaG9zdCIsInVzZXJuYW1lIjoidGVzdGhhaGEiLCJlbWFpbCI6InRlc3RoYWhhQGV4LmNvbSIsImV4cCI6MTgzNzU1NTk3M30.RCttDcrEmcDk4HPgk5Z4V8pZZ-hKfc1iTE3XXfSwYoQ',
    'Content-Length': str(len(str(data)))
}
r = requests.post(url, data = json.dumps(data), headers=headers)
print(r.json())