import logging
import os
import uuid
from typing import List

from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from faker import Faker
from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError
from kafka.producer import KafkaProducer

from commands import CreatePeopleCommand
from entities import Person

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
load_dotenv(verbose=True)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Creating Kafka Client
    client = KafkaAdminClient(
        bootstrap_servers=os.environ['BOOTSTRAP_SERVERS'])
    # Creating New Topics
    topic = NewTopic(name=os.environ['TOPICS_PEOPLE_ADV_NAME'],
                     num_partitions=int(
        os.environ['TOPICS_PEOPLE_BASIC_PARITION']),
        replication_factor=int(
        os.environ['TOPICS_PEOPLE_BASIC_REPLICAS'])
    )

    try:
        client.create_topics([topic])
    except TopicAlreadyExistsError as e:
        print(e)

    yield
    client.close()


app = FastAPI()


def make_producer():
    producer = KafkaProducer(bootstrap_servers=os.environ['BOOTSTRAP_SERVERS'],
                             linger_ms=int(os.environ['TOPICS_PEOPLE_ADV_LINGER_MS']),
                             retries=int(os.environ['TOPICS_PEOPLE_ADV_RETRIES']),
                             max_in_flight_requests_per_connection=int(os.environ['TOPICS_PEOPLE_ADV_INFLIGHT_REQS']),
                             acks=os.environ['TOPICS_PEOPLE_ADV_ACK'])
    return producer

class SuccessHandler:
    def __init__(self, person):
        self.person = person
    
    def __call__(self, rec_metadata):
        logger.info(f"""
            Successfully produced
            person {self.person}
            to topic {rec_metadata.topic}
            and partition {rec_metadata.partition}
            at offset {rec_metadata.offset}
                    """)
        
class ErrorHandler:
    def __init__(self, person):
        self.person = person
    
    def __call__(self, ex):
        logger.error(f"Failed producing person {self.person}", exc_info=ex)

@app.post('/api/people', status_code=201, response_model=List[Person])
async def create_people(cmd: CreatePeopleCommand):
    people: List[Person] = []
    faker = Faker()
    producer = make_producer()

    for _ in range(cmd.count):
        person = Person(id=str(uuid.uuid4()),
                        name=faker.name(), title=faker.job().title())

        people.append(person)
        producer.send(topic=os.environ['TOPICS_PEOPLE_ADV_NAME'],
                      key=person.title.lower().replace(r's+', '-').encode('utf-8'),
                      value=person.model_dump_json().encode('utf-8')
                      )
    producer.flush()

    return people
