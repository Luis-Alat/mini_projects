#!/bin/bash

set -e

ShowArguments() {

	# Arguments passed by reference
	local -n ARG=$1
	local KEY

	printf "\nARGUMENTS\n"
    for KEY in "${!ARG[@]}"; do
            echo "${KEY}: ${ARG[$KEY]}"
    done
    printf "\n"

}

declare -A ARGUMENTS

while [ $# -gt 0 ]; do

	ARGUMENTS[$1]=$2

	case $1 in 
		-h|--host)
			HOST_POSTGRES=$2
			shift 2
			;;
		-U|--user)
			USER_POSTGRES=$2
			shift 2
			;;
		*)
			echo "Invalid argument: $1"
			exit 1
			;;
	esac
done

ShowArguments ARGUMENTS

printf "WARNING: ANY EXISTING DATABASE WILL BE DROPPED. CONTINUE? [Yes][No]: "
read INPUT

if [ "$INPUT" != "Yes" ] && [ "$INPUT" != "No" ]; then
	echo "Option not valid. Ending script..."
	exit 1
fi

if [ "$INPUT" == "No" ]; then
	echo "Ending script..."
	exit 1
fi

psql -U $USER_POSTGRES -h $HOST_POSTGRES << EOF
	
	DROP DATABASE IF EXISTS youtube;
	CREATE DATABASE youtube;

	\c youtube;

	CREATE TABLE languages (
		id_language SMALLSERIAL UNIQUE NOT NULL PRIMARY KEY,
		code VARCHAR(9) NOT NULL
	);

	CREATE TABLE titles (
		id_video VARCHAR(12) UNIQUE NOT NULL PRIMARY KEY,
		title VARCHAR NOT NULL
	);

	CREATE TABLE users (
		id_user SERIAL UNIQUE NOT NULL PRIMARY KEY,
		name VARCHAR NOT NULL
	);

	CREATE TABLE comments (
		id_comment SERIAL UNIQUE NOT NULL PRIMARY KEY,
		comment text,
		published_date DATE,
		likes INTEGER,
		id_user INTEGER,
		id_video VARCHAR(12),
		id_language SMALLINT
	);

	ALTER TABLE comments 
	ADD CONSTRAINT fk_user FOREIGN KEY (id_user) REFERENCES users (id_user);

	ALTER TABLE comments
	ADD CONSTRAINT fk_video FOREIGN KEY (id_video) REFERENCES titles (id_video);

	ALTER TABLE comments
	ADD CONSTRAINT fk_language FOREIGN KEY (id_language) REFERENCES languages (id_language);

EOF

