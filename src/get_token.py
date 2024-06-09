#!/usr/bin/python
import base64
import sys

if len(sys.argv) != 3:
    print("Usage: python get_token.py username password")
    sys.exit(1)

message = '{}:{}'.format(sys.argv[1], sys.argv[2])
message_bytes = message.encode('utf-8')
base64_bytes = base64.b64encode(message_bytes)
print('Basic {}'.format(base64_bytes.decode('utf-8')))
