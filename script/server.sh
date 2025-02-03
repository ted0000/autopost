#!/bin/bash

# 쉘 스크립트를 실행할 때, Python 스크립트를 호출합니다.
uvicorn main_web:app --reload --port 8088

