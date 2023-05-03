## Note （2023/05/03）
 - There's no dockerfile in this exercice project, better to build one
 - Consider to replace sqlite with PostgresSQL and build a docker-compose file
 - No typing annotation or tests functions in app  (please add your own testcase and type annotation...)
 - One bug found: Failed to access userprofile page if the user doesn't have the portrait, it will work if you upload the portrait 
 

## Dependency issue fixed （2021/12/26）
 - fix dependencies issue
 - python version used in project: 3.10
 - if problem appears when trying to install requeirements.txt, try to manually install with command `pip install <package name>`

## Run project (2022/01/16)

```bash
$ # Download
$ git clone https://github.com/yaozeliang/Library.git
$ cd Library

$ # Install vierual environment
$ pip install virtualenv
$ virtualenv envname

$ # Activae virtual env
$ envname\scripts\activate

$cd ../..
$ pip3 install -r requirements.txt
$
$ # Create tables
$ python manage.py makemigrations
$ python manage.py migrate
$
$ # Start the application 
$ python manage.py runserver 

```
## Other issues
 - No type convention or comments
 - No unit/function test implemented
 - No performance improvements yet


## Another way to download project
https://katfile.com/users/alphaglobalus/114645/Django%E5%9B%BE%E4%B9%A6%E9%A6%86%E9%A1%B9%E7%9B%AE%E5%93%94%E5%93%A9%E5%93%94%E5%93%A9
