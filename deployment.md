# Deployment

## Requirements

```
pip install daphne
pip install channels_redis
```

- Redis (only for production)
   - https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04
   - Change supervised from no to systemd in /etc/redis/redis.conf
- Elasticsearch


## Setup
- create folder for static as configured in labs/labs/settings_prod.py
- create htpasswd and labs/secret_key.txt
- copy labs/labs/setting_prod.py to labs/labs/settings.py
- copy static files:

```
python manage.py collectstatic
```

- Run:

```
daphne labs.asgi:application
```

## Deployment
- stop daphne server
- after git pull, check settings_prod for changes 

```
git pull
python manage.py collectstatic
python manage.py migrate
daphne labs.asgi:application

```

## Apache as proxy

Install websocket proxy:
```
a2enmod proxy_wstunnel
```

Apache config

```
<VirtualHost *:80>
        ServerAdmin webmaster@localhost

        ServerName labs.judaicalink.org

        DocumentRoot /data/judaicalink/labs.judaicalink.org/htdocs
        <Location />
                AuthType Basic
                AuthName "Restricted"
                AuthUserFile "/data/judaicalink/judaicalink-labs/htpasswd"
                Require user hdm
        
        </Location>

        ProxyPass /static !
        ProxyPass /ws ws://localhost:8000/ws
        ProxyPassReverse /ws ws://localhost:8000/ws
        ProxyPass / http://localhost:8000/
        ProxyPassReverse / http://localhost:8000/

        ProxyRequests On
        ProxyPreserveHost On
        <Proxy *>
                Require all granted
        </Proxy>
        Alias "/static/" "/data/judaicalink/judaicalink-labs/static/"
        <Directory "/data/judaicalink/judaicalink-labs/static/">
                Require all granted
        </Directory>
</VirtualHost>
```


## Nginx as proxy
```
server {
        listen 80;
        listen [::]:80;

        server_name labs2.judaicalink.org labs.judaicalink.org;
        auth_basic "not public";
        auth_basic_user_file /data/judaicalink-labs/.htpasswd;

        location /static/ {
                root /data/judaicalink-labs/;
        }
        location /ws/ {
            proxy_pass http://localhost:8000/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_set_header Host $host;
        }
        location / {
                proxy_pass http://localhost:8000;
        }
}
```
