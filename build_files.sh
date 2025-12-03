pip install -r requirements.txt
python3.12 manage.py collectstatic --noinput
python3.12 manage.py migrate