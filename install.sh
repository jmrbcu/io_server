# change root password
echo "Setting new password for user root..."
sudo passwd root

# install dependencies
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y install ssh ruby mc htop redis-server redis-tools git python-pip supervisor python-serial python-construct python-redis python-hiredis libusb-dev ipython
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.save
sudo sed -i 's/bind 127.0.0.1/bind 0.0.0.0/g' /etc/redis/redis.conf
sudo sed -i 's/daemonize yes/daemonize no/g' /etc/redis/redis.conf
sudo service redis-server stop
sudo update-rc.d redis-server disable

# redis client
sudo git clone https://github.com/marians/rebrow.git /usr/local/rebrow
sudo pip install -r /usr/local/rebrow/requirements.txt

# io server
sudo git clone https://github.com/jmrbcu/io_server.git /usr/local/io_server
sudo pip install --pre -r /usr/local/io_server/requirements.txt
sudo pip install git+https://github.com/jmrbcu/foundation.git

echo "Enter password for user root:"
su -c "python /usr/local/io_server/io_server.py -g"

# BIXOLON printer driver for cups
sudo mkdir /tmp/printer
sudo cp /usr/local/io_server/deps/printer/SPP-100II_Linux_v1.0.0.tar.bz2 /tmp
sudo tar -xvpf /tmp/SPP-100II_Linux_v1.0.0.tar.bz2 -C /tmp/printer/
sudo sh /tmp/printer/SPP-100II_Linux_v1.0.0/setup_v1.0.0.sh
sudo rm -rf /tmp/printer
sudo service cups stop
sudo service cups start

# configure supervisor
sudo cp /usr/local/io_server/conf/supervisord.conf /etc/supervisor/supervisord.conf
sudo service supervisor stop
sudo service supervisor start

# extras
git clone https://github.com/jmrbcu/dotfiles.git .dotfiles
for x in `ls -ha ~/.dotfiles`; do ln -sf ~/.dotfiles/$x ~/$x; done
