#!/bin/bash
# (c) layzeelab.com 2018, Armin Ranjbar Daemi (@rmin)
#
# This file is part of Unicron (@layzeelab).
# Unicron is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

set -e
readonly TZ=Europe/Amsterdam
readonly UNICRON_KEY=`openssl rand -base64 16 | md5 | head -c16`
readonly CONTAINER=unicron-test

bold=`tput bold`
green=`tput setaf 2`
reset=`tput sgr0`

echo "${green}Setting test env...${reset}"

docker run --name=redis-$CONTAINER -d redis:alpine

echo "${green}Building and starting the container...${reset}"

docker build -t $CONTAINER -f ./Dockerfile.tests .
docker run --name=$CONTAINER --link=redis-$CONTAINER \
	-e "UNICRON_KEY=$UNICRON_KEY" \
	-e "TZ=$TZ" \
	-e "DEBUG=1" \
	-e "REDIS_HOST=redis-$CONTAINER" \
	$CONTAINER

echo "${green}Cleaning up containers...${reset}"

docker stop $CONTAINER > /dev/null 2>&1 && docker rm $CONTAINER
docker stop redis-$CONTAINER > /dev/null 2>&1 && docker rm redis-$CONTAINER
