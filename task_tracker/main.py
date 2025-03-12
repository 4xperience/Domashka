from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests


load_dotenv()
class Task(BaseModel):
    task_id: int
    name: str
    task_status: str

class ResponseModel(BaseModel):
    message: str
    task: Task

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
        if len(tasks) == 1:
            tasks.append(task.model_dump())
            self.write_to_cloud(tasks)
            return {"message": f'Task-{task.task_id} has been created', "task": task}
        for t in tasks[1:]:
            if t['task_id'] == task.task_id:
                self.write_to_cloud(tasks)
                raise HTTPException(status_code=400, detail=f"Task with id {task.task_id} already exists")
        tasks.append(task.model_dump())
        self.write_to_cloud(tasks)
        return {"message": f'Task-{task.task_id} has been created', "task": task}

    def update_task(self, task: Task):
        tasks = self.get_tasks()
        for t in tasks[1:]:
            if t['task_id'] == task.task_id:
                t.update(task.model_dump())
                self.write_to_cloud(tasks)
                return {"message": f'Task-{task.task_id} has been updated', "task": task}
        raise HTTPException(status_code=404, detail=f"Task with id {task.task_id} not found")

    def delete_task(self, task_id: int):
        tasks = self.get_tasks()
        for t in tasks[1:]:
            if t and t['task_id'] == task_id:
                tasks.remove(t)
                self.write_to_cloud(tasks)
                return {"message": f'Task-{task_id} has been deleted', "task": t}

        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    def write_to_cloud(self, tasks):
        requests.put(self.jsonbin_url, json=tasks)



app = FastAPI()

worker = WorkerIO(api_key=os.getenv("API_KEY"),
                  bin_id='67d1d0c28561e97a50eab07e')

@app.get('/tasks', response_model=list)
def get_tasks():
    resp = worker.get_tasks()
    if len(resp) == 1:
        raise HTTPException(status_code=404, detail="No tasks found")
    return resp[1:]

@app.post('/tasks', response_model=ResponseModel)
def create_task(task: Task):
    return worker.create_tasks(task)

@app.put('/tasks/{task_id}', response_model=ResponseModel)
def update_task(task: Task):
    return worker.update_task(task)

@app.delete('/tasks/{task_id}', response_model=ResponseModel)
def delete_task(task_id: int):
    return worker.delete_task(task_id)