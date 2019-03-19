# Cauldron-development

Start Docker with `grimoirelab/secured` image
```bash
$ docker run -p 9200:9200 -p 5601:5601 -p 3306:3306 -e RUN_MORDRED=NO -t grimoirelab/secured
```

Create a new database for MariaDB (running in the container)
```bash
$ mysql -u grimoirelab -h 127.0.0.1
> create database test_db;
> exit
```

Install the packages in a new Python3 environment

```bash
$ python3 -m venv env-cauldron
$ source env-cauldron/bin/activate
(env-cauldron) $ pip install -r requirements

```

Start the mordred script in the environment. It waits for new tasks
```bash
(env-cauldron) $ python3 Cauldron2/MordredManager/manager.py

```

Run Django in the same environment
```bash
(env-cauldron) $ cd Cauldron2
(env-cauldron) $ python3 manage.py makemigrations
(env-cauldron) $ python3 manage.py migrate
(env-cauldron) $ python3 manage.py runserver
```
Go to [http://locahost:8000](http://locahost:8000), login with your GitHub account and analyze one repository

(It doesn't display anything at the moment, but you can go to [https://localhost:5601](https://localhost:5601) and filter your repository)