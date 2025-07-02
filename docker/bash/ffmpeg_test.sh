#!/bin/bash
ffplay -video_size 1921x1080 -framerate 60 -window_title "Lifebook00 Webcam Feed"  /dev/video0 | cefputstream ccnx:/p/test
