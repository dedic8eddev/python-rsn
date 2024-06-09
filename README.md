# python-app

## Backend installation

- clone GitHub project
- Move to the src directory `cd src`
- Make sure you have virtualenv installed, and run `virtualenv venv` to create the virtual environment.
- Activate the virtual environment: `source venv/bin/activate`
- Install dependencies `pip install -r requirements.txt`
- Move to the raisin directory inside src `cd raisin`
- Create a local environments file by copying the example `cp env.example .env`. Make sure you configure `RAISIN_LOGFILE_PATH_DIR` to a folder that exists on your computer, with writing permissions.
- Create a `media` directory in the main repo dir (added to .gitignore)
- Make sure you have PostgreSQL 12 installed. Customize the database name and credentials in the .env file.
- Install the `unaccent` extension for Postgres. From the psql console type `create extension unaccent;`
- Go back to the src directory. Run the server `python manage.py runserver`

#### PostgreSQL instructions

```
sudo apt update   
sudo apt -y install postgresql-12 postgresql-client-12
```

I. Create database and user:

```
sudo su - postgres
psql
CREATE DATABASE db_name;
CREATE USER db_user WITH PASSWORD 'db_password';
ALTER USER db_user WITH SUPERUSER;
GRANT ALL PRIVILEGES ON DATABASE db_name TO db_user;
```

II. Restore DB from dump file:

`pg_restore -d db_name dump_file_name_path.sql`

#### GDAL instructions
- Install `libheif` (on OS)
- Setup Redis server https://redis.io/topics/quickstart
- Setup GDAL. Run `gdal-config --version` to get the correct version number.

```
pip3 download GDAL==version_number
tar -xpzf GDAL-version_number.tar.gz
cd GDAL-version_number/
python setup.py build_ext --include-dirs=/usr/include/gdal/
python setup.py build
python setup.py install
```

#### Celery instructions
- Create celery.log file in `/logs/`
- Create celery.pid and celerybeat.pid in `/src/`
- Add RAISIN_CELERY_BEAT_SCHEDULE variable in .env (see env.example for more details)
- `chmod a+rwx /home/ubuntu/raisin/repo/src/media/` (location of media folder)
- Add /etc/conf.d/celery
- Add /etc/systemd/system/celery.service
- Add /etc/systemd/system/celerybeat.service
- systemctl daemon-reload
- systemctl {start|stop|restart|status} celery.service
- systemctl {start|stop|restart|status} celerybeat.service

#### Caching issues
To invalidate cache on deploy, change the Version number in web.version.py.
Version name is not relevant for caching, it is a human descriptor in alphabetical order, representing a wine type (next version names: Beaujolais, Cabernet, Dolcetto, Eiswein etc.)

#### Possible issues:
When installing the dependencies on Mac, some issues with the `psycopg2` package may appear. Make sure openssl and gcc are both installed, and use export `LDFLAGS="-L/usr/local/opt/openssl/lib" export CPPFLAGS="-I/usr/local/opt/openssl/include"`. Run the pip install command again to make sure it runs without errors.

#### Style Guide
Please follow [Google's python style guide](https://google.github.io/styleguide/pyguide.html).
A few generic points:
* Four spaces as tabulation.
* Max line length = 120
* Excludes & ignore files/folders list located in the root directory in `.flake` configuration file 
* A contributor is advised to manually run the style guidelines tests before commits:
```
cd python-app
flake8
```


#### Enabling the flake8 pre-commit check
This lints all staged files and does not let you commit code that is not in the Python standards.

`flake8 --install-hook git`

## Useful commands

#### Creating a new user
Enter a shell `python manage.py shell`

```
from web.factories import UserProfileFactory
from django.contrib.auth.hashers import make_password
user = UserProfileFactory(username='example_name')
user.password = make_password('test')
user.save()
```

Optionally before saving you can also set `user.is_staff = True` for an admin account.

#### Creating a new user to use ChargeBee webhooks
For chargeBee webhooks to work, in principle, we need any user with a 
password through which the webhook can authenticate. This is set up at 
https://raisin-test.chargebee.com/apikeys_and_webhooks/webhooks

```
from web.factories import UserProfileFactory
from django.contrib.auth.hashers import make_password
user = UserProfileFactory(username='chargebee')
user.password = make_password('chargebee')
user.save()
```

Get chargebee user UUID:
```
from web.models.models import UserProfile
UserProfile.active.get(username="chargebee").id
```

...and save it in the .env (.env_dev) file 
into RAISIN_CHARGEBEE_CMS_USER_UUID variable:

```
RAISIN_CHARGEBEE_CMS_USER_UUID=7d993bd2-00ca-405e-8a53-3675676cd190
```

#### Creating a new erased_user to be able to delete (remove from DB) Users from mobile apps
When a user is deleted, part of the user's data is deleted completely, 
another part of the user's data is depersonalized and assigned to the 
erased_user account, such as comments.
```
from web.factories import UserProfileFactory
from django.contrib.auth.hashers import make_password
user = UserProfileFactory(username='erased_user')
user.password = make_password('any_password')
user.save()
```

Get erased_user UUID:
```
from web.models.models import UserProfile
UserProfile.active.get(username="erased_user").id
```

...and save it in the .env (.env_dev) file 
into RAISIN_ERASED_USER_UUID variable:

```
RAISIN_ERASED_USER_UUID=a6b7c228-0e35-415d-a887-5e7f70e42c1f
```

#### Logging in on the API
Using the get_token script in 'src': `python get_token.py username password` you will get a string like "Basic _provisionalTokenValue_".

Make an API request to `/api/users/login` with the header:
- Authorization: "Basic _provisionalTokenValue_"

The API will return a Token. Any further API request must be made with the header:
- Authorization: "Token _realTokenValue_"

#### If translations don't work

First thing to try is `python manage.py compilemessages`


### Run project using Docker ###

```sh
cp hose_crm/local_settings.base hose_crm/local_settings.py
```

Install docker, docker-compose
For ubuntu - https://docs.docker.com/install/linux/docker-ce/ubuntu/
Postinstall for ubuntu - https://docs.docker.com/install/linux/linux-postinstall/
Install docker-compose - https://docs.docker.com/compose/install/#install-compose

Build docker containers
```sh
docker-compose build
```

Run project (http://127.0.0.1:8000)
```sh
docker-compose up -d
```

Connect to Docker container
```sh
docker-compose exec web bash
```

Apply migrations using the commands 
```sh
docker-compose exec web bash

python3 manage.py migrate
```

Creating a new user in Docker container
```sh
docker-compose exec web bash

python3 manage.py shell

from web.factories import UserProfileFactory
from django.contrib.auth.hashers import make_password
user = UserProfileFactory(username='example_name')
user.password = make_password('test')
user.save()
```

Stop project
```sh
docker-compose down
```

Build docker containers without cache
```sh
docker-compose build --no-cache
```

####Cities
Before import data need to add in settings.py 
```python
CITIES_CITY_MODEL = 'custom_cities.CustomCity'
```
