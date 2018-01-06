#!/usr/bin/env python
#
#  Run against a .md file to generate a table of contents based on the headings
#  contained in that file.
#

import re
import sys

RE_TOKENS = re.compile('[A-Za-z0-9-]+')

## Table of Contents
## 1. Introduction
## 2. Comparing Map-Reduce to Traditional Parallelism
### 2.1. Traditional Parallel Applications
### 2.2. Data-intensive Applications
### 3. Hadoop - A Map-Reduce Implementation
### 3.1. The Magic of HDFS
### 3.2. Map-Reduce Jobs
#### 3.2.1. The Map Step
#### 3.2.2. The Reduce Step
## 4. Summary

headers = []
min_level = 999
for line in open(sys.argv[1], 'r').readlines():
    if line.startswith('#'):
        headers.append(line.strip())
        hashes = line.split()[0]
        if len(hashes) < min_level:
            min_level = len(hashes)

for header in headers:
    hashes, title = header.split(None, 1)
    if title.lower() == "table of contents":
        continue
    anchor = '-'.join(filter(lambda x: x != '-' and x, RE_TOKENS.findall(title))).lower()
    print "%s* [%s](#%s)" % (
        "    " * (len(hashes) - min_level),
        title,
        anchor)
