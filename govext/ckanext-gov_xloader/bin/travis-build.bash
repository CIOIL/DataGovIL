#!/bin/bash
set -e

echo "This is travis-build.bash..."

echo "Installing the packages that CKAN requires..."
sudo apt-get update -qq
sudo apt-get install solr-jetty

echo "Installing CKAN and its Python dependencies..."
git clone https://github.com/ckan/ckan
cd ckan
if [ $CKANVERSION == 'master' ]
then
    echo "CKAN version: master"
else
    CKAN_TAG=$(git tag | grep ^ckan-$CKANVERSION | sort --version-sort | tail -n 1)
    git checkout $CKAN_TAG
    echo "CKAN version: ${CKAN_TAG#ckan-}"
fi

# install the recommended version of setuptools
if [ -f requirement-setuptools.txt ]
then
    echo "Updating setuptools..."
    pip install -r requirement-setuptools.txt
fi

if [ $CKANVERSION == '2.7' ]
then
    echo "Installing setuptools"
    pip install setuptools==39.0.1
fi

python setup.py develop
if [ -f requirements-py2.txt ]
then
    pip install -r requirements-py2.txt
else
    # To avoid error:
    # Error: could not determine PostgreSQL version from '10.1'
    # we need newer psycopg2 and corresponding exc name change
    sed -i -e 's/psycopg2==2.4.5/psycopg2==2.8.2/' requirements.txt
    sed -i -e 's/except sqlalchemy.exc.InternalError:/except (sqlalchemy.exc.InternalError, sqlalchemy.exc.DBAPIError):/' ckan/config/environment.py
    pip install -r requirements.txt
fi
pip install -r dev-requirements.txt
cd -

echo "Creating the PostgreSQL user and database..."
sudo -u postgres psql -c "CREATE USER user23 WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE user24 WITH OWNER user23;'
sudo -u postgres psql -c "CREATE USER datastore_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE datastore_test WITH OWNER datastore_default;'

echo "Setting up Solr..."
# Solr is multicore for tests on ckan master, but it's easier to run tests on
# Travis single-core. See https://github.com/ckan/ckan/issues/2972
sed -i -e 's/solr_url.*/solr_url = http:\/\/x.x.x.x:p8\/solr/' ckan/test-core.ini
printf "NO_START=0\nJETTY_HOST=x.x.x.x\nJETTY_PORT=p8\nJAVA_HOME=$JAVA_HOME" | sudo tee /etc/default/jetty
sudo cp ckan/ckan/config/solr/schema.xml /etc/solr/conf/schema.xml
sudo service jetty restart

echo "Create full text function..."
cp full_text_function.sql /tmp
cd /tmp
sudo -u postgres psql datastore_test -f full_text_function.sql
cd -

echo "Initialising the database..."
cd ckan
paster db init -c test-core.ini
paster datastore set-permissions -c test-core.ini | sudo -u postgres psql
cd -

echo "Installing ckanext-xloader and its requirements..."
python setup.py develop
pip install -r requirements.txt
pip install -r dev-requirements.txt

echo "Moving test.ini into a subdir..."
mkdir subdir
mv test.ini subdir

echo "travis-build.bash is done."
