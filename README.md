# Vertex AI Multi-Agent Framework with RAG and SOP Agents (using ADK)

This repository contains a Google Agent Development Kit (ADK) implementation of a multi-agent framework featuring a manager agent that delegates tasks to specialized sub-agents: a Retrieval-Augmented Generation (RAG) agent and a Standard Operating Procedure (SOP) agent.

## Overview

This multi-agent system is orchestrated by a manager agent that routes tasks to the appropriate sub-agent based on the user's query.

### RAG Agent Capabilities

The Vertex AI RAG Agent allows you to:

- Query document corpora with natural language questions
- List available document corpora
- Create new document corpora
- Add new documents to existing corpora
- Get detailed information about specific corpora
- Delete corpora when they're no longer needed

### SOP Agent Capabilities

The SOP Agent allows you to:

- Search for Standard Operating Procedures (SOPs) within a Google Sheet based on keywords.
- Retrieve and understand the content of a specific SOP.
- Answer questions about procedures, ensuring it provides information from the latest revision if multiple are present.

## Prerequisites

- A Google Cloud account with billing enabled
- A Google Cloud project with the Vertex AI API enabled
- Appropriate access to create and manage Vertex AI resources
- Python 3.9+ environment
- A Google Sheet configured as an SOP repository for the SOP Agent.

## Setting Up Google Cloud Authentication

Before running the agent, you need to set up authentication with Google Cloud:

1. **Install Google Cloud CLI**:
   - Visit [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) for installation instructions for your OS

2. **Initialize the Google Cloud CLI**:
   ```bash
   gcloud init
   ```
   This will guide you through logging in and selecting your project.

3. **Set up Application Default Credentials**:
   ```bash
   gcloud auth application-default login
   ```
   This will open a browser window for authentication and store credentials in:
   `~/.config/gcloud/application_default_credentials.json`

4. **Verify Authentication**:
   ```bash
   gcloud auth list
   gcloud config list
   ```

5. **Enable Required APIs** (if not already enabled):
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

## Installation

1. **Set up a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Using the Agent

You interact with the system through the `manager` agent. The manager analyzes your request and delegates it to the correct sub-agent.

- **For RAG-related tasks**: Ask questions about creating, managing, or querying document corpora. For example: "Create a new corpus named 'my-docs'", "Add 'gs://my-bucket/doc.pdf' to 'my-docs'", or "What is the capital of France?" (assuming you have relevant documents).

- **For SOP-related tasks**: Ask questions about procedures at 'Those Who Care (TWC)'. For example: "How do I onboard a new employee?" or "What is the procedure for expense reports?". The agent will search the SOP master list and retrieve the relevant information.

## Troubleshooting

If you encounter issues:

- **Authentication Problems**:
  - Run `gcloud auth application-default login` again
  - Check if your service account has the necessary permissions

- **API Errors**:
  - Ensure the Vertex AI API is enabled: `gcloud services enable aiplatform.googleapis.com`
  - Verify your project has billing enabled

- **Quota Issues**:
  - Check your Google Cloud Console for any quota limitations
  - Request quota increases if needed

- **Missing Dependencies**:
  - Ensure all requirements are installed: `pip install -r requirements.txt`

## Additional Resources

- [Vertex AI RAG Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-overview)
- [Google Agent Development Kit (ADK) Documentation](https://github.com/google/agents-framework)
- [Google Cloud Authentication Guide](https://cloud.google.com/docs/authentication)