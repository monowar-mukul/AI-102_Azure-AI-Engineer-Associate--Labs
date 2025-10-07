import os
from dotenv import load_dotenv
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    FilePurpose,
    CodeInterpreterTool,
    ListSortOrder,
    MessageRole
)


def main():
    # Clear the console
    os.system('cls' if os.name == 'nt' else 'clear')

    # Load environment variables
    load_dotenv()
    project_endpoint = os.getenv("PROJECT_ENDPOINT")
    model_deployment = os.getenv("MODEL_DEPLOYMENT_NAME")

    if not project_endpoint or not model_deployment:
        print("Missing environment variables. Check your .env file.")
        return

    # Read data file
    script_dir = Path(__file__).parent
    file_path = script_dir / 'data.txt'

    if not file_path.exists():
        print(f"Data file not found at {file_path}")
        return

    with file_path.open('r') as file:
        data = file.read()
        print("Data to be analyzed:\n")
        print(data)

    # Initialize AgentsClient
    agent_client = AgentsClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_managed_identity_credential=True
        )
    )

    with agent_client:
        # Upload file with correct purpose
        file = agent_client.files.upload_and_poll(
            file_path=file_path,
            purpose=FilePurpose.CODE_INTERPRETER_TOOL  # ✅ Correct enum value
        )
        print(f"Uploaded {file.filename}")

        # Create CodeInterpreterTool
        code_interpreter = CodeInterpreterTool(file_ids=[file.id])

        # Create agent
        agent = agent_client.create_agent(
            model=model_deployment,
            name="data-agent",
            instructions="You are an AI agent that analyzes the uploaded data file. Use Python to calculate statistical metrics as needed.",
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )
        print(f"Using agent: {agent.name}")

        # Create thread
        thread = agent_client.threads.create()

        # Interactive loop
        while True:
            user_prompt = input("Enter a prompt (or type 'quit' to exit): ").strip()
            if user_prompt.lower() == "quit":
                break
            if not user_prompt:
                print("Please enter a prompt.")
                continue

            # Send message
            agent_client.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=user_prompt
            )

            # Run agent
            run = agent_client.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )

            if run.status == "failed":
                print(f"Run failed: {run.last_error}")
                continue

            # Get last agent message
            last_msg = agent_client.messages.get_last_message_text_by_role(
                thread_id=thread.id,
                role=MessageRole.AGENT
            )
            if last_msg:
                print(f"Last Message: {last_msg.text.value}")

        # Show conversation history
        print("\nConversation Log:\n")
        messages = agent_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
        for message in messages:
            if message.text_messages:
                last_msg = message.text_messages[-1]
                print(f"{message.role}: {last_msg.text.value}\n")

        # Clean up
        agent_client.delete_agent(agent.id)


if __name__ == '__main__':
    main()
