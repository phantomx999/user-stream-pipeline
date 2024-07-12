from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner':  'airscholar',
    'start_date': datetime(2023, 9, 3, 10, 00)  # August 3rd, 2023, 10:00 AM,
}

def get_data():
    import json
    import requests

    res = requests.get("https://randomuser.me/api/")
    # print((res.json())['results'][0])
    result = (res.json())['results'][0]
    print(json.dumps(result, indent=3))

    return result

def format_data(res):
    data = {}
    location = res['location']
    data['first_name'] = res['name']['first']
    data['last_name'] = res['name']['last']
    data['gender'] = res['gender']
    data['address'] = f"{str(location['street']['number'])} {location['street']['name']}, " \
                      f"{location['city']}, {location['state']}, {location['country']}"
    data['post_code'] = location['postcode']
    data['email'] = res['email']
    data['username'] = res['login']['username']
    data['dob'] = res['dob']['date']
    data['registered_date'] = res['registered']['date']
    data['phone'] = res['phone']
    data['picture'] = res['picture']['medium']

    return data

def stream_data():
    import json
    from kafka import KafkaProducer
    import time

    # res = get_data()
    # res = format_data(res)
    # print(json.dumps(res, indent=3))

    producer = KafkaProducer(bootstrap_servers=['broker:29092'], max_block_ms=5000)

    curr_time = time.time()

    while True:
        if time.time() > curr_time + 60:
            break
        try:
            res = get_data()
            res = format_data(res)

            producer.send('users_created', json.dumps(res).encode('utf-8'))
        except Exception as e:
            logging.error(f'An error occurred: {e}')
            continue

with DAG('user_automtation',
    default_args= default_args,
    schedule_interval='@daily',  # Correct cron expression
    catchup=False) as dag:

    streaming_task = PythonOperator(
        task_id='stream_data_from_api',
        python_callable=stream_data
    )

#stream_data()