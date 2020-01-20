# Deployment

## Requirements

```
pip install daphne
pip install channels_redis
```

- Redis (only for production)
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
