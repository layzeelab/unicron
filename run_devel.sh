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

readonly TZ=Europe/Amsterdam
readonly UNICRON_KEY=`openssl rand -base64 16 | md5 | head -c16`
readonly CONTAINER=unicron-dev
readonly API_PORT=8185

bold=`tput bold`
green=`tput setaf 2`
reset=`tput sgr0`

echo "${green}Setting dev env...${reset}"

docker run --name=redis-$CONTAINER -d redis:alpine

echo "${green}Building and starting the container...${reset}"

docker build -t $CONTAINER -f ./Dockerfile . && \
docker run --name=$CONTAINER --link=redis-$CONTAINER -p $API_PORT:80 \
	-e "UNICRON_KEY=$UNICRON_KEY" \
	-e "TZ=$TZ" \
	-e "DEBUG=0" \
	-e "REDIS_HOST=redis-$CONTAINER" \
	-e "REDIS_PORT=6379" \
	-e "REDIS_DB=0" \
	-e "REDIS_PASSWORD=" \
	-e "EMAIL_FROM=example@gmail.com" \
	-e "SMTP_HOST=smtp.gmail.com" \
	-e "SMTP_PORT=587" \
	-e "SMTP_TLS=1" \
	-e "SMTP_USER=example@gmail.com" \
	-e "SMTP_PASSWORD=p4ssw0rd" \
	-d $CONTAINER

if [ $? -eq 0 ]; then
	echo "${green}Unicron is up!${reset}"
	echo "API URL http://localhost:$API_PORT/api/"
	echo "${bold}Press any key to clean up and quit dev environment.${reset}"
	read -n 1
fi

echo "${green}Cleaning up containers...${reset}"

docker stop $CONTAINER > /dev/null 2>&1 && docker rm $CONTAINER
docker stop redis-$CONTAINER > /dev/null 2>&1 && docker rm redis-$CONTAINER
