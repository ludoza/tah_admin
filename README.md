# tah Admin

Python Package to add Cheetah functionality to flask-admin.

[Chee](https://github.com/ludoza/chee) is the native application you will use to connect to tah-admin.

# Setup

Clean Ubuntu install:

```sh
# install py3.6 and venv
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.6 python3.6-venv -y
# setup example prj directory
mkdir ~/prj
cd ~/prj
# create py3.6 venv for our project
python3.6 -m venv venv
# activate venv and instal flask-admin deps
source venv/bin/activate
pip install flask-admin flask_sqlalchemy paho-mqtt
# git clone our tah-admin project and install it editable using pip
git clone https://github.com/ludoza/tah_admin.git
cd tah-admin
pip install -e .
cd examples/sqla/
python app.py 
```

# `import tah_admin`

You will either need to mixin `TahAdminViewMixin` classes to your `ModelView` or
your model views should inhirit from `TahModelView` to use tah-admin.

# License

MIT/LGPL