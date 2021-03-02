# -*- mode: ruby -*-
# vi: set ft=ruby :
#
#

Vagrant.configure(2) do |config|

  config.vm.synced_folder ".", "/pgcli"

  pgcli_version = ENV['version']
  pgcli_description = "Postgres CLI with autocompletion and syntax highlighting"

  config.vm.define "debian" do |debian|
    debian.vm.box = "bento/debian-10.8"
    debian.vm.provision "shell", inline: <<-SHELL
    echo "-> Building DEB on `lsb_release -d`"
    sudo apt-get update
    sudo apt-get install -y libpq-dev python-dev python-setuptools rubygems
    sudo apt install -y python3-pip
    sudo pip3 install --no-cache-dir virtualenv virtualenv-tools3
    sudo apt-get install -y ruby-dev
    sudo apt-get install -y git
    sudo apt-get install -y rpm librpmbuild8

    sudo gem install fpm

    echo "-> Cleaning up old workspace"
    sudo rm -rf build
    mkdir -p build/usr/share
    virtualenv build/usr/share/pgcli
    build/usr/share/pgcli/bin/pip install /pgcli

    echo "-> Cleaning Virtualenv"
    cd build/usr/share/pgcli
    virtualenv-tools --update-path /usr/share/pgcli > /dev/null
    cd /home/vagrant/

    echo "-> Removing compiled files"
    find build -iname '*.pyc' -delete
    find build -iname '*.pyo' -delete

    echo "-> Creating PgCLI deb"
    sudo fpm -t deb -s dir -C build -n pgcli -v #{pgcli_version} \
        -a all \
        -d libpq-dev \
        -d python-dev \
        -p /pgcli/ \
        --after-install /pgcli/post-install \
        --after-remove /pgcli/post-remove \
        --url https://github.com/dbcli/pgcli \
        --description "#{pgcli_description}" \
        --license 'BSD'

    SHELL
  end

  
# This is considerably more messy than the debian section.  I had to go off-standard to update
# some packages to get this to work.

  config.vm.define "centos" do |centos|

    centos.vm.box = "bento/centos-7.9"
    centos.vm.box_version = "202012.21.0"
    centos.vm.provision "shell", inline: <<-SHELL
    #!/bin/bash
    echo "-> Building RPM on `hostnamectl | grep "Operating System"`"
    export PATH=/usr/local/rvm/gems/ruby-2.6.3/bin:/usr/local/rvm/gems/ruby-2.6.3@global/bin:/usr/local/rvm/rubies/ruby-2.6.3/bin:/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/rvm/bin:/root/bin
    echo "PATH -> " $PATH

#####
### get base updates

    sudo yum install -y rpm-build gcc postgresql-devel python-devel  python3-pip git python3-devel

######
### install FPM, which we need to install to get an up-to-date version of ruby, which we need for git

    echo "-> Get FPM installed"
    # import the necessary GPG keys
    gpg --keyserver hkp://pool.sks-keyservers.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3 7D2BAF1CF37B13E2069D6956105BD0E739499BDB
    sudo gpg --keyserver hkp://pool.sks-keyservers.net --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3 7D2BAF1CF37B13E2069D6956105BD0E739499BDB
    # install RVM
    sudo curl -sSL https://get.rvm.io | sudo bash -s stable
    sudo usermod -aG rvm vagrant
    sudo usermod -aG rvm root
    sudo /usr/local/rvm/bin/rvm alias create default 2.6.3
    source /etc/profile.d/rvm.sh
    
    # install a newer version of ruby.  centos7 only comes with ruby2.0.0, which isn't good enough for git.
    sudo yum install -y ruby-devel
    sudo /usr/local/rvm/bin/rvm install 2.6.3
    
    #
    # yes,this gives an error about generating doc but we don't need the doc. 

    /usr/local/rvm/gems/ruby-2.6.3/wrappers/gem install fpm

######

    sudo pip3 install virtualenv virtualenv-tools3
    echo "-> Cleaning up old workspace"
    rm -rf build
    mkdir -p build/usr/share
    virtualenv build/usr/share/pgcli
    build/usr/share/pgcli/bin/pip install /pgcli

    echo "-> Cleaning Virtualenv"
    cd build/usr/share/pgcli
    virtualenv-tools --update-path /usr/share/pgcli > /dev/null
    cd /home/vagrant/

    echo "-> Removing compiled files"
    find build -iname '*.pyc' -delete
    find build -iname '*.pyo' -delete

    cd /home/vagrant
    echo "-> Creating PgCLI RPM"
    /usr/local/rvm/gems/ruby-2.6.3/gems/fpm-1.12.0/bin/fpm -t rpm -s dir -C build -n pgcli -v #{pgcli_version} \
        -a all \
        -d postgresql-devel \
        -d python-devel \
        -p /pgcli/ \
        --after-install /pgcli/post-install \
        --after-remove /pgcli/post-remove \
        --url https://github.com/dbcli/pgcli \
        --description "#{pgcli_description}" \
        --license 'BSD'


  SHELL


  end


end

