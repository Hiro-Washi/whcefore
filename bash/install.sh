
cd
sudo apt update
sudo apt install libssl-dev automake git
git clone https://github.com/cefore/cefore
git clone https://github.com/cefore/cefpyco
cd cefore
autoconf
automake
./configure --enable-csmgr --enable-cache --enable-cefping
make
sudo make install
# sudo ldconfig
