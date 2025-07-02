#!/bin/bash
ffmpeg -i - -vcodec mpeg4 -b:v 2M -acodec aac -f mpegts - | cefputstream ccnx:/stream -r 2 -b 1400 -t 3600 -e 3600

