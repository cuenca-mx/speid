#!/usr/bin/env bash
export PATH=/bin:/usr/bin:/sbin:/usr/sbin

# Define basic functions
function print_info {
        echo -n -e '\e[1;36m'
        echo -n $1
        echo -e '\e[0m'
}

function print_warn {
        echo -n -e '\e[1;33m'
        echo -n $1
        echo -e '\e[0m'
}

print_info "Read parameters"

# Read parameters
while getopts u:h:p:P: option
do
case "${option}"
in
u) USER=${OPTARG};;
h) HOST=${OPTARG};;
P) PASS=${OPTARG};;
p) PORT=${OPTARG};;
esac
done

print_info "Will conect to: $USER:$PASS@$HOST:$PORT"

# Install postgres

print_info "Install postgres"

echo "deb http://apt.postgresql.org/pub/repos/apt/ stretch-pgdg main" > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -q -y install "$1"

# Install pandas

print_info "Install DEV"

make install-dev

# Read data from postgres and put it into a csv file
print_info "Connect to postgres and extract transactions"
psql -U USER -h ${HOST} -P ${PASS} -p ${PORT} -c "\copy (SELECT * FROM public.transactions) to 'transactions.csv' with csv header"

print_info "Connect to postgres and extract requests"
psql -U USER -h ${HOST} -P ${PASS} -p ${PORT} -c "\copy (SELECT * FROM public.requests) to 'requests.csv' with csv header"

print_info "Connect to postgres and extract events"
psql -U USER -h ${HOST} -P ${PASS} -p ${PORT} -c "\copy (SELECT * FROM public.events) to 'requests.csv' with csv header"


# Load data into mongodb
print_info "Connect to mongodb and send info"
# mongoimport --uri ${DATABASE_URI} --jsonArray transactions.json
# mongoimport --uri ${DATABASE_URI} --jsonArray requests.json

# Wipe data
print_info "Delete temp files"
rm -f transactions.json requests.json
