git clone https://github.com/io_server.git /usr/local/io_server
cd /usr/local/io_server

sudo apt-get -y update
sudo apt-get -y ssh ruby mc htop redis-server redis-tools git python-pip supervisor
sudp cp /etc/redis/redis.conf /etc/redis/redis.conf.save
sudo sed -i 's/bind 127.0.0.1/bind 0.0.0.0/g' /etc/redis/redis.conf
sudo sed -i 's/daemonize yes/daemonize no/g' /etc/redis/redis.conf
sudo service redis-server stop
sudo update-rc.d redis-server disable

# redis client
sudo git clone https://github.com/marians/rebrow.git /usr/local/rebrow
sudo pip install -r /usr/local/rebrow/requirements.txt

# io server dependencies
sudo pip install -r requirements.txt

# configure supervisor
sudo cp conf/supervisord.conf /etc/supervisor/supervisord.conf
sudo service supervisor stop
sudo service supervisor start

