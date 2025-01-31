from openai import OpenAI
import time

from assistant_db import AssistantDatabase


class Assistant:
    def __init__(self, name, instructions, model="gpt-4o"):
        self.name = name
        self.instructions = instructions    # the instructions from the user for current persona
        self.model = model
        self.client = OpenAI()
        self.db = AssistantDatabase()
        self.assistant_id = None
        self.thread_id = None

        # Reuse or create assistant
        self.__reuse_or_create_assistant()

    def __reuse_or_create_assistant(self):
        assistant_data = self.db.get_assistant(self.name)
        if assistant_data:
            self.assistant_id, self.thread_id = assistant_data
            print(f"reusing existing assistant: {self.name}")
        else:
            assistant = self.client.beta.assistants.create(
                name=self.name,
                instructions=self.instructions,
                model=self.model,
                tools=[]        # disable code interpreter, reduce unnecessary cost
            )
            thread = self.client.beta.threads.create()

            self.assistant_id, self.thread_id = assistant.id, thread.id
            self.db.save_assistant(self.name, self.assistant_id, self.thread_id)
    
    def __create_message(self, user_message):
        return self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=user_message
        )

    def __create_run(self):
        # Polling to check run status
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id,
            instructions=self.instructions
        )

        while True:
            run_status = self.client.beta.threads.runs.retrieve(run_id=run.id, thread_id=self.thread_id)
            if run_status.status in ["completed", "failed", "cancelled"]:
                break
            time.sleep(1)  # Wait before checking again

        return run_status

    def reply(self, message):
        self.__create_message(message)
        run = self.__create_run()

        if run.status == "completed":   # if run completed, we extract the message
            messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)

            for msg in messages.data:     # list of messages, function call, assistant, etc
                if msg.role == "assistant":
                    return msg.content[0].text.value

            return "No response from assistant"
        else:
            return f"Run failed with status: {run.status}"

