#!/bin/bash

# Attendre que MySQL soit prêt
while ! mysqladmin ping -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" --silent; do
    sleep 1
done

python app.py 