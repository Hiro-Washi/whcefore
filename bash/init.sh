sudo sysctl –w net.core.rmem_default=10000000
sudo sysctl –w net.core.wmem_default=10000000
sudo sysctl –w net.core.rmem_max=10000000
sudo sysctl –w net.core.wmem_max=10000000

sudo cefnetdstop
sleep 1
sudo csmgrdstop
sleep 1
sudo csmgrdstart
sleep 1
sudo cefnetdstart
echo "DO TEST: sudo cefputfile ccnx:/test -f Readme.md"
