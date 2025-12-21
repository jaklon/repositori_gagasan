echo "Building the project..."
pip install -r requirements.txt

echo "Collecting static files..."
python3.12 manage.py collectstatic --noinput --clear

echo "Migrating database..."
python3.12 manage.py migrate --noinput

echo "Build Process Completed!"