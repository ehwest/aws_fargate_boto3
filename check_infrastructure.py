import requests
import sys
import time

try:
    if not sys.argv[1]:
        print("Please specify DNS name")
        sys.exit(1)
    else:
        dns = sys.argv[1]
except IndexError:
    print("Please specify DNS name")
    sys.exit(1)

while True:
    url = "http://" + dns + "/phpmyadmin"
    try:
        r = requests.get(url)
    except Exception as e:
        print("Error: {}".format(e))
        sys.exit(1)
    if r.ok:
        print("Ready to work")
        sys.exit(0)
    print("{} response {}".format(url, r.status_code))
    s = 10
    print("Lets wait {} seconds".format(s))
    time.sleep(s)

