import logging
import os
import time
import openai
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI()
model = "gpt-4o"

# Step 1. Upload a file to OpenAI embeddings
# Create a vector store caled "Financial Statements"
vector_store = client.beta.vector_stores.create(name="Financial Statements")

# Ready the files for upload to OpenAI
file_paths = ["./cryptocurrency.pdf"]
file_streams = [open(path, "rb") for path in file_paths]

# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id = vector_store.id,
    files = file_streams
)

# file_path = "./cryptocurrency.pdf"
# file_object = client.files.create(
#     file=open(file_path, "rb"),
#     purpose="assistants"
# )


# Step 2. Create an assistant 
assistant = client.beta.assistants.create(
    name="Studdy Buddy",
    instructions="""You are a helpful study assistant who knows a lot about understanding research papers.
    Your role is to summarize papers, clarify terminology within context, and extract key figures and data.
    Cross-reference information for additional insights and answer related questions comprehensively.
    Analyze the papers, noting strengths and limitations.
    Respond to queries effectively, incorporating feedback to enhance your accuracy.
    Handle data securely and update your knowledge base with the latest research.
    Adhere to ethical standards, respect intellectual property, and provide users with guidance on any limitations.
    Maintain a feedback loop for continuous improvement and user support.
    Your ultimate goal is to facilitate a deeper understanding of complex scientific material, making it more accessible and comprehensible.""",
    model = model,
    tools = [{"type" : "file_search"}],
    tool_resources = {"file_search":{"vector_store_ids":[vector_store.id]}}
)
assistant_id = assistant.id
print("ASSISTANT_ID:", assistant_id)


# Step 4. Create a thread 
thread = client.beta.threads.create()
thread_id = thread.id
print("THREAD_ID:", thread_id)


# Step 4. Run the assistant
run = client.beta.threads.runs.create(
    assistant_id=assistant_id,
    thread_id=thread_id,
    instructions="Please address the user as Bruce"
)


def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
    """
    Waits for a run to complete and prints the elapsed time.:param client: The OpenAI client object.
    :param thread_id: The ID of the thread.
    :param run_id: The ID of the run.
    :param sleep_interval: Time in seconds to wait between checks.
    """
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime(
                    "%H:%M:%S", time.gmtime(elapsed_time)
                )
                print(f"Run completed in {formatted_elapsed_time}")
                logging.info(f"Run completed in {formatted_elapsed_time}")
                # Get messages here once Run is completed!
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0]
                response = last_message.content[0].text.value
                print(f"Assistant Response: {response}")
                break
        except Exception as e:
            logging.error(f"An error occurred while retrieving the run: {e}")
            break
        logging.info("Waiting for run to complete...")
        time.sleep(sleep_interval)
        
        
# Run it
wait_for_run_completion(client=client,
                        thread_id=thread_id,
                        run_id=run.id)

run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run.id)
print(f"Run Steps --> {run_steps.data[0]}")