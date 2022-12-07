#! /bin/sh
set -e

case $1 in
	web)
	  export PYTHONPATH="${PYTHONPATH}:."
	  pipenv run python app/application.py
		;;
	?)
		echo "run app components: [web|worker|beat]. Or any other shell command."
		;;
	*)
		exec "$@"
		;;
esac
