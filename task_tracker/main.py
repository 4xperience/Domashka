from fastapi import FastAPI
from pydantic import BaseModel
import requests

class Task(BaseModel):
    task_id: int
    name: str
    task_status: str


class WorkerIO:
    def __init__(self, api_key: str, bin_id: str):
        self.api_key = api_key
        self.bin_id = bin_id
        self.jsonbin_url = f"https://api.jsonbin.io/v3/b/{bin_id}"

    def get_tasks(self):
        response = requests.get(self.jsonbin_url + "/latest?meta=false")
        return response.json()

    def create_tasks(self, task: Task):
        tasks = self.get_tasks()
        for t in tasks:
            if t['task_id'] == task.task_id:
                self.write_to_cloud(tasks)
                return {'error': f'Task-{task.task_id} already exists'}
        tasks.append(task.model_dump())
        self.write_to_cloud(tasks)
        return {f'Task-{task.task_id} has been created': task}

    def update_task(self, task_id: int, task: Task):
        tasks = self.get_tasks()
        for t in tasks:
            if task_id == task.task_id and t['task_id'] == task.task_id:
                t.update(task.model_dump())
                self.write_to_cloud(tasks)
                return {f'Task-{task_id} has been updated': task}
        return {'error': 'Update failed'}

    def delete_task(self, task_id: int):
        tasks = self.get_tasks()
        for t in tasks:
            if t and t['task_id'] == task_id:
                tasks.remove(t)
                self.write_to_cloud(tasks)
                return {f'Task-{task_id} has been deleted': t}

        return {'error': 'Task does not exist'}
    def write_to_cloud(self, tasks):
        requests.put(self.jsonbin_url, json=tasks)



app = FastAPI()

worker = WorkerIO(api_key='2a$10$6lE9rubkN9ABunw28JAYkOZQksN09U8m0/HE8VXNKInr1eIEq3UR',
                  bin_id='67bf68c8acd3cb34a8f175b6')

@app.get('/tasks', response_model=list)
def get_tasks():
    return worker.get_tasks()

@app.post('/tasks', response_model=dict)
def create_task(task:Task):
    return worker.create_tasks(task)

@app.put('/tasks/{task_id}', response_model=dict)
def update_task(task_id: int, task: Task):
    return worker.update_task(task_id, task)

@app.delete('/tasks/{task_id}', response_model=dict)
def delete_task(task_id: int):
    return worker.delete_task(task_id)