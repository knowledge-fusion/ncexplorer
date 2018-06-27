#! /bin/sh
set -e

case $1 in
	web)
	    cd app && python application.py
		;;
	worker)
		celery worker -A celery_worker.celery --loglevel=INFO -P gevent \
		  --without-mingle --no-color --purge
		;;
	beat)
		rm -f /var/run/celerybeat.pid
		celery beat -A celery_worker.celery -s $CELERY_BEAT_SCHEDULE --loglevel=INFO --no-color \
		  --pidfile /var/run/celerybeat.pid
		;;
	?)
		echo "run tac components: [web|worker|beat]. Or any other shell command."
		;;
	*)
		exec "$@"
		;;
esac
