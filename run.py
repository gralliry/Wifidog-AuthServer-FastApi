#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Description:
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # 添加参数 port，设置默认值为 8080
    parser.add_argument('-=', '--port', type=int, default=8080, help='Port number to run the server on (default: 8080)')
    args = parser.parse_args()
    uvicorn.run("app:app", host="0.0.0.0", port=args.port, reload=True)
