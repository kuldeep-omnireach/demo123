#!/bin/bash
# To run in EKS we need to set --host to 0.0.0.0, if you want to bind to localhost you can remove the --host setting
exec uvicorn --app-dir src main:app --host 0.0.0.0

# if you want to run with DataDog trace
#exec ddtrace-run uvicorn --app-dir src main:app --host 0.0.0.0