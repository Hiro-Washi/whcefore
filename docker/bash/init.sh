#!/bin/bash
sysctl -w net.core.rmem_default=10000000
sysctl -w net.core.wmem_default=10000000
sysctl -w net.core.rmem_max=10000000
sysctl -w net.core.wmem_max=10000000

cefnetdstop
sleep 1
csmgrdstop
sleep 1
cefnetdstart
sleep 1
csmgrdstart
