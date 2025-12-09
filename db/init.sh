psql -U bucrep -d bucrep --no-password -f /init.sql --no-owner -v 
touch /tmp/restore-done.txt
