#!/bin/sh
curl -X POST -H "Authorization: Token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwiZXhwIjoxNzkyNzg5NDQ3LCJodHRwX3Jvb3QiOiJodHRwOi8vbG9jYWxob3N0IiwidXNlcl9pZCI6IjJjMTUxNDM1LTA2YTktNDgzZS04YWRjLTUyNzBiMzIyYjdhMCIsInVzZXJuYW1lIjoiYWRtaW4ifQ.VSbSrYiVN17augkzq4yOtyf1inFzblb2JCK2m1zcB1Y" -d '{"tl_id":59  }' http://146.185.166.173:8000/api/likes/add

./delete.sh

