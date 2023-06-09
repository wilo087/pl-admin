# PL Admin
[Cambiar a Español](docs/README.md)

PL-Amin is a PL/SQL Manager that provides you with an easy way to clone a main schema, compile pl/sql code on realtime, check for database errors, check for differences between repos and databases, and so much more.

PL-Admin allows you to version your PL/SQL code from your Oracle database with Git without losing the advantages of programming within the same database.
It also works perfectly for automated deployments using GitHub, GitLab or the repository of your choice.

## Requirements
```sh
$ docker -v
  Docker version 19.03.5 # Or greater
```

## docker-compose
```yml
version: "3.7"
services:
  pladmin-omega:
    image: viva/pl-admin
    container_name: pladmin-omega
    build:
      context: '.'
    volumes:
      - <you_plsql_path>:/plsql # <-- DO NOT FORGET SETUP YOUR PL/SQL PATH
    tty: true
    networks:
      - backend
```

## Setup
+ Clone the repo
```sh
# Git
git clone <repo_url>
```

+ Creating images and container
```sh
# Build the docker image
docker build --no-cache -t viva/pl-admin .

# Create the container
# Do not forget replace <path_to_plsql_code> for your plsql path
docker run -ti --name=pladmin-omega -d -v <path/to/plsql_code>:/plsql viva/pl-admin

# In case that you have other schema just create another container with other name
docker run -ti --name=pladmin-reclamaciones -d -v <path/to/plsql_code>:/plsql viva/pl-admin
```

+ Copy `.env.sample` file to each pl/sql path and change the params
```sh
cp .env.sample you_plsql_path/.env
```

Create an alias the made the proccess more easier
```sh
# Open your profile config should be .bash_profile or .zshrc
vim ~/.bash_profile

# Enter this line:
alias pladmin="docker container exec -ti pladmin-omega pladmin"

# If you have multiple schemas, enter this line too:
alias pl-reclamaciones="docker container exec -ti pladmin-reclamaciones pladmin"

# Close the file and source you new alias
source ~/.bash_profile
```

### Topics
- [Usage](docs/usage.md)
- [Creating a New Shcema](docs/new-schema.md)
- [Export changes from your Database to Git (db2wc)](docs/db2wc.md)
- [Change SYS DBA Password](docs/change-sys-password.md)

> ### Important for your PL/SQL path
> - The file name has to be the same of the object name.
> - Do not duplicate files names.
> - The file extension indicates what kind of object it is.
> - Each object type has to be in it's corresponding directory.

| Object Type | File Extention | Directory |
| ------ | ------ | ------ |
| PACKAGE | .pks | ./packages |
| PACKAGE BODY | .pkb | ./packages |
| VIEW | .vw | ./views |
| FUNCTION | .fnc | ./functions |
| PROCEDURE | .prc | ./procedures |
