import json
import logging
import os
from dotenv import load_dotenv
from kafka.consumer import KafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)
load_dotenv(verbose=True)

def people_key_deserializer(key):
    return key.decode('utf-8')

def people_value_deserializer(value):
    return json.loads(value.decode('utf-8'))

def main():
    logger.info(f"""
        Started Python Consumer
        for topic {os.environ['TOPICS_PEOPLE_BASIC_NAME']}
    """)

    consumer = KafkaConsumer(bootstrap_servers=os.environ['BOOTSTRAP_SERVERS'],
                             group_id=os.environ['CONSUMER_GROUP'],
                             key_deserializer=people_key_deserializer,
                             value_deserializer=people_value_deserializer
                             )
    
    consumer.subscribe(os.environ['TOPICS_PEOPLE_BASIC_NAME'])

    for record in consumer:
        logger.info(
            f"""
            Consumed person {record.value}
            with key {record.key}
            from parition {record.partition}
            at offset {record.offset}
        """
        )



if __name__ == '__main__':
    main()
