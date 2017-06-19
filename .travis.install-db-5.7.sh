#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

set -e

if [ "$EXTRAS" = 'all,mysql' ]; then
  echo mysql-apt-config mysql-apt-config/select-server select mysql-5.7 | sudo debconf-set-selections
  wget http://dev.mysql.com/get/mysql-apt-config_0.7.3-1_all.deb
  sudo dpkg --install mysql-apt-config_0.7.3-1_all.deb
  sudo apt-get update -q
  sudo apt-get install -q -y --force-yes -o Dpkg::Options::=--force-confnew mysql-server
  sudo service mysql restart
  sudo mysql_upgrade

  # reset root password
  sudo service mysql stop || echo "mysql not stopped"
  sudo stop mysql-5.6 || echo "mysql-5.6 not stopped"
  sudo  mysqld_safe --skip-grant-tables &
  sleep 4
  sudo mysql -e "use mysql; update user set authentication_string=PASSWORD('') where User='travis'; update user set plugin='mysql_native_password';FLUSH PRIVILEGES;"
  sudo kill -9 `sudo cat /var/lib/mysql/mysqld_safe.pid`
  sudo kill -9 `sudo cat /var/run/mysqld/mysqld.pid`

  sudo service mysql restart
fi
