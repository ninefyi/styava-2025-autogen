import streamlit as st
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
import asyncio

load_dotenv()

st.title("Travel Planning App")

destination = st.text_input("Destination", "Nepal")
days = st.number_input("Number of days", min_value=1, max_value=30, value=3)
user_request = st.text_area("Describe your travel preferences", "I want adventure and local experiences.")

plan_clicked = st.button("Plan Trip")

async def display_stream(stream):
    async for message in stream:
        # Handle message formatting as before
        if isinstance(message, str):
            st.write(message)
        elif isinstance(message, dict):
            sender = message.get("sender") or message.get("role")
            content = message.get("content") or message.get("text") or str(message)
            if sender:
                st.markdown(f"**{sender}:**")
            st.write(content)
        elif hasattr(message, "content"):
            sender = getattr(message, "sender", None) or getattr(message, "role", None)
            content = getattr(message, "content", str(message))
            if sender:
                st.markdown(f"**{sender}:**")
            st.write(content)
        else:
            st.write(str(message))

if plan_clicked:
    with st.spinner("Planning your trip..."):
        model_client = OpenAIChatCompletionClient(model="gpt-4o")
        planner_agent = AssistantAgent(
            "planner_agent",
            model_client=model_client,
            description="A helpful assistant that can plan trips.",
            system_message="You are a helpful assistant that can suggest a travel plan for a user based on their request.",
        )
        local_agent = AssistantAgent(
            "local_agent",
            model_client=model_client,
            description="A local assistant that can suggest local activities or places to visit.",
            system_message="You are a helpful assistant that can suggest authentic and interesting local activities or places to visit for a user and can utilize any context information provided.",
        )
        language_agent = AssistantAgent(
            "language_agent",
            model_client=model_client,
            description="A helpful assistant that can provide language tips for a given destination.",
            system_message="You are a helpful assistant that can review travel plans, providing feedback on important/critical tips about how best to address language or communication challenges for the given destination. If the plan already includes language tips, you can mention that the plan is satisfactory, with rationale.",
        )
        travel_summary_agent = AssistantAgent(
            "travel_summary_agent",
            model_client=model_client,
            description="A helpful assistant that can summarize the travel plan.",
            system_message="You are a helpful assistant that can take in all of the suggestions and advice from the other agents and provide a detailed final travel plan. You must ensure that the final plan is integrated and complete. YOUR FINAL RESPONSE MUST BE THE COMPLETE PLAN. When the plan is complete and all perspectives are integrated, you can respond with TERMINATE.",
        )
        termination = TextMentionTermination("TERMINATE")
        group_chat = RoundRobinGroupChat(
            [planner_agent, local_agent, language_agent, travel_summary_agent], termination_condition=termination
        )
        task = f"Plan a {days} day trip to {destination}. {user_request}"

        stream = group_chat.run_stream(task=task)
        asyncio.run(display_stream(stream))
        model_client.close()